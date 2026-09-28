## Context

系统已具备完整的 PostgreSQL 数据表、Alembic 迁移脚本与 SQLAlchemy ORM 模型。
在此基础上，需要实现领域服务（Services）、Pydantic 数据验证契约（Schemas）、RESTful 控制器（APIs）以及针对 PRD 核心业务规则的强校验逻辑。

## Goals / Non-Goals

**Goals:**
- 提供严谨的 Pydantic V2 请求与响应数据契约（DTOs）。
- 实现块模型（Block Models）校验与纯文本解析提取器，确保任何写入知识点的 blocks 均能自动派生精确的 `plain_text`。
- 实现分类管理服务：支持层级树构建、分类停用、删除安全保护（迁移/设为未分类）以及父子级联过滤。
- 实现标签管理服务：支持标签 CRUD、知识关联统计以及关键的“标签合并”事务。
- 实现知识管理服务：支持完整 CRUD、阅读与编辑视图模式、状态流转（draft、published、archived、trashed）、回收站恢复与彻底删除。
- 编写完备的自动化集成测试套件，覆盖业务边界与异常场景。

**Non-Goals:**
- 本阶段不执行实际的全文检索与向量相似度计算（留待 M3 阶段集中实现）。
- 本阶段不接入外部 AI 联网搜索调用与流式生成（留待 M4 阶段实现）。

## Decisions

1. **块数据结构设计（Block Data Schema）**：
   - 每个块具备 `id`（UUID）、`type`（字符串枚举）、`properties`（字典）、`content`（字符串或结构化内容）、`children`（可选嵌套子块）。
   - 纯文本提取器（`extract_plain_text`）：递归遍历 blocks，拼接段落、标题、列表项、代码、表格单元格文本，保持词间与行间合理间距，去除控制符，作为后续 FTS 与 Embedding 的权威纯文本源。
2. **分类删除保护策略（Category Deletion Guard）**：
   - 提供参数 `reassign_to_id: Optional[str]`：
     - 若分类下存在知识点且未提供 `reassign_to_id`，抛出 HTTP 400 业务异常（包含关联知识数量），阻断删除；
     - 若提供 `reassign_to_id`（目标分类 ID），事务中批量更新关联知识的 `category_id`；
     - 若 `reassign_to_id="unclassified"` 或指定置空，批量将关联知识的 `category_id` 置为 `None`。
3. **标签合并事务（Tag Merge Transaction）**：
   - 接收 `source_tag_id` 与 `target_tag_id`；
   - 查询所有绑定了 `source_tag_id` 的知识；
   - 对于已同时绑定目标标签的知识，仅删除源标签关联；对于未绑定目标标签的知识，更新关联为目标标签；
   - 彻底删除源标签，保障无重复无孤儿记录。
4. **软删除与回收站隔离（Trash & Soft Delete）**：
   - 知识列表与搜索默认过滤 `status != 'trashed'`；
   - 提供专门的 `/api/knowledge/trash` 路由查看与管理回收站中的知识；
   - 彻底删除需显式调用 `DELETE /api/knowledge/{id}/permanent`。

## Risks / Trade-offs

- **风险 1：块结构嵌套过深导致文本提取栈溢出**
  - *缓解措施*：纯文本提取器采用迭代循环配合深度限制（上限 10 层嵌套），避免递归耗尽堆栈。
- **风险 2：标签合并时多对多关系唯一键冲突**
  - *缓解措施*：先在数据库中批量查询现有绑定，使用差集（Set Difference）精准更新，避免违反 `uq_knowledge_tag` 唯一性约束。
