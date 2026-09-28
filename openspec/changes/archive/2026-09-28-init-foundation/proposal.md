## Why

为知识库管理系统搭建工程脚手架、核心数据底座及外部服务适配层。
这是整个系统运转的前提，落实已裁决的技术栈（后端 FastAPI、前端 Next.js + BlockSuite、数据库 PostgreSQL + pgvector、异步队列 Redis），建立规范的数据模型与服务抽象，为后续所有业务能力提供坚实的运行底座。

## What Changes

1. **工程骨架与本地开发环境**：
   - 建立根目录模块化结构：`backend/`（FastAPI）、`frontend/`（Next.js + TypeScript）、`docker/` 与 `docker-compose.yml`（PostgreSQL 16 + pgvector, Redis 7）。
2. **核心数据模型与迁移（ORM & Migrations）**：
   - 使用 SQLAlchemy 2.0 (asyncpg) 实现核心实体数据模型：`categories`, `tags`, `knowledge_items`, `knowledge_sources`, `search_sessions`, `embeddings`, `assets`。
   - 配置 Alembic 异步迁移脚本。
   - 预置默认顶级分类数据种子（“技术类”、“公司知识类”）。
3. **基础设施适配器（Provider Adapters）**：
   - 封装统一的 LLM Provider（OpenAI-compatible，支持 API Key、Base URL 配置与连通性检测）。
   - 封装统一的 Embedding Provider 接口与维度校验。
   - 封装 Web Search Provider 基础协议接口。
   - 封装存储服务（本地磁盘/S3）基础抽象。
4. **自动化测试底座**：
   - 配置 pytest-asyncio、SQLAlchemy 内存/测试库连接池与基础连通性测试。

## Capabilities

### New Capabilities
- 无（系统级 11 个 Capabilities 已在 `openspec/specs/` 中初始化）。

### Modified Capabilities
- `system-settings`: 落实后端配置驱动与 Provider 基础接口。
- `category-management`: 落实数据表模型与“技术类”、“公司知识类”默认种子。
- `knowledge-management`: 落实核心实体字段模型与持久化基础。

## Impact

- 创建 `backend/` 服务目录与依赖定义。
- 创建 `frontend/` 基础目录骨架。
- 创建 `docker-compose.yml`，提供 PostgreSQL + pgvector 与 Redis 的一键启动能力。
- 确立后端统一代码分层规范（api, core, models, schemas, services, providers）。
