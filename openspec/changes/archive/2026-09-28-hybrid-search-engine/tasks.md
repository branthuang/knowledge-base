## 1. 文本分块与向量索引生成服务

- [x] 1.1 实现结构化文本分块器 `backend/app/services/chunker.py`，支持块语义边界、长度窗口及重叠滑动
- [x] 1.2 实现知识点向量索引服务 `backend/app/services/index_service.py`，负责分块切割、调用 EmbeddingProvider 批量向量化持久化及状态更新
- [x] 1.3 编写文本分块与索引服务单元测试 `backend/tests/test_chunker_index.py`

## 2. 双路召回与多维过滤引擎

- [x] 2.1 实现关键词全文检索加权召回模块（标题权重最高，其次标签、摘要、正文）
- [x] 2.2 实现向量语义相似度召回模块（基于余弦距离，提供环境兼容向量计算回退支持）
- [x] 2.3 整合分类级联（父分类包含子分类）与多标签等结构化过滤约束

## 3. 分数归一化、加权融合与分块聚合

- [x] 3.1 实现混合评分归一化加权融合算法（关键词分 40% + 向量语义分 50% + 标题完全命中加权 10%）
- [x] 3.2 实现以知识点（`knowledge_id`）为粒度聚合去重，并提取最佳命中分块片段（Best Snippet）

## 4. 充分性判定与统一搜索 API

- [x] 4.1 实现搜索 DTO 数据契约 `backend/app/schemas/search.py`，定义统一搜索出入参、充分性指标与 AI 引导字段
- [x] 4.2 实现混合搜索领域服务 `backend/app/services/search_service.py`，串联双路召回、加权融合、分块聚合与充分性判定
- [x] 4.3 实现统一搜索 API 路由 `backend/app/api/search.py` 并在 `backend/app/main.py` 挂载

## 5. 端到端集成测试与全量回归验收

- [x] 5.1 编写混合搜索、充分性判定（充足 vs 不足）、多维过滤等完整场景集成测试 `backend/tests/test_search_api.py`
- [x] 5.2 运行全量测试套件（新旧全部用例），执行静态类型检查，确保 100% 验收通过
