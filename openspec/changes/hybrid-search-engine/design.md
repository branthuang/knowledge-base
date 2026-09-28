## Context

知识库已支持知识点、分类和标签的完整生命周期管理。但检索系统尚未打通。
根据 PRD 要求，搜索必须是统一入口，先查本地，本地不足再引向 AI。

## Goals / Non-Goals

**Goals:**
- 实现文本分块算法（`Chunker`），保证长文被合理切割为 300~500 字符的独立语义单元，保留上下文重叠。
- 实现单篇及全量知识点索引管线（`IndexService`），调用 `BaseEmbeddingProvider` 批量计算向量，持久化到 `embedding_chunks`。
- 实现双路召回：
  1. 关键词通道（Keyword/FTS）：对标题、摘要、标签、正文做加权匹配。
  2. 语义通道（Vector）：pgvector 余弦距离计算与 Top-K 召回。
- 实现分数归一化与加权融合（解决 Open Question 5）：
  $$\text{FusedScore} = 0.4 \times S_{keyword\_norm} + 0.5 \times S_{vector\_norm} + 0.1 \times \text{TitleBonus}$$
- 实现分块向知识点聚合，并挑选最佳匹配文本片段（Best Snippet）。
- 实现充分性判定（Sufficiency Check）：Top-1 综合得分低于 `minimum_score`（默认 0.60）或有效命中数为 0 时，判定为 `is_sufficient=False` 并输出引导。
- 编写端到端集成测试，验证双路召回、充分性判定及分类标签过滤。

**Non-Goals:**
- 本阶段不调用真实的公网网页搜索服务（留待 M4 阶段与 AI 搜索闭环打通）。
- 本阶段不引入重排（Reranker）深度模型（按 PRD 归属于 P2 阶段）。

## Decisions

1. **分块策略（Chunking Strategy）**：
   - 优先按块边界（Blocks）切分；
   - 若单个块文本超过 500 字符，按段落/换行二次切分，并保留 50 字符滑动重叠窗口（Overlap）；
   - 保留 `block_id` 关联，便于未来精确定位到原内容块。
2. **分数归一化与融合方案（Score Normalization & Fusion）**：
   - 向量相似度采用余弦相似度（Cosine Similarity），天然处于 `[0, 1]` 范围；
   - 全文关键词匹配采用词频与字段权重评分，通过 Min-Max 或 Sigmoid 函数缩放归一化到 `[0, 1]`；
   - 融合公式赋权：向量分 50% + 关键词分 40% + 标题完全命中加权 10%，最终融合分严格限制在 `[0, 1]`。
3. **充分性判定（Sufficiency Evaluation）**：
   - 设定阈值 `MINIMUM_SCORE = 0.60`；
   - 若聚合后 Top-1 结果分数 $\ge$ 0.60，`is_sufficient = True`；
   - 若最高分 < 0.60 或有效结果为 0，`is_sufficient = False`，提示“本地知识库匹配不足，建议向 AI 搜索获取更全面的解答”。
4. **环境适配性（SQLite / Postgres 双环境兼容测试）**：
   - 在 Docker PostgreSQL 环境中直接使用 pgvector 运算符；
   - 在本地单测无 PG 环境（SQLite）时，提供内存向量余弦相似度计算回退逻辑，保证单元测试与 CI 均可 100% 自动化跑通。

## Risks / Trade-offs

- **风险 1：长文分块过多导致 Embedding 接口限流或缓慢**
  - *缓解措施*：分块服务支持批量计算（Batching，每批 16~32 个分块），并在索引服务中记录状态。
- **风险 2：冷启动时本地无知识导致搜索报错**
  - *缓解措施*：充分性判定天然兼容 0 结果，输出友好的空状态与 AI 搜索引导。
