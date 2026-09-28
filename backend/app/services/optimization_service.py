import logging
import re
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.providers.base import BaseLLMProvider, LLMMessage
from app.providers.openai_provider import OpenAICompatibleProvider
from app.schemas.block import BlockItem
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationMode,
)
from app.services.block_parser import blocks_to_markdown, markdown_to_blocks
from app.services.category_service import list_categories
from app.services.tag_service import list_tags

logger = logging.getLogger(__name__)


def get_default_llm_provider() -> BaseLLMProvider:
    return OpenAICompatibleProvider(
        api_base=settings.LLM_API_BASE,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL_NAME,
    )


class OptimizationService:
    """
    AI Content Optimization Domain Service:
    Provides text polishing, typo fixing, structural formatting, code-preservation guarantees,
    and category/tag recommendation.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self._llm = llm_provider

    @property
    def llm(self) -> BaseLLMProvider:
        if self._llm is None:
            self._llm = get_default_llm_provider()
        return self._llm

    async def optimize_content(
        self,
        session: AsyncSession,
        request: OptimizationRequest,
    ) -> OptimizationResponse:
        # 1. Normalize original text
        if request.blocks:
            blocks_dict = [b.model_dump() for b in request.blocks]
            original_text = blocks_to_markdown(blocks_dict)
        elif request.content_markdown:
            original_text = request.content_markdown.strip()
        else:
            original_text = ""

        if not original_text:
            return OptimizationResponse(
                original_text="",
                polished_text="",
                blocks=[],
                changes_summary="原始内容为空，未做修改。",
            )

        mode = request.mode
        mode_instruction = ""
        if mode == OptimizationMode.CONCISE:
            mode_instruction = "【简洁易懂模式】：修正错别字与标点语病，剔除重复冗余口语，理顺逻辑结构与段落分层，使文字通俗干练、条理分明。"
        elif mode == OptimizationMode.STRUCTURED:
            mode_instruction = "【结构化整理模式】：重构大纲与层级，合理运用小标题、有序/无序列表与引用块，使逻辑递进严密。"
        elif mode == OptimizationMode.FORMAL:
            mode_instruction = "【专业规范模式】：提升行文规范度，使用准确的专业术语与书面语态表达。"
        elif mode == OptimizationMode.CORRECT_ONLY:
            mode_instruction = "【仅纠错模式】：仅修正拼写错别字与标点符号，严禁改动任何句子原意和段落排版。"

        system_prompt = (
            "你是一个严谨的个人知识库文本优化助理。\n"
            f"当前优化目标: {mode_instruction}\n\n"
            "【严格安全准则】:\n"
            "1. 代码块安全: 代码片段（```code ... ```）必须逐字逐行原样保留，严禁修改任何变量、语法或逻辑；\n"
            "2. 数据真实性: 原文中的具体数值、百分比、日期、专业术语和 URL 链接必须原样保留；\n"
            "3. 严禁捏造: 严禁引入或补充原文不存在的事实结论；\n"
            "4. 输出格式规范: 必须按照如下格式输出两部分：\n"
            "<<<POLISHED>>>\n"
            "[这里是优化后的完整 Markdown 格式正文]\n"
            "<<<CHANGES>>>\n"
            "[这里用 1~2 句话简要说明主要优化点]"
        )

        resp = await self.llm.chat_complete(
            [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=f"待优化文本:\n{original_text}"),
            ]
        )

        content = resp.content or ""
        polished_text = content
        changes_summary = "已对内容完成语言润色与排版梳理。"

        # Extract structured delimiters if present
        if "<<<POLISHED>>>" in content:
            parts = content.split("<<<CHANGES>>>")
            polished_part = parts[0].replace("<<<POLISHED>>>", "").strip()
            polished_text = polished_part
            if len(parts) > 1 and parts[1].strip():
                changes_summary = parts[1].strip()

        # Parse into BlockItem tree
        blocks = markdown_to_blocks(polished_text)

        # Recommend Category and Tags
        categories = await list_categories(session)
        tags = await list_tags(session)

        full_lower = polished_text.lower()
        rec_cat_id = None
        rec_cat_name = None
        for cat in categories:
            if cat.name.lower() in full_lower:
                rec_cat_id = cat.id
                rec_cat_name = cat.name
                break

        rec_tag_ids = []
        rec_tag_names = []
        for tag in tags:
            if tag.name.lower() in full_lower:
                rec_tag_ids.append(tag.id)
                rec_tag_names.append(tag.name)

        return OptimizationResponse(
            original_text=original_text,
            polished_text=polished_text,
            blocks=blocks,
            changes_summary=changes_summary,
            suggested_category_id=rec_cat_id,
            suggested_category_name=rec_cat_name,
            suggested_tag_ids=rec_tag_ids,
            suggested_tag_names=rec_tag_names,
        )


default_optimization_service = OptimizationService()
