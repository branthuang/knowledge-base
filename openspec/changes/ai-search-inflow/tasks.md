## 1. AI 搜索领域服务与会话管理

- [x] 1.1 实现 AI 搜索入参及出参 DTO `backend/app/schemas/ai_search.py`
- [x] 1.2 实现 AI 搜索领域服务 `backend/app/services/ai_search_service.py`，覆盖 4 种搜索模式调度、本地与外部上下文组装、大模型问答生成及 `search_sessions` 持久化
- [x] 1.3 编写 AI 搜索与会话服务单元测试 `backend/tests/test_ai_search.py`

## 2. 知识沉淀回流流水线

- [ ] 2.1 实现知识回流入库契约 `backend/app/schemas/inflow.py`，定义预览与确认请求响应模型
- [ ] 2.2 实现知识沉淀回流服务 `backend/app/services/inflow_service.py`，实现结构化块转换、智能标签分类推荐、相似防重检测与确认入库落盘
- [ ] 2.3 编写知识回流流水线单元测试 `backend/tests/test_inflow.py`

## 3. 路由注册与全量端到端验收

- [ ] 3.1 实现 AI 搜索与会话 API 路由 `backend/app/api/ai_search.py` 并在 `backend/app/main.py` 挂载
- [ ] 3.2 实现知识回流 API 路由 `backend/app/api/inflow.py` 并在 `backend/app/main.py` 挂载
- [ ] 3.3 执行全量自动化测试套件与代码静态校验，确保 100% 验收通过
