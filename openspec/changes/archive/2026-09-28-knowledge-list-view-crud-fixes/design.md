# Technical Design: 知识库列表模式改造、新建/编辑功能补齐与删除异常修复

## 1. 架构与交互设计 (Architecture & Interaction)

```mermaid
graph TD
    A[知识库列表 /knowledge] -->|点击新建知识点| B[新建页面 /knowledge/new]
    A -->|点击表格项| C[知识详情页 /knowledge/[id]]
    A -->|点击行内编辑按钮| D[编辑页面 /knowledge/[id]/edit]
    C -->|点击顶部编辑按钮| D
    C -->|点击移入回收站| E[调用 DELETE /api/knowledge/{id}]
    A -->|点击行内删除图标| E
    
    B -->|复用表单组件| F[KnowledgeEditorForm]
    D -->|复用表单组件| F
    F -->|保存| G[调用 POST /api/knowledge 或 PUT /api/knowledge/{id}]
    
    subgraph 底层通信修正
        E --> H[api.ts: request 函数]
        H -->|支持 HTTP 204 No Content| I[FastAPI 后端]
    end
```

---

## 2. 核心模块与实现细节

### 2.1 底层 API 通信修复 (`frontend/src/lib/api.ts`)
- **根因**：后端软删除 (`DELETE /api/knowledge/{id}`) 与硬删除 (`DELETE /api/knowledge/{id}/permanent`) 返回 HTTP 204 No Content。当前 `request<T>` 无论状态码一律执行 `response.json()`，触发 `SyntaxError: Unexpected end of JSON input`。
- **方案**：
  ```ts
  if (response.status === 204) {
    return {} as T;
  }
  const text = await response.text();
  if (!text || text.trim() === '') {
    return {} as T;
  }
  return JSON.parse(text) as T;
  ```
  彻底解决 204 报错问题，并保障所有删除与恢复动作正常刷新页面状态。

### 2.2 前端双向 Block 转换工具 (`frontend/src/lib/blocks.ts`)
- 实现 `markdownToBlocks(md: string): BlockItem[]`：
  - 自动识别层级标题 `# ~ ####`、待办 `- [ ]`、列表 `- ` / `1.`、代码块 ` ``` `、引用 `> `、水平分割线 `---`、段落文本；
  - 自动为每个 Block 生成客户端 UUID。
- 实现 `blocksToMarkdown(blocks: BlockItem[]): string`：
  - 将后端返回的 `BlockItem[]` 逆向无损还原为标准 GitHub Flavored Markdown 文本，用于填充编辑器的多行输入框。

### 2.3 高复用编辑器组件 (`frontend/src/components/knowledge/KnowledgeEditorForm.tsx`)
- **功能特性**：
  - 双模式支持：`create`（新建）与 `edit`（编辑现有知识点）；
  - **基础元数据区**：
    - 标题（Title）：带必填校验与字数统计；
    - 摘要（Summary）：自动/手动提取简短描述；
    - 主分类选择器：加载 `/api/categories`，支持选择或设为未分类；
    - 标签多选选择器：加载 `/api/tags`，支持点击关联/移除已有标签，或即时新建标签；
    - 发布状态（Status）：草稿（draft）、已发布（published）、已归档（archived）；
    - 收藏置顶切换（Favorite）；
  - **正文编辑区**：
    - 快捷工具栏（标题、加粗、列表、代码块、引用、表格）；
    - 支持 Markdown 模式与即时预览 Tab 切换（“编辑正文” / “即时效果预览”）；
  - **提交行为**：
    - 新建：提交至 `POST /api/knowledge`，成功后跳转至 `/knowledge/${newItem.id}`；
    - 编辑：提交至 `PUT /api/knowledge/${id}`，成功后跳转回 `/knowledge/${id}`。

### 2.4 独立路由页面
- **新建页面**：`frontend/src/app/knowledge/new/page.tsx`
  - 渲染 `KnowledgeEditorForm mode="create"`。
  - Next.js 静态路由自然优先于 `[id]` 动态匹配，从根源消除 404。
- **编辑页面**：`frontend/src/app/knowledge/[id]/edit/page.tsx`
  - 获取知识点当前详情，渲染 `KnowledgeEditorForm mode="edit"`。

### 2.5 知识库列表重构为列表视图 (`frontend/src/app/knowledge/page.tsx`)
- **布局升级**：
  - 顶部操作栏右侧增加显眼的 `+ 新建知识点` 主按钮；
  - 增加视图模式切换控件：`列表视图（List View）`（默认）/ `卡片视图（Card View）`；
  - **列表模式（List View）**采用现代数据表格：
    - `标题与摘要`：粗体标题（悬浮高亮，点击直达详情），副标题展示 1~2 行灰色摘要预览；
    - `分类`：彩色分类徽章（带分类图标与色块）；
    - `标签`：最多展示前 3 个标签徽章，超出显示 `+N`；
    - `状态`：已发布（绿色）、草稿（橙黄色）、已归档（灰色）；
    - `收藏`：星标图标，点击直接切换收藏状态并不影响行跳转；
    - `更新时间`：友好的本地化时间；
    - `操作`：
      - 编辑图标（跳转 `/knowledge/[id]/edit`）；
      - 导出 Markdown 图标；
      - 移入回收站图标（安全二次确认弹窗）。
- **详情页补齐入口**：`frontend/src/app/knowledge/[id]/page.tsx`
  - 顶部操作栏增加【编辑知识点】按钮（`Edit` 图标），点击直达 `/knowledge/[id]/edit`。
