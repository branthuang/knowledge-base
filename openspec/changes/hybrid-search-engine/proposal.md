## Why

系统核心原则是“先查自己的知识，再向 AI / 公网提问”。为了支撑该原则，需要构建统一、精准且具备自我充分性评估的检索引擎。
单纯的关键词搜索无法理解语义，单纯的向量搜索缺乏对精确专有名词和代码符号的精确召回。本变更旨在实现“全文关键词检索 + 向量语义检索”双路并发召回，结合结构化条件过滤、分数归一化融合与聚合去重，并严格实现“本地知识充分性判定”，在本地知识不足时智能引导用户衔接 AI 搜索。

## What Changes

1. **正文分块与向量索引生成管线（Chunking & Index Pipeline）**：
   - 实现结构化文本分块器（Text Chunker），支持基于段落边界与语义窗口（带重叠滑动）的分块。
   - 实现知识点向量化索引服务：调用 Embedding Provider 计算分块向量并写入 `embedding_chunks` 表，同步更新 `index_status = 'indexed'`。
2. **多路并发召回引擎（Multi-way Recall Engine）**：
   - 全文检索通道（FTS）：基于标题、标签、摘要及派生正文计算加权匹配分。
   - 语义检索通道（Vector Search）：调用 Embedding Provider 计算查询向量，通过 pgvector 计算余弦相似度召回最相关的分块。
3. **混合分数归一化加权融合与分块聚合（Score Fusion & Aggregation）**：
   - 采用归一化加权融合算法（融合关键词得分、语义相似度、标题加权与时间新鲜度加权）。
   - 按知识点（`knowledge_id`）聚合去重，选取最相关的匹配分块作为最佳摘要片段（Best Snippet）并高亮命中词。
4. **本地知识充分性判定机制（Sufficiency Evaluator）**：
   - 基于设定的 `minimum_score`（默认 0.65）与有效结果数阈值，评估本地检索结果是否充分覆盖用户查询。
   - 判定为不足时，返回清晰的状态标识并输出“建议继续使用 AI 搜索”行动建议。
5. **统一搜索 RESTful API**：
   - 提供 `GET /api/search` 端点，支持查询词、分类过滤（含级联）、标签过滤、模式切换与分页。

## Capabilities

### Modified Capabilities
- `hybrid-search`: 落地统一搜索入口、全文检索、向量语义检索、分数融合、分块聚合与知识充分性评估。

## Impact

- 新增分块服务：`backend/app/services/chunker.py`。
- 新增索引服务：`backend/app/services/index_service.py`。
- 新增混合检索服务：`backend/app/services/search_service.py`。
- 新增搜索数据契约：`backend/app/schemas/search.py`。
- 新增 API 路由：`backend/app/api/search.py`。
- 在 `backend/app/main.py` 中挂载 `/api/search`。
