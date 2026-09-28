import logging
from typing import Optional
from app.providers.base import BaseSearchProvider, SearchResult, SearchCitation
from app.core.config import settings

logger = logging.getLogger(__name__)


class MockSearchProvider(BaseSearchProvider):
    """Mock search provider for local testing and offline execution."""

    async def search(self, query: str, max_results: int = 5) -> SearchResult:
        citations = [
            SearchCitation(
                title=f"参考资料 1: 关于 '{query}' 的官方文档",
                url=f"https://docs.example.com/search?q={query}",
                snippet=f"这是针对问题 '{query}' 的概要说明与核心参数配置方法...",
                source_name="ExampleDocs",
                published_at="2026-09-01",
            ),
            SearchCitation(
                title=f"参考资料 2: '{query}' 最佳工程实践与常见问题",
                url=f"https://blog.example.com/posts/{query}",
                snippet=f"深入探讨 '{query}' 在生产环境部署中的注意事项与性能调优建议...",
                source_name="TechBlog",
                published_at="2026-09-15",
            ),
        ]
        return SearchResult(
            query=query,
            citations=citations[:max_results],
            raw_answer=f"针对 '{query}' 的检索总结：已聚合来自外部站点的权威建议。",
        )

    async def check_connectivity(self) -> bool:
        return True


def get_search_provider() -> BaseSearchProvider:
    """Factory to retrieve configured web search provider."""
    provider_type = settings.SEARCH_PROVIDER.lower()
    if provider_type == "mock":
        return MockSearchProvider()
    # Placeholder for tavily, serper, bing providers in later milestones
    return MockSearchProvider()
