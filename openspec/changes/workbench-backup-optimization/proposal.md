# Change: 工作台看板、AI 智能优化与数据备份恢复 (workbench-backup-optimization)

## Why

目前系统已完成数据底座（M1）、知识与分类标签核心管理（M2）、双路混合检索（M3）以及 AI 搜索与知识沉淀入库（M4）。
为了实现整个个人知识库系统（MVP 阶段）的完整商业级交付闭环，还需要打通：
1. **工作台统计看板（Workbench Dashboard）**：提供系统宏观沉淀指标（知识总数、分类总数、标签总数、本月新增、AI 沉淀转化数）、待整理草稿提醒、近期编辑和最近搜索历史，为前端提供高频统一的工作台 API。
2. **AI 智能优化与安全对比（AI Optimization）**：在知识编辑过程中提供一键纠错、润色与结构化整理（MVP 简洁易懂模式），输出结构化前后差异与标签分类推荐，严格防篡改与防幻觉。
3. **数据备份与无损恢复（Backup & Restore）**：确保个人知识资产主权，支持一键打包导出 ZIP（包含分类、标签、知识点 blocks、来源、manifest.json 与校验和），支持完整校验恢复导入，以及单篇知识无损导出为 Markdown。

## What Changes

1. **工作台看板服务（Workbench Dashboard）**：
   - 实现 `GET /api/workbench/stats`: 聚合 5 项核心指标（知识总量、分类数、标签数、本月新增、AI 转化沉淀数）。
   - 实现 `GET /api/workbench/activities`: 聚合最近编辑的知识、待整理的 AI 沉淀草稿列表以及最近的搜索会话。

2. **AI 编辑器优化服务（AI Optimization）**：
   - 实现 `POST /api/optimization/polish`: 调用 LLM 提供“简洁易懂”文本润色、格式理顺，输出优化后的块草稿、修改差异说明及推荐的分类/标签建议。

3. **数据备份与恢复服务（Backup & Restore）**：
   - 实现 `GET /api/backup/export`: 全量导出知识库数据为包含 `manifest.json` 与 `data.json` 的标准 ZIP 归档包。
   - 实现 `POST /api/backup/restore`: 上传校验并恢复导入数据库记录，自动联动重建向量索引。
   - 实现 `GET /api/knowledge/{id}/export/markdown`: 单篇知识无损导出为标准 GitHub Flavored Markdown 文本流。

4. **端到端集成测试与验收**：
   - 编写看板统计、AI 优化、ZIP 导出/导入恢复及 Markdown 导出的单元与集成测试套件。

## Capabilities

### New Capabilities
- `workbench-dashboard`: 工作台看板、资产统计与动态流转。
- `ai-optimization`: 编辑器一键 AI 润色与智能打标。
- `backup-restore`: 数据全量打包备份、原子恢复与单篇 Markdown 导出。

### Modified Capabilities
- `knowledge-management`: 增加单篇 Markdown 导出端点。
