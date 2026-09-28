## Context

前三阶段已完成数据底座、知识核心管理和本地双路混合检索。
本阶段（M4）实现整个系统的闭环命脉：当本地知识不足时，驱动 AI 搜索问答与外部检索，并将高价值信息通过用户确认转化为结构化知识资产。

## Goals / Non-Goals

**Goals:**
- 实现 4 种搜索模式调度：`knowledge_first`（默认）、`external_supplement`、`knowledge_only`、`direct_ai`。
- 实现大模型 Prompt 模板与回答生成，明确划分本地知识与外部公网引用（Citations）。
- 实现搜索过程数据物理隔离，在 `search_sessions` 中持久化快照与执行元数据。
- 实现入库预览生成（`InflowService.generate_preview`）：
  - Markdown 转结构化内容块（Blocks）；
  - 自动提取标题、摘要草稿；
  - 自动匹配已有分类与标签；
  - 库内相似知识防重检测（相似度高时提示覆盖或新建）。
- 实现用户人工确认落盘（`InflowService.confirm_inflow`）：
  - 持久化为 `source_type='ai_search'` 的正式知识点；
  - 生成 `KnowledgeSource` 溯源记录；
  - 回填 `search_sessions.saved_knowledge_id`；
  - 同步/异步建立文本分块与向量索引。

**Non-Goals:**
- 本阶段不实现重排模型（Reranker）二次精排。
- 本阶段不实现知识冲突消解深度 Agent 对话（归属于 M5 AI 优化阶段）。

## Decisions

1. **AI 搜索与过程数据隔离设计**：
   - 搜索会话全生命周期存储于 `search_sessions` 表，与 `knowledge_items` 表保持松耦合外键或独立 ID。
   - 会话记录 `query`, `search_mode`, `local_results_snapshot`, `citations_json`, `ai_answer`, `model_name`, `saved_knowledge_id`。
2. **入库内容结构化组装（Block Transformation）**：
   - 复用 `block_parser.markdown_to_blocks` 将 AI 回答自动转化为段落、标题、列表、代码块。
   - 外部引用链接统一格式化为文末的参考资料块（引用块或列表块）。
3. **相似检测与防重机制（Duplicate Detection）**：
   - 预览生成时，以草稿标题和内容为 Query 触发本地混合检索。
   - 当 Top-1 分数超过防重告警阈值 `0.75` 时，标定 `has_similar_knowledge = True`，并在预览中返回相似知识卡片。
   - 用户在确认时可选择：
     - `create_new`: 坚持作为全新知识入库；
     - `update_existing`: 将新内容追加或合并至已有知识点。
4. **Provider 依赖注入与测试兼容性**：
   - `AISearchService` 注入 `BaseLLMProvider` 和 `BaseSearchProvider`，在单元测试中注入 Mock Provider，杜绝测试过程中的真实公网网络依赖。

## Risks / Trade-offs

- **风险 1：外部搜索或 LLM 响应超时导致用户感知卡顿**
  - *缓解措施*：设置合理超时时间（默认 15~30s），对于失败的外部搜索优雅降级为纯本地或纯模型思考。
- **风险 2：AI 回答生成虚假引用**
  - *缓解措施*：系统 Prompt 严格限定仅能从提供的本地命中片段与公网搜索结果中提炼标注引用，不得臆造 URL。
