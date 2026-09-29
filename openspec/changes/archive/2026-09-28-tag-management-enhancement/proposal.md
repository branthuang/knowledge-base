# Change Proposal: 知识标签悬浮快捷重命名与解绑删除能力 (tag-management-enhancement)

## 1. 目标与背景 (Why)

在系统当前的分类与标签治理模块（`/taxonomy`）中：
1. **分类体系（Category）** 拥有完善的生命周期管理（添加子分类、编辑属性、删除防孤立保护）；
2. **标签体系（Tag）** 现状：
   - 后端服务（`backend/app/api/tags.py` 与 `tag_service.py`）早已实现完整的 `POST`（创建）、`PUT`（更新）、`DELETE`（级联解绑删除）与 `merge`（原子合并）能力；
   - 但前端 API 客户端（`frontend/src/lib/api.ts`）遗漏了 `update` 和 `delete` 方法的封装；
   - 前端管理页面（`/taxonomy`）将标签徽章做成了纯静态展示，用户无法直接重命名标签名称，也无法清理废弃或错误的标签。

为了补齐标签日常治理的核心闭环，同时遵循“MVP 保持极简直观、避免过度设计”的原则，本变更将为标签徽章补齐**悬浮快捷重命名**与**确认后直接解绑删除**能力。

---

## 2. 变更范围与核心决策 (Scope & Decisions)

### 2.1 变更内容 (What Changes)
1. **API 客户端补齐 (`frontend/src/lib/api.ts`)**：
   - 为 `api.tags` 补充 `update: (id: string, data: Partial<Tag>) => Promise<Tag>`；
   - 为 `api.tags` 补充 `delete: (id: string) => Promise<void>`（复用已修复的 HTTP 204 No Content 短路逻辑）。
2. **标签卡片悬浮操作交互 (`frontend/src/app/taxonomy/page.tsx`)**：
   - 标签徽章添加 Hover 状态，悬浮时平滑展示两个微型图标：
     - **✎ 编辑图标**：点击唤起轻量重命名弹窗；
     - **🗑 删除图标**：点击唤起二次确认提示。
3. **极简重命名弹窗**：
   - 聚焦单一诉求：仅修改标签名称（不引入复杂的色盘或描述维护，保持轻量高效）；
   - 输入新名称校验（必填、去空格），提交调用 `api.tags.update(id, { name })`，成功后无感刷新标签列表。
4. **确认后直接解绑删除策略**：
   - 点击删除时提示当前影响面：“确定要删除标签‘#xxx’吗？删除后将自动从其关联的 N 篇知识点中移除该标签”；
   - 用户确认后调用 `api.tags.delete(id)`，后端在数据库级联清理 `knowledge_tags` 中的关系，知识数据毫发无损，前端即时刷新。

### 2.2 非目标 (Non-Goals)
- 本阶段不实现复杂颜色调色板（统一使用标准轻量色调）；
- 本阶段不实现跨知识多选批量打标（保持在知识编辑页和标签中心单体操作）。

---

## 3. 关联 Capability Specs

- `openspec/specs/tag-system/spec.md`:
  - 增补：标签在管理界面上的悬浮重命名能力；
  - 增补：标签被引用时的直接解绑删除交互规则。

---

## 4. 风险与缓解 (Risks & Mitigations)

- **重名冲突**：若用户重命名的名称与已有标签重复，后端会返回 HTTP 400（“标签名称已存在”），前端应在弹窗内友好拦截并给出清晰提示。
- **引用解绑确认**：删除带引用的标签前必须明确告知“将从 N 篇知识中移除”，避免误删导致丢失标签维度的聚合检索。
