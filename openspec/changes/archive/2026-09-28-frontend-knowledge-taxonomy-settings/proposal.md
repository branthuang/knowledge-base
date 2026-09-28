# Change Proposal: 知识库列表、分类标签体系、回收站与系统设置前端交互 (frontend-knowledge-taxonomy-settings)

## 1. 目标与价值 (Goal & Value)
在完成第六阶段“工作台看板与统一搜索中心（含 AI 搜索与知识回流）”后，本阶段全面实现知识资产的日常维护、分类整理、安全生命周期与数据治理：
1. **知识库列表与详情浏览 (`/knowledge`, `/knowledge/[id]`)**：
   - 支持多维组合检索（分类、标签、发布/草稿状态、收藏）；
   - 提供知识详情阅读器、结构化内容块渲染与单篇 Markdown 导出下载；
   - 支持快捷编辑、状态切换与安全软删除（移入回收站）。
2. **分类与标签体系治理 (`/taxonomy`)**：
   - 树状分类管理：新建分类、无限级子分类、编辑属性（名称、颜色）、删除保护机制（关联知识重新指派或阻断）；
   - 标签系统管理：标签列表、知识引用计数、原子事务合并（将同义重复标签安全合并）。
3. **安全回收站 (`/trash`)**：
   - 软删除知识列表查看、一键恢复到知识库、物理彻底清除。
4. **数据备份与系统设置 (`/settings`)**：
   - 一键导出全量标准 ZIP 归档（带 SHA-256 签名）；
   - 上传 ZIP 原子全量恢复导入；
   - 一键触发全量向量语义索引重建。

---

## 2. 关联 Capability Specs
- `openspec/specs/knowledge-management/spec.md`
- `openspec/specs/category-management/spec.md`
- `openspec/specs/tag-system/spec.md`
- `openspec/specs/backup-restore/spec.md`
- `openspec/specs/system-settings/spec.md`

---

## 3. 风险与缓解 (Risks & Mitigations)
- **分类删除关联知识风险**：后端已具备关联检测拦截机制，前端提供对话框让用户显式选择将知识“重新指派给其他分类”或“转为未分类”，杜绝数据孤立。
- **标签合并数据一致性**：调用后端 `/api/tags/merge` 事务接口，合并后自动无感刷新标签列表与关联计数。
- **备份还原体验**：提供清晰上传进度与还原成功的即时反馈。
