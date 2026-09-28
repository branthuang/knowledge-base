## 1. 知识库列表与详情浏览页面

- [x] 1.1 实现知识库多维检索与卡片列表页面 `frontend/src/app/knowledge/page.tsx`
- [x] 1.2 实现结构化内容块与溯源参考阅读页面 `frontend/src/app/knowledge/[id]/page.tsx`
- [x] 1.3 串联单篇 Markdown 导出下载与安全移入回收站交互

## 2. 分类与标签治理中心

- [x] 2.1 实现树状分类层级管理交互（新建顶级/子级分类、编辑属性与安全重分配删除）
- [x] 2.2 实现标签列表、创建与原子事务合并弹窗（调用 `/api/tags/merge`）
- [x] 2.3 完成分类与标签统一管理页面 `frontend/src/app/taxonomy/page.tsx`

## 3. 安全回收站与系统备份设置

- [ ] 3.1 实现回收站列表、一键恢复与彻底删除页面 `frontend/src/app/trash/page.tsx`
- [ ] 3.2 实现全量标准 ZIP 导出下载、ZIP 文件上传恢复与全量向量重建交互页面 `frontend/src/app/settings/page.tsx`

## 4. 全局编译构建与端到端质量验收

- [ ] 4.1 执行前端静态类型校验（`npm run typecheck`）与生产构建（`npm run build`），确保全站路由畅通无阻
