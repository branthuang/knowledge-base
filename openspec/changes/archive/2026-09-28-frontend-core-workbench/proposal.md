# Change: 前端工程搭建、工作台与统一搜索交互界面 (frontend-core-workbench)

## Why

目前后端 5 个阶段的核心领域服务、RESTful API 与数据层已全部高质量完成（63 个自动化测试 100% 通过）。
根据 PRD 与“先查自己的知识，再向 AI / 公网提问；有价值的搜索结果由用户确认后沉淀为可持续维护、可检索、可追溯的知识”核心原则，用户需要直观、现代、流畅的 Web 交互界面：
1. **全局导航与工作台（Workbench Dashboard）**：居中统一搜索入口、宏观指标卡片、待整理草稿提醒徽章、最近编辑知识与搜索会话历史；
2. **统一搜索交互中心（Search Center）**：支持 4 种搜索模式切换、多维级联分类与标签筛选、本地命中知识卡片高亮匹配片段，以及当本地充分性不足时智能展现 AI 搜索综合回答与公网引用列表；
3. **知识回流抽屉/弹窗（Inflow Modal）**：在 AI 搜索结果卡片上一键“收藏到知识库”，展示结构化 Blocks 预览、智能推荐的标题/摘要/分类/标签，以及高相似防重提醒与人工确认落盘。

## What Changes

1. **前端工程配置与 API 契约客户端（Frontend Foundation & API SDK）**：
   - 初始化 Next.js 14 App Router 结构、TailwindCSS 样式体系与 Lucide 图标库。
   - 封装严格对齐后端 OpenAPI 契约的类型安全 API 客户端 (`frontend/src/lib/api.ts`)。

2. **全局布局体系（Global Layout & Navigation）**：
   - 侧边栏导航：工作台（Dashboard）、知识库列表（Knowledge）、分类标签管理（Categories & Tags）、回收站（Trash）、系统备份与设置（Settings）。
   - 顶部全局导航栏：全局快捷搜索触发器、新建知识快捷按钮。

3. **首页知识工作台（Home / Workbench Dashboard）**：
   - 页面中心置顶大幅统一搜索框（“搜索你的知识；找不到再问 AI”）。
   - 5 项核心宏观统计卡片（知识总数、分类总数、标签总数、本月新增、AI沉淀转化数）。
   - 待整理草稿（Pending Review Drafts）提醒卡片与数量徽章。
   - 最近编辑知识列表、最近 AI 搜索历史、常用高频标签快捷入口。

4. **统一搜索结果与 AI 问答交互页（Unified Search Page）**：
   - 搜索模式切换控件（知识优先、仅知识库、外部补充、直接 AI）。
   - 多维结构化筛选面板（分类树级联展开、多标签选择、来源过滤）。
   - 检索结果渲染：
     - 本地知识卡片：高亮最佳匹配片段（Best Snippet）、匹配得分与分类标签；
     - 充分性不足时的高亮引导条（“本地知识库匹配不足，建议向 AI 搜索获取更全面的解答”）；
     - AI 增强回答卡片：展示总结性回答、可追溯公网链接引用列表（Citations）、关联内部知识点引用标签；
     - “收藏到知识库”交互入口与入库预览抽屉（智能元数据编辑、相似防重提醒与确认落盘）。

## Capabilities

### New Capabilities
- `workbench-dashboard`: 前端工作台看板页面与宏观统计渲染。
- `hybrid-search`: 前端统一搜索交互界面与多维过滤面板。
- `ai-search`: 前端 AI 问答渲染、多模式切换与引用追溯展示。
- `knowledge-inflow`: 前端一键收藏到知识库预览抽屉与相似防重确认。

## Impact

- 前端代码目录：
  - `frontend/src/lib/api.ts`: API 客户端
  - `frontend/src/lib/types.ts`: TypeScript 接口模型定义
  - `frontend/src/app/layout.tsx`: 根布局与侧边栏导航
  - `frontend/src/app/page.tsx`: 工作台首页
  - `frontend/src/app/search/page.tsx`: 统一搜索与 AI 问答中心
  - `frontend/src/components/inflow/InflowDrawer.tsx`: 知识回流预览与确认抽屉
  - `frontend/src/components/search/SearchBox.tsx`: 统一搜索框组件
  - `frontend/src/components/search/FilterSidebar.tsx`: 分类级联与标签筛选组件
