# Technical Design: 知识标签悬浮快捷重命名与解绑删除能力

## 1. 交互与状态流转设计

```
                      /taxonomy 标签管理面板
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   标签资产库 (共 N 个标签)                                   │
│                                                             │
│   ┌──────────────────────────────────────────────┐          │
│   │ #OpenResty (3)   [✎ 编辑] [🗑 删除]          │ ◄── Hover 呈现
│   └──────┬──────────────────┬────────────────────┘          │
│          │ 点击编辑          │ 点击删除                      │
│          ▼                  ▼                               │
│   ┌───────────────┐  ┌────────────────────────────────────┐ │
│   │ 轻量重命名弹窗│  │ 确认解绑弹窗                       │ │
│   │ [新标签名称 ] │  │ "将从关联的 3 篇知识中解除该标签"  │ │
│   │ [取消] [保存] │  │ [取消] [确认删除]                  │ │
│   └──────┬────────┘  └──────┬─────────────────────────────┘ │
│          │ 提交             │ 确认                          │
│          ▼                  ▼                               │
│      PUT /api/tags/{id}  DELETE /api/tags/{id}              │
│          │                  │                               │
│          └────────┬─────────┘                               │
│                   ▼                                         │
│            无感重新拉取并刷新                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 核心改动模块详细设计

### 2.1 API 客户端补齐 (`frontend/src/lib/api.ts`)
在 `api.tags` 命名空间下补全缺失的两个方法：
```ts
tags: {
  list: () => request<Tag[]>('/api/tags'),
  create: (data: Partial<Tag>) =>
    request<Tag>('/api/tags', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: string, data: Partial<Tag>) =>
    request<Tag>(`/api/tags/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  delete: (id: string) =>
    request<void>(`/api/tags/${id}`, {
      method: 'DELETE',
    }),
  merge: (source_tag_id: string, target_tag_id: string) =>
    request<{ status: string; message: string }>('/api/tags/merge', {
      method: 'POST',
      body: JSON.stringify({ source_tag_id, target_tag_id }),
    }),
}
```

### 2.2 标签管理页面交互重构 (`frontend/src/app/taxonomy/page.tsx`)
1. **标签徽章添加悬浮操作栏**：
   - 默认隐藏操作图标（`opacity-0 group-hover:opacity-100` 或 `hidden group-hover:flex`）；
   - 悬浮在徽章上时平滑浮现：
     - 编辑按钮（`Edit2` / `Pencil` 图标），点击阻止事件冒泡并呼出重命名弹窗；
     - 删除按钮（`Trash2` 图标），点击阻止事件冒泡并触发解绑删除流程。
2. **轻量重命名弹窗 (`TagRenameModal`)**：
   - 表单状态：`tagToRename: Tag | null`, `renameInputValue: string`, `renameError: string | null`；
   - 提交验证：非空校验、首尾空格清理；
   - 异常处理：若后端返回“标签名称已存在”，在弹窗内直接显示错误警示，不关闭弹窗。
3. **安全解绑删除处理 (`handleDeleteTag`)**：
   - 计算提示信息：
     - 若 `tag.knowledge_count > 0`：`确定要删除标签“#${tag.name}”吗？删除后将自动从其关联的 ${tag.knowledge_count} 篇知识点中移除该标签。`
     - 若 `tag.knowledge_count === 0`：`确定要删除标签“#${tag.name}”吗？`
   - 用户确认后调用 `api.tags.delete(tag.id)`，执行完成后无感重新调用 `loadData()`。
