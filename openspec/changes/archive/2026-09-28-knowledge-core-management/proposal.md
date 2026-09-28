## Why

在第一阶段（基础设施与数据底座）完成后，系统需要实现业务层核心资产的读写、组织与生命周期管理能力。
分类与标签是知识的横向与纵向索引支柱，块数据是知识表达的基石。本变更旨在实现分类、标签及知识点的完整业务逻辑、API 端点、安全约束及自动化测试，为后续混合检索与 AI 搜索回流提供可操作的业务核心。

## What Changes

1. **分类管理业务与 API（Category Management）**：
   - 树形层级分类（1~3级）CRUD、图标/颜色维护、排序与停用机制。
   - 删除保护约束：禁止直接删除包含知识的分类，提供“迁移到其他分类”或“设为未分类”的处置选项。
   - 分类级联查询引擎：支持传入父分类 ID，自动级联展开其所有子分类 ID 列表。
2. **标签系统业务与 API（Tag System）**：
   - 标签 CRUD、多标签绑定与使用统计。
   - 标签合并操作（Tag Merge）：自动将源标签关联的所有知识点重新关联至目标标签，去重后安全删除源标签。
3. **知识点核心管理业务与 API（Knowledge Management）**：
   - 知识点完整 CRUD、草稿保存、发布、归档全生命周期。
   - 软删除进入回收站、回收站恢复、彻底删除。
   - 来源追溯关联（URL、Query、Provider、Metadata）。
4. **块数据结构与纯文本派生转换（Block Editor Models & Text Extractor）**：
   - 严格的 Pydantic 块数据校验模型（支持段落、各级标题、列表、代码高亮、表格、图片、附件、提示块、分割线）。
   - 结构化块派生纯文本提取器（Plain Text Extractor），从任意复杂块内容自动提取权威纯文本供检索使用。
   - 基础 Markdown 到块结构解析转换器（Markdown to Blocks Parser）。

## Capabilities

### Modified Capabilities
- `category-management`: 落实分类层级树、排序、停用、删除安全保护与级联筛选服务。
- `tag-system`: 落实多标签绑定、使用统计、标签合并关系迁移服务。
- `knowledge-management`: 落实知识点 CRUD、状态流转（draft/published/archived/trashed）、阅读/编辑数据契约与回收站机制。
- `block-editor`: 落实块结构 Pydantic DTO 校验、纯文本派生提取器及 Markdown 块转换器。

## Impact

- 新增后端 DTO schemas 目录：`backend/app/schemas/`（`category.py`, `tag.py`, `knowledge.py`, `block.py`）。
- 新增业务服务层目录：`backend/app/services/`（`category_service.py`, `tag_service.py`, `knowledge_service.py`, `block_parser.py`）。
- 新增 RESTful API 路由：`backend/app/api/`（`/categories`, `/tags`, `/knowledge`）。
- 挂载路由至 `backend/app/main.py` 并提供交互式 OpenAPI / Swagger 文档。
