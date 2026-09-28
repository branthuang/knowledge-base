import logging
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.search_session import SearchSession
from app.schemas.search import SearchRequest
from app.schemas.ai_search import (
    SearchMode,
    AISearchRequest,
    AISearchResponse,
    CitationItem,
    LocalHitRef,
    SearchSessionListItem,
    SearchSessionDetailResponse,
)
from app.providers.base import BaseLLMProvider, BaseSearchProvider, LLMMessage
from app.providers.openai_provider import OpenAICompatibleProvider
from app.providers.search_provider import MockSearchProvider
from app.services.search_service import HybridSearchService, default_search_service

logger = logging.getLogger(__name__)


def get_default_llm_provider() -> BaseLLMProvider:
    return OpenAICompatibleProvider(
        api_base=settings.LLM_API_BASE,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL_NAME,
    )


def get_default_search_provider() -> BaseSearchProvider:
    return MockSearchProvider()


class AISearchService:
    """
    AI Search Domain Service:
    1. Dispatches across 4 search modes (knowledge_first, external_supplement, knowledge_only, direct_ai).
    2. Coordinates HybridSearchService for local recall and BaseSearchProvider for external citations.
    3. Builds structured LLM context prompts and invokes BaseLLMProvider for synthesis.
    4. Persists search snapshots in `search_sessions` for auditability and history isolation.
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        search_provider: Optional[BaseSearchProvider] = None,
        hybrid_search_svc: Optional[HybridSearchService] = None,
    ):
        self._llm = llm_provider
        self._search = search_provider
        self.search_service = hybrid_search_svc or default_search_service

    @property
    def llm(self) -> BaseLLMProvider:
        if self._llm is None:
            self._llm = get_default_llm_provider()
        return self._llm

    @property
    def search_provider(self) -> BaseSearchProvider:
        if self._search is None:
            self._search = get_default_search_provider()
        return self._search

    async def execute_ai_search(
        self,
        session: AsyncSession,
        request: AISearchRequest,
    ) -> AISearchResponse:
        mode = request.mode
        query = request.query.strip()
        local_hits_refs: List[LocalHitRef] = []
        citations: List[CitationItem] = []
        is_sufficient = False
        ai_answer = ""
        model_used = getattr(self.llm, "model", "default-llm")

        # 1. Mode Dispatching
        if mode == SearchMode.KNOWLEDGE_ONLY:
            # Strictly local knowledge only
            local_res = await self.search_service.search(
                session,
                SearchRequest(
                    query=query,
                    category_id=request.category_id,
                    tag_ids=request.tag_ids,
                    minimum_score=request.minimum_score,
                ),
            )
            is_sufficient = local_res.is_sufficient

            if local_res.items:
                for hit in local_res.items[:3]:
                    local_hits_refs.append(
                        LocalHitRef(
                            id=hit.id,
                            title=hit.title,
                            snippet=hit.best_snippet,
                            score=hit.score,
                            category_name=hit.category_name,
                        )
                    )

            if is_sufficient and local_hits_refs:
                prompt_context = "\n\n".join(
                    f"[本地知识 {i+1}] 标题: {h.title}\n内容: {h.snippet}"
                    for i, h in enumerate(local_hits_refs)
                )
                system_prompt = (
                    "你是一个严谨的个人知识库 AI 助手。用户当前开启了【仅知识库】模式。\n"
                    "你必须严格仅依据下方提供的本地知识库内容作答，不得引入任何未经证明的外部信息。\n"
                    "在回答中请清晰标明参考的本地知识标题。"
                )
                user_msg = f"本地知识库参考信息:\n{prompt_context}\n\n用户问题: {query}"
                resp = await self.llm.chat_complete(
                    [
                        LLMMessage(role="system", content=system_prompt),
                        LLMMessage(role="user", content=user_msg),
                    ]
                )
                ai_answer = resp.content
                model_used = resp.model
            else:
                ai_answer = (
                    "本地知识库中未检索到与该问题充分匹配的知识。\n"
                    "（当前为【仅知识库】模式，系统已严格禁用外部公网检索。如需获取更全面的解答，请切换至【知识优先】或【外部补充】模式。）"
                )

        elif mode == SearchMode.KNOWLEDGE_FIRST:
            # Default: try local first, fall back to external if insufficient
            local_res = await self.search_service.search(
                session,
                SearchRequest(
                    query=query,
                    category_id=request.category_id,
                    tag_ids=request.tag_ids,
                    minimum_score=request.minimum_score,
                ),
            )
            is_sufficient = local_res.is_sufficient

            for hit in local_res.items[:3]:
                local_hits_refs.append(
                    LocalHitRef(
                        id=hit.id,
                        title=hit.title,
                        snippet=hit.best_snippet,
                        score=hit.score,
                        category_name=hit.category_name,
                    )
                )

            if is_sufficient:
                # Local knowledge is sufficient -> synthesize using local knowledge only
                prompt_context = "\n\n".join(
                    f"[内部知识 {i+1}] 标题: {h.title}\n内容: {h.snippet}"
                    for i, h in enumerate(local_hits_refs)
                )
                system_prompt = (
                    "你是一个严谨的个人知识库 AI 助手。本地知识库中已检索到与用户问题高度吻合的内容。\n"
                    "请优先以提供的本地知识库内容为核心组织回答，结构清晰，并在回答中明确指出参考的知识标题。"
                )
                resp = await self.llm.chat_complete(
                    [
                        LLMMessage(role="system", content=system_prompt),
                        LLMMessage(
                            role="user",
                            content=f"本地知识库内容:\n{prompt_context}\n\n用户问题: {query}",
                        ),
                    ]
                )
                ai_answer = resp.content
                model_used = resp.model
            else:
                # Local is insufficient -> trigger external search supplement
                search_data = await self.search_provider.search(query, max_results=5)
                citations = [
                    CitationItem(
                        title=c.title,
                        url=c.url,
                        snippet=c.snippet,
                        source_name=c.source_name,
                        published_at=c.published_at,
                    )
                    for c in search_data.citations
                ]

                context_blocks = []
                if local_hits_refs:
                    context_blocks.append("【本地知识库关联参考】:")
                    for i, h in enumerate(local_hits_refs):
                        context_blocks.append(f"[内部知识 {i+1}] 《{h.title}》: {h.snippet}")

                if citations:
                    context_blocks.append("\n【外部公网检索参考】:")
                    for i, c in enumerate(citations):
                        context_blocks.append(f"[{i+1}] 《{c.title}》: {c.snippet} (来源: {c.url})")

                system_prompt = (
                    "你是一个专业的智能搜索助手。本地知识库未能完全覆盖用户问题，系统已补充公网检索结果。\n"
                    "请综合下方提供的参考材料进行回答。回答要求：\n"
                    "1. 结论明确，层次清晰；\n"
                    "2. 在论述中，引用公网来源请使用方括号角标 [1]、[2] 进行标注；若引用了本地知识，请明确指明《知识标题》；\n"
                    "3. 保持客观中立，不得虚构材料中不存在的事实。"
                )
                resp = await self.llm.chat_complete(
                    [
                        LLMMessage(role="system", content=system_prompt),
                        LLMMessage(
                            role="user",
                            content=f"参考材料:\n" + "\n".join(context_blocks) + f"\n\n用户问题: {query}",
                        ),
                    ]
                )
                ai_answer = resp.content
                model_used = resp.model

        elif mode == SearchMode.EXTERNAL_SUPPLEMENT:
            # Force dual combination
            local_res = await self.search_service.search(
                session,
                SearchRequest(
                    query=query,
                    category_id=request.category_id,
                    tag_ids=request.tag_ids,
                    minimum_score=request.minimum_score,
                ),
            )
            is_sufficient = local_res.is_sufficient

            for hit in local_res.items[:3]:
                local_hits_refs.append(
                    LocalHitRef(
                        id=hit.id,
                        title=hit.title,
                        snippet=hit.best_snippet,
                        score=hit.score,
                        category_name=hit.category_name,
                    )
                )

            search_data = await self.search_provider.search(query, max_results=5)
            citations = [
                CitationItem(
                    title=c.title,
                    url=c.url,
                    snippet=c.snippet,
                    source_name=c.source_name,
                    published_at=c.published_at,
                )
                for c in search_data.citations
            ]

            context_blocks = []
            if local_hits_refs:
                context_blocks.append("【本地知识库关联参考】:")
                for i, h in enumerate(local_hits_refs):
                    context_blocks.append(f"[内部知识 {i+1}] 《{h.title}》: {h.snippet}")

            if citations:
                context_blocks.append("\n【外部公网检索参考】:")
                for i, c in enumerate(citations):
                    context_blocks.append(f"[{i+1}] 《{c.title}》: {c.snippet} (来源: {c.url})")

            system_prompt = (
                "你是一个专业的智能搜索助手。用户指定进行【外部公网补充】综合问答。\n"
                "请将本地沉淀与公网最新资讯进行对比和综合，清晰输出解答并标注引用来源。"
            )
            resp = await self.llm.chat_complete(
                [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(
                        role="user",
                        content=f"参考材料:\n" + "\n".join(context_blocks) + f"\n\n用户问题: {query}",
                    ),
                ]
            )
            ai_answer = resp.content
            model_used = resp.model

        elif mode == SearchMode.DIRECT_AI:
            # Direct external AI search
            search_data = await self.search_provider.search(query, max_results=5)
            citations = [
                CitationItem(
                    title=c.title,
                    url=c.url,
                    snippet=c.snippet,
                    source_name=c.source_name,
                    published_at=c.published_at,
                )
                for c in search_data.citations
            ]
            context_blocks = [
                f"[{i+1}] 《{c.title}》: {c.snippet} (来源: {c.url})"
                for i, c in enumerate(citations)
            ]
            system_prompt = (
                "你是一个 AI 搜索引擎。请根据提供的公网检索结果，对用户的问题进行准确客观的解答，并在相关陈述处引用 [1]、[2] 对应来源。"
            )
            resp = await self.llm.chat_complete(
                [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(
                        role="user",
                        content=f"公网检索结果:\n" + "\n".join(context_blocks) + f"\n\n用户问题: {query}",
                    ),
                ]
            )
            ai_answer = resp.content
            model_used = resp.model

        # 2. Persist SearchSession
        session_id = request.session_id or str(uuid.uuid4())
        existing_sess = await session.get(SearchSession, session_id)
        local_snapshot = [h.model_dump() for h in local_hits_refs]
        citations_snapshot = [c.model_dump() for c in citations]

        if existing_sess:
            existing_sess.query = query
            existing_sess.mode = mode.value
            existing_sess.local_hits_json = local_snapshot
            existing_sess.citations_json = citations_snapshot
            existing_sess.ai_answer = ai_answer
            existing_sess.model = model_used
            search_sess = existing_sess
        else:
            search_sess = SearchSession(
                id=session_id,
                query=query,
                mode=mode.value,
                local_hits_json=local_snapshot,
                citations_json=citations_snapshot,
                ai_answer=ai_answer,
                provider="openai",
                model=model_used,
            )
            session.add(search_sess)

        await session.commit()
        await session.refresh(search_sess)

        return AISearchResponse(
            session_id=search_sess.id,
            query=query,
            mode=mode,
            ai_answer=ai_answer,
            is_sufficient=is_sufficient,
            local_hits=local_hits_refs,
            citations=citations,
            model_used=model_used,
            created_at=search_sess.created_at,
        )

    async def list_sessions(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SearchSessionListItem]:
        stmt = (
            select(SearchSession)
            .order_by(desc(SearchSession.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await session.execute(stmt)
        sessions = res.scalars().all()

        items = []
        for s in sessions:
            preview = s.ai_answer[:100] + "..." if s.ai_answer and len(s.ai_answer) > 100 else s.ai_answer
            items.append(
                SearchSessionListItem(
                    id=s.id,
                    query=s.query,
                    mode=s.mode,
                    ai_answer_preview=preview,
                    model=s.model,
                    saved_knowledge_id=s.saved_knowledge_id,
                    created_at=s.created_at,
                )
            )
        return items

    async def get_session(
        self,
        session: AsyncSession,
        session_id: str,
    ) -> Optional[SearchSessionDetailResponse]:
        sess = await session.get(SearchSession, session_id)
        if not sess:
            return None
        return SearchSessionDetailResponse(
            id=sess.id,
            query=sess.query,
            mode=sess.mode,
            local_hits_json=sess.local_hits_json or [],
            citations_json=sess.citations_json or [],
            ai_answer=sess.ai_answer,
            provider=sess.provider,
            model=sess.model,
            saved_knowledge_id=sess.saved_knowledge_id,
            created_at=sess.created_at,
        )


# Global default AI search service instance
default_ai_search_service = AISearchService()
