## 1. 前端基础架构与 API SDK

- [x] 1.1 配置 TailwindCSS、PostCSS 与全局样式 `frontend/src/app/globals.css`
- [x] 1.2 编写类型安全 API SDK `frontend/src/lib/api.ts` 与数据契约 `frontend/src/lib/types.ts`
- [x] 1.3 实现全局响应式侧边栏导航与根布局 `frontend/src/app/layout.tsx`

## 2. 首页知识工作台 (Workbench Dashboard)

- [x] 2.1 实现工作台宏观统计指标卡片与待整理草稿动态组件
- [x] 2.2 实现居中置顶统一搜索引导输入组件
- [x] 2.3 完成首页工作台集成 `frontend/src/app/page.tsx`（连接 `/api/workbench/stats` 与 `/api/workbench/activities`）

## 3. 统一搜索中心与知识回流抽屉

- [ ] 3.1 实现 4 种搜索模式切换控件与多维结构化过滤侧栏（级联分类树与多标签）
- [ ] 3.2 实现本地知识命中卡片、充分性提示条与 AI 增强回答（附带可追溯公网 Citations）组件
- [ ] 3.3 实现知识回流入库预览与相似防重抽屉 `frontend/src/components/inflow/InflowDrawer.tsx`
- [ ] 3.4 完成统一搜索中心页面端到端交互串联 `frontend/src/app/search/page.tsx`

## 4. 前端构建校验与端到端质量验收

- [ ] 4.1 执行静态类型校验（TypeScript `tsc --noEmit`），确保前端工程无报错并与后端接口完全对齐
