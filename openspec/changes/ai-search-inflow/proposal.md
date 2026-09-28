# Change: AI 增强搜索与知识沉淀入库闭环 (ai-search-inflow)

## Why

目前系统已具备完整的本地知识点生命周期管理（M2）与双路混合检索及本地充分性评估能力（M3）。
然而，知识库的核心产品闭环是：“先查自己的知识，再向 AI / 公网提问；有价值的搜索结果由用户确认后沉淀为可持续维护、可检索、可追溯的知识”。
当前缺失的关键环节为：
1. 本地知识不足时，如何通过大模型与公网搜索 Provider 获取结构化回答与外部引用；
2. 搜索过程历史如何独立记录在 `search_sessions` 中，与正式知识物理隔离；
3. 用户如何将满意的搜索结果“一键收藏到知识库”，完成入库预览、相似防重检测、人工编辑调整并最终沉淀落库，触发派生向量索引。

## What Changes

1. **AI 搜索与会话服务（AI Search Engine & Sessions）**：
   - 实现搜索模式支持：
     - `knowledge_first`（默认：本地优先，本地充分时仅用本地知识；不足时结合外部搜索）；
     - `external_supplement`（强制本地 + 外部公网综合回答）；
     - `knowledge_only`（仅本地知识，绝不发起外部请求）；
     - `direct_ai`（跳过本地评估直接调用 AI 问答）。
   - 实现 LLM 提示词组装与结构化引用提炼（内部知识点引用与公网链接引用）。
   - 实现 `search_sessions` 会话快照存储与历史查询接口。

2. **知识回流与入库预览流水线（Knowledge Inflow Pipeline）**：
   - 实现从搜索会话或富文本内容自动转换为 Block 结构草稿。
   - 实现自动提取推荐标题、摘要、分类及标签。
   - 实现相似知识检测与防重比对（基于向量或关键词计算与库中既有知识的最高相似度，给出高相似提醒）。
   - 实现确认入库持久化（创建 `KnowledgeItem`，`source_type='ai_search'`，创建 `KnowledgeSource`，回填 `search_sessions.saved_knowledge_id`，并触发向量索引生成）。

3. **统一 API 接口与回归测试套件**：
   - `POST /api/ai-search`: 发起 AI 增强搜索与生成结构化回答。
   - `GET /api/ai-search/sessions`: 查询搜索会话历史列表与详情。
   - `POST /api/inflow/preview`: 生成入库预览（草稿块、智能推荐元数据、相似知识检测结果）。
   - `POST /api/inflow/confirm`: 用户确认入库落盘。
   - 编写完整的场景单元与集成测试套件。

## Capabilities

### New Capabilities
- `ai-search`: AI 问答、多源引用追溯、搜索模式切换与会话记录。
- `knowledge-inflow`: 搜索结果结构化组装、入库预览、相似检测与确认入库。

### Modified Capabilities
- `hybrid-search`: 与 AI 搜索进行无缝协同。
- `knowledge-management`: 接收 AI 来源知识入库并建立完整追溯关系。

## Impact

- 后端新增：
  - `backend/app/schemas/ai_search.py`
  - `backend/app/schemas/inflow.py`
  - `backend/app/services/ai_search_service.py`
  - `backend/app/services/inflow_service.py`
  - `backend/app/api/ai_search.py`
  - `backend/app/api/inflow.py`
- 后端测试：
  - `backend/tests/test_ai_search.py`
  - `backend/tests/test_inflow.py`
