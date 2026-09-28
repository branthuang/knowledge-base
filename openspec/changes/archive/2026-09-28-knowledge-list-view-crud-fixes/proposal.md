# Change Proposal: 知识库列表模式改造、新建/编辑功能补齐与删除异常修复 (knowledge-list-view-crud-fixes)

## 1. 目标与背景 (Why)

在完成核心功能与文档导入后，用户在实际操作知识库资产时遇到以下核心痛点：
1. **知识库列表展示模式不佳**：
   - 当前 `/knowledge` 页面采用三列卡片（Card Grid）布局，在知识条目增多后，卡片形式高度冗余、纵向滚动长、信息密度低，不利于快速扫视、批量对比与定位。用户要求以结构清晰的**列表/表格方式（List View）**展示。
2. **“新建知识点”功能不可用**：
   - 工作台看板中的“新建知识点”链接到 `/knowledge/new`，但前端未定义该静态路由页面。Next.js 将其作为动态参数匹配到 `/knowledge/[id]`，导致向后端请求 UUID 为 `new` 的详情并触发 404 错误。且知识库列表页本身缺少新建入口。
3. **缺少知识点编辑功能**：
   - 知识点详情页和列表页均无编辑入口，无法修改已沉淀知识的标题、摘要、分类、标签、正文 Blocks 及发布状态。
4. **删除功能无法正常执行**：
   - 后端软删除与物理删除接口返回标准 HTTP 204 No Content，前端 `api.ts` 中的通用 `request` 函数未处理空响应体直接调用 `response.json()`，导致抛出 `SyntaxError: Unexpected end of JSON input` 异常，弹出“移入回收站失败”报错。

---

## 2. 变更内容 (What Changes)

### 2.1 知识库列表展示模式改造 (List View)
- 将 `/knowledge` 默认布局重构为紧凑、结构化的**列表视图（List View）**：
  - 核心列：标题与摘要预览、所属分类徽章、标签列表、发布状态（已发布/草稿/已归档）、收藏星标、更新时间、操作列；
  - 操作列：编辑、导出 Markdown、移入回收站；
  - 提供视图切换功能（列表视图 List View 为默认推荐模式，卡片视图 Card View 为可选模式）；
  - 列表顶部右侧新增显眼的【+ 新建知识点】主行动按钮。

### 2.2 补齐“新建知识点”功能与页面 (`/knowledge/new`)
- 创建 `/knowledge/new` 路由页面，避开动态路由匹配冲突；
- 封装高复用性编辑器表单组件 `KnowledgeEditorForm`：
  - 支持录入标题（必填）、摘要、主分类下拉、标签多选绑定、发布状态选择、收藏设置；
  - 支持多行 Markdown / 富文本内容录入；
  - 保存后自动解析为 BlockItem 结构，调用后端 `POST /api/knowledge` 创建并自动触发向量索引，完成后无缝跳转至详情页。

### 2.3 补齐“编辑知识点”功能 (`/knowledge/[id]/edit`)
- 创建 `/knowledge/[id]/edit` 路由页面，复用 `KnowledgeEditorForm`；
- 进入编辑页时自动加载当前知识点详情，正文 Blocks 自动还原为 Markdown 编辑文本；
- 详情页 `/knowledge/[id]` 顶部操作栏新增【编辑】按钮；列表页操作栏同步增加【编辑】图标；
- 提交更新调用 `PUT /api/knowledge/{id}`，成功后保存并自动联动待更新索引，返回详情页。

### 2.4 修复删除功能 HTTP 204 异常
- 修复 `frontend/src/lib/api.ts` 中的 `request` 方法：
  当 `response.status === 204` 或响应头表明无内容时，直接返回空对象，杜绝调用 `response.json()` 导致的解析崩溃；
- 确保列表页、详情页、回收站页的移入回收站、恢复、物理彻底删除均能顺畅闭环并给出正确的交互反馈。

---

## 3. 关联规范 (Capabilities)

- `openspec/specs/knowledge-management/spec.md`:
  - 增补：知识库列表支持列表视图与卡片视图切换；
  - 增补：知识点在线新建与编辑流转能力；
  - 增补：软删除与硬删除的前端无损调用与状态即时同步。

---

## 4. 风险与缓解 (Risks & Mitigations)

- **Markdown 与 Block 转换保真度**：
  - 前端利用已有的 `markdown_to_blocks` 与 `blocks_to_markdown` 进行双向映射，并在保存前提供预览，确保标题、列表、代码块、表格等不失真。
- **路由优先级**：
  - Next.js App Router 静态目录 `knowledge/new/page.tsx` 天生优先于动态目录 `knowledge/[id]/page.tsx`，无冲突风险。
