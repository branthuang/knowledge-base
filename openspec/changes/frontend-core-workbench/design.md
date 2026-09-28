## Context

后端全部能力已闭环。本阶段完成前端核心交互基座搭建，为用户呈现全局工作台、统一搜索结果页与知识回流确认抽屉。

## Goals / Non-Goals

**Goals:**
- 初始化标准 Next.js 14 App Router 页面骨架、TailwindCSS 样式系统与 TypeScript 类型定义。
- 封装类型安全的前端 API 客户端（`frontend/src/lib/api.ts`）。
- 实现全局统一布局（Sidebar 导航栏、顶部快捷操作栏）。
- 实现首页知识工作台（`/`）：
  - 居中置顶统一搜索框；
  - 5 项核心宏观统计卡片（知识总数、分类总数、标签总数、本月新增、AI沉淀转化数）；
  - 待整理草稿卡片（徽章提醒与快捷处理）；
  - 最近知识与近期搜索历史列表。
- 实现统一搜索与 AI 问答中心（`/search`）：
  - 4 种搜索模式切换；
  - 分类树级联展开与多标签交集筛选；
  - 本地知识卡片展示与充分性高亮指示器；
  - AI 增强搜索回答卡片（渲染 Markdown 格式、公网引用链接列表、关联内部知识引用）；
  - “收藏到知识库”入库抽屉（Blocks 预览、智能元数据调整、相似知识防重提醒、确认入库落盘）。

**Non-Goals:**
- 本阶段不实现复杂画板（Canvas/Mermaid）高级交互渲染（MVP 阶段聚焦基础文字、代码、列表、引用块）。
- 完整独立块富文本编辑器页面（新建/编辑知识点 `/knowledge/edit`）将在下一前端阶段全面完善。

## Decisions

1. **统一搜索状态机设计**：
   - 模式切换响应：
     - `knowledge_first`: 优先调用 `/api/search`。若 `is_sufficient=true`，优先展示本地高分知识卡片；若 `is_sufficient=false`，自动无缝启动 `/api/ai-search` 获取公网补充回答；
     - `knowledge_only`: 仅调用 `/api/search` 与纯本地问答，禁止外部引用；
     - `external_supplement` / `direct_ai`: 触发 `/api/ai-search`，展示 AI 综合答案与公网引用。
2. **入库防重交互闭环（Duplicate Inflow Guard）**：
   - 点击“收藏到知识库”后，调用 `/api/inflow/preview` 获取草稿与相似度分析。
   - 若 `has_similar_knowledge == true`，在抽屉顶部突出显示警示条，列出相似知识对比卡片，并提供“坚持创建为新知识”与“更新已有知识”单选切换。
