## 1. 工作台看板与资产统计服务

- [x] 1.1 实现工作台 DTO `backend/app/schemas/workbench.py`
- [x] 1.2 实现工作台领域服务 `backend/app/services/workbench_service.py`，聚合 5 项核心指标、待整理草稿、近期编辑与搜索动态
- [x] 1.3 实现工作台 API 路由 `backend/app/api/workbench.py` 并在 `backend/app/main.py` 挂载

## 2. 编辑器 AI 优化与差异对比服务

- [x] 2.1 实现 AI 优化 DTO `backend/app/schemas/optimization.py`
- [x] 2.2 实现 AI 优化领域服务 `backend/app/services/optimization_service.py`，实现“简洁易懂”润色、代码防篡改与分类标签智能推荐
- [x] 2.3 实现 AI 优化 API 路由 `backend/app/api/optimization.py` 并在 `backend/app/main.py` 挂载

## 3. 数据备份导出、恢复与单篇 Markdown 导出

- [x] 3.1 实现备份恢复领域服务 `backend/app/services/backup_service.py`，支持 ZIP 打包导出、SHA-256 校验和恢复与单篇 Markdown 导出
- [x] 3.2 实现备份恢复 API 路由 `backend/app/api/backup.py` 与单篇导出路由并在 `backend/app/main.py` 挂载

## 4. 全量端到端测试与回归验收

- [x] 4.1 编写工作台、AI 优化与备份恢复集成测试 `backend/tests/test_workbench_backup_optimization.py`
- [x] 4.2 运行全量自动化测试套件（新旧全部用例），执行静态类型与编译检查，确保 100% 验收通过
