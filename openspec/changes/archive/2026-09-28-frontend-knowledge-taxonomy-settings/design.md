# Technical Design: 知识库管理、分类标签体系、回收站与系统设置前端交互 (frontend-knowledge-taxonomy-settings)

## 1. 架构与组件拓扑

```
frontend/src/app/
├── knowledge/
│   ├── page.tsx                     # 知识库管理列表页面 (过滤栏、卡片列表、分页、批量/快捷操作)
│   └── [id]/
│       └── page.tsx                 # 知识点详情阅读器 (正文块渲染、元数据属性、溯源外链、单篇MD导出)
├── taxonomy/
│   └── page.tsx                     # 分类与标签管理中心 (左侧分类树CRUD，右侧标签管理与原子合并Modal)
├── trash/
│   └── page.tsx                     # 安全回收站 (软删除知识卡片、一键恢复、彻底永久删除)
└── settings/
    └── page.tsx                     # 系统设置与数据备份 (ZIP导出/还原、向量索引重建、引擎健康诊断)
```

## 2. 页面与组件交互设计

### 2.1 知识库列表 (`/knowledge`)
- 顶部快捷操作栏：分类筛选下拉、状态筛选按钮（全部 / 已发布 / 待整理草稿）、搜索框、新建按钮；
- 知识卡片流：展示标题、摘要、分类胶囊、标签列表、发布状态、更新时间、收藏星标；
- 卡片操作菜单：单篇 Markdown 导出（调用 `/api/backup/export/markdown/{id}` 直接下载）、移入回收站（调用 `DELETE /api/knowledge/{id}`）。

### 2.2 知识详情与阅读页 (`/knowledge/[id]`)
- 顶部导航栏：返回列表、编辑按钮、导出 Markdown 按钮、移入回收站；
- 元数据面板：分类、标签、创建/更新时间、来源类型；
- 内容块渲染器：逐块渲染 Paragraph、Heading (H1-H4)、List、Code (代码高亮样式)、Quote、Callout、Divider 等；
- 底部溯源区域：展示外部参考资料与 AI 搜索原始会话追溯链接。

### 2.3 分类与标签治理 (`/taxonomy`)
- 双栏布局：
  - 左栏（分类树）：
    - 树状层级展开/收起；
    - 新建顶级/子级分类模态框；
    - 编辑分类模态框；
    - 删除分类模态框（提供关联知识重新分配选项：未分类 / 其他分类）。
  - 右栏（标签管理）：
    - 标签列表与知识引用计数；
    - 新增标签输入；
    - 标签合并操作抽屉/弹窗：选择源标签与目标标签，调用 `/api/tags/merge` 实现安全无缝合并。

### 2.4 回收站 (`/trash`)
- 列表展示软删除知识点；
- 动作：
  - 一键恢复 (`POST /api/knowledge/trash/{id}/restore`)；
  - 彻底物理删除 (`DELETE /api/knowledge/{id}/permanent`) 并附带二次防误触确认。

### 2.5 系统备份与设置 (`/settings`)
- 数据归档导出：一键导出包含 `data.json` 与 SHA-256 签名 `manifest.json` 的标准 ZIP 备份文件；
- 数据备份还原：拖拽上传 ZIP 文件并提交 `/api/backup/restore`，展示恢复成功与重建索引通知；
- 索引维护：一键触发 `/api/search/reindex` 重建派生分块与 pgvector 语义向量索引；
- 连通性状态卡片：展示后端 API、PostgreSQL 16 与 Redis 7 运行状态。
