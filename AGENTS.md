# AI Development Rules & Project Governance

## 权限 (Permissions)
- AI 可以自主操作当前项目目录内所有文件。
- 项目目录内常规创建、修改、删除无需询问。
- 不允许操作项目目录之外的文件。
- 不允许读取用户 SSH、系统配置、其他项目配置。

## OpenSpec 规范
所有功能开发必须遵循严格的生命周期流程：
```
proposal
→ specs
→ design
→ tasks
→ apply
→ verify
→ archive
```
- **禁止绕过 OpenSpec 直接实现新需求**。

## 开发原则 (Development Principles)
- **不允许自行增加产品需求**。
- **不允许因为“体验更好”自行修改需求**。
- **需求不明确时记录 Open Question**，等待用户裁决。
- **优先使用成熟开源组件**。
- **避免重复造轮子**。
- **保持模块边界清晰**。
- **MVP 阶段避免过度设计**。

## Task 推进流程 (Task Workflow)
每完成一个 task，必须严格遵循闭环流程：
1. 完成代码
2. 执行对应测试
3. 执行 lint/typecheck
4. 验证 acceptance criteria
5. 更新 `tasks.md`
6. 再开始下一个 task

- **禁止一次性把所有 task 标记完成**。

## 验收标准 (Acceptance Criteria)
**功能完成 ≠ Task 完成**。必须同时满足：
- Spec Scenario 验证通过
- Acceptance Criteria 逐条满足
- 自动化测试执行通过
- 实际功能端到端验证通过
才允许标记完成。

## Git 规范 (Git Standards)
- 每完成一个独立功能形成一个清晰 commit。
- **严禁**：
  - `git push --force`
  - `git reset --hard`
  - 大范围删除代码
  （除非用户明确授权）。
