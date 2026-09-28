## 1. 修复底层 API 客户端与删除功能

- [x] 1.1 修复 `frontend/src/lib/api.ts` 中 `request` 函数对 HTTP 204 No Content / 空响应体的处理，杜绝 JSON 解析报错
- [x] 1.2 验证移入回收站、从回收站恢复、物理删除的无感刷新与提示逻辑

## 2. 前端 Block 转换工具与编辑器表单组件

- [x] 2.1 创建 `frontend/src/lib/blocks.ts`，实现 `markdownToBlocks` 与 `blocksToMarkdown` 结构化转换函数
- [x] 2.2 封装通用编辑器表单组件 `frontend/src/components/knowledge/KnowledgeEditorForm.tsx`，支持标题、摘要、分类、标签、状态、收藏及正文 Markdown 录入与即时预览

## 3. 实现新建与编辑知识点功能

- [x] 3.1 创建新建知识点页面 `frontend/src/app/knowledge/new/page.tsx`，接入 `KnowledgeEditorForm mode="create"`，解决路由 404 与新建不可用问题
- [x] 3.2 创建编辑知识点页面 `frontend/src/app/knowledge/[id]/edit/page.tsx`，接入 `KnowledgeEditorForm mode="edit"`，支持预填与保存更新
- [x] 3.3 在详情页 `frontend/src/app/knowledge/[id]/page.tsx` 顶部操作栏补齐【编辑】按钮

## 4. 知识库列表模式改造与入口完善

- [x] 4.1 重构 `frontend/src/app/knowledge/page.tsx`：默认以紧凑结构化的列表视图（List View 表格）展示，支持标题、分类、标签、状态、收藏、更新时间与操作列
- [x] 4.2 在列表页顶部操作栏增加【+ 新建知识点】主按钮，在每一行操作列中增加【编辑】图标
- [x] 4.3 支持列表视图（List View）与卡片视图（Card View）切换切换机制，默认保存用户偏好

## 5. 端到端功能验证与回归测试

- [x] 5.1 验证“新建知识点”完整流程（从创建到自动索引再到详情浏览）
- [x] 5.2 验证“编辑知识点”完整流程（修改标题、正文与标签，更新并查看详情）
- [x] 5.3 验证“删除知识点”完整流程（从列表/详情移入回收站，在回收站查看并恢复或彻底删除）
- [x] 5.4 验证全量列表与筛选、卡片/列表切换及全部 63 项后端单元测试无回归
