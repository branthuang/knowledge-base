## 1. 块数据模型验证与纯文本提取器

- [x] 1.1 实现块数据 Pydantic Schemas `backend/app/schemas/block.py`，支持段落、标题、列表、代码、表格、图片、附件、提示块、分割线
- [x] 1.2 实现块纯文本派生提取器与基础 Markdown 转换器 `backend/app/services/block_parser.py`
- [x] 1.3 编写块模型及文本提取自动化测试 `backend/tests/test_block_parser.py`

## 2. 分类管理服务与 API（含删除保护与级联筛选）

- [x] 2.1 实现分类 DTO 数据契约 `backend/app/schemas/category.py`，支持创建、更新、树形响应
- [x] 2.2 实现分类领域服务 `backend/app/services/category_service.py`，包含树形构建、级联子分类展开以及删除知识保护约束
- [x] 2.3 实现分类 API 路由 `backend/app/api/categories.py` 并编写自动化集成测试 `backend/tests/test_category_api.py`

## 3. 标签系统服务与 API（含标签合并与统计）

- [x] 3.1 实现标签 DTO 数据契约 `backend/app/schemas/tag.py`，包含 CRUD 与合并入参
- [x] 3.2 实现标签领域服务 `backend/app/services/tag_service.py`，包含使用统计与标签合并（关联关系安全迁移）事务
- [x] 3.3 实现标签 API 路由 `backend/app/api/tags.py` 并编写自动化集成测试 `backend/tests/test_tag_api.py`

## 4. 知识点核心管理与回收站生命周期

- [ ] 4.1 实现知识点 DTO 数据契约 `backend/app/schemas/knowledge.py`，覆盖创建、更新、详情、列表过滤与来源追溯
- [ ] 4.2 实现知识点领域服务 `backend/app/services/knowledge_service.py`，支持自动纯文本派生、多标签关联、状态流转（草稿/发布/归档/移入回收站/还原/彻底删除）
- [ ] 4.3 实现知识点及回收站 API 路由 `backend/app/api/knowledge.py`
- [ ] 4.4 编写知识点 CRUD、生命周期流转与回收站机制集成测试 `backend/tests/test_knowledge_api.py`

## 5. 路由挂载与全量测试回归验收

- [ ] 5.1 在 `backend/app/main.py` 中挂载分类、标签、知识点 API 路由，验证 OpenAPI 文档
- [ ] 5.2 运行全量测试套件（新旧全部测试用例），执行静态类型检查，确保 100% 验收通过
