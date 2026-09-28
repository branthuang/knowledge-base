# knowledge-management Specification

## Overview
知识点管理是系统的核心资产容器。系统中的最小业务对象为“知识点（Knowledge Item）”，支持多状态流转、纯文本派生、来源追溯以及软硬删除生命周期管理。

## Requirements

### Requirement: 知识点核心模型与字段定义
系统必须支持结构化知识点数据模型，包含标识、标题、摘要、内容块 JSON、派生纯文本、主分类、多标签、来源信息、业务状态、版本号及审计时间。

#### Scenario: 知识点实体持久化
- **WHEN** 用户或系统创建一个新的知识点
- **THEN** 系统持久化存储以下核心属性：
  - `id`: 唯一标识符
  - `title`: 标题（必填）
  - `summary`: 摘要（选填，支持手工或 AI 生成）
  - `blocks_json`: 结构化内容块 JSON（必填）
  - `plain_text`: 派生纯文本（由 blocks 自动抽取）
  - `category_id`: 所属主分类 ID
  - `source_type`: 来源类型（`manual` / `ai_search` / `import` / `web_clip`）
  - `status`: 状态（`draft` / `published` / `archived` / `trashed`）
  - `favorite`: 收藏标记（布尔值）
  - `index_status`: 索引状态（`pending` / `indexed` / `failed`）
  - `created_at` 与 `updated_at`: 时间戳

### Requirement: 知识草稿与自动保存
在知识新建或编辑过程中，系统必须支持自动保存草稿机制，防止意外关闭或刷新导致内容丢失。

#### Scenario: 编辑过程中的自动暂存
- **WHEN** 用户在知识编辑器中输入或修改内容超过设定防抖间隔（如 1~2 秒）
- **THEN** 系统自动将当前 blocks 数据和标题暂存为 `draft` 状态，并向用户提示已自动保存。

### Requirement: 知识点生命周期与状态流转
系统必须支持知识点在草稿（draft）、已发布（published）、归档（archived）和回收站（trashed）状态之间的显式切换。

#### Scenario: 知识发布
- **WHEN** 用户点击“保存并发布”按钮
- **THEN** 知识状态更新为 `published`，触发异步全文与向量索引生成任务。

#### Scenario: 移入回收站与软删除
- **WHEN** 用户在知识详情或列表中触发“删除”操作
- **THEN** 知识状态变更为 `trashed`，进入回收站列表，同时将其从搜索索引中标记为不可检索。

#### Scenario: 回收站恢复
- **WHEN** 用户在回收站中选择某篇知识并点击“恢复”
- **THEN** 知识状态恢复为移入回收站前的状态（如 `published`），并重新启用搜索索引。

#### Scenario: 彻底删除
- **WHEN** 用户在回收站中确认“彻底删除”某篇知识
- **THEN** 知识记录及关联的索引数据被物理删除，关联的静态附件资源进入延迟清理队列。

### Requirement: 详情阅读与编辑模式分离
知识详情页面必须严格区分阅读模式与编辑模式，减少日常查看时的误触修改风险。

#### Scenario: 默认进入阅读模式
- **WHEN** 用户从列表或搜索结果点击某篇知识
- **THEN** 系统以只读排版渲染内容块，并展示分类、标签、来源追溯信息和元数据；提供明确的“编辑”操作按钮切换至编辑模式。

### Requirement: 来源追溯与关联
对于通过 AI 搜索收藏入库的知识，系统必须完整记录并展示其原始追溯信息。

#### Scenario: 查看 AI 搜索来源
- **WHEN** 用户查看 `source_type` 为 `ai_search` 的知识详情
- **THEN** 详情页清晰展示关联的原始搜索问题（Query）、使用的模型/提供商、收藏时间以及公网引用链接（URL与标题），点击引用链接可外部跳转。
