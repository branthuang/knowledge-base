## Context

用户已明确系统技术选型与范围边界：
- 后端采用 **FastAPI (Python 3.11+)**；
- 前端采用 **Next.js / React (TypeScript) + BlockSuite**；
- 数据存储采用 **PostgreSQL 16 + pgvector** 扩展；
- 异步队列引入 **Redis**；
- MVP 范围限定基础块，Mermaid / Canvas 画板延至 P1。

本阶段作为系统首个交付里程碑，专注于确立工程规范、定义数据库 Schema、构建 Provider 抽象以及打通基础设施测试闭环。

## Goals / Non-Goals

**Goals:**
- 提供标准化、容器化的本地开发环境编排（`docker-compose.yml` 运行 PostgreSQL + pgvector 与 Redis）。
- 搭建 FastAPI 规范化工程分层结构（`core/config`, `db/session`, `models/`, `schemas/`, `providers/`, `api/`）。
- 建立与 PRD 严格对齐的核心数据表模型（`categories`, `tags`, `knowledge_items`, `knowledge_sources`, `search_sessions`, `embeddings`, `assets`）。
- 配置 Alembic 数据库迁移支持，并实现“技术类”、“公司知识类”系统预置分类的自动种子加载。
- 封装统一的 OpenAI 兼容大模型客户端、Embedding 客户端及 Search Provider 抽象。
- 建立自动化测试套件（pytest + pytest-asyncio），确保配置、数据库连通性、模型映射及 Provider 均通过测试。

**Non-Goals:**
- 本阶段不实现前端复杂交互界面与 BlockSuite 编辑器集成（留待 Phase 2）。
- 本阶段不实现具体的全文与向量混合搜索逻辑（留待 Phase 3）。
- 本阶段不实现端到端 AI 搜索会话流与收藏沉淀前端交互（留待 Phase 4）。

## Decisions

1. **项目工程结构**：
   - 采用前后端同仓（Monorepo 结构）：
     - `backend/`: FastAPI 应用、Alembic 迁移、依赖文件与测试。
     - `frontend/`: Next.js 前端应用脚手架与基础配置。
     - `docker-compose.yml`: 本地基础设施服务编排。
2. **数据库与 ORM 技术栈**：
   - 使用 **SQLAlchemy 2.0 (DeclarativeBase, Mapped, mapped_column)** 配合 **asyncpg** 驱动，全面采用强类型与异步 I/O。
   - 使用 **pgvector-python** 支持向量列存储与余弦距离/点积计算索引。
   - 使用 **Alembic** 管理数据库 Schema 版本迭代。
3. **配置管理**：
   - 使用 **Pydantic Settings (`pydantic-settings`)**，通过环境变量与 `.env` 文件统一管理数据库连接串、Redis 地址、LLM API Key 及存储路径。
4. **异步队列客户端架构**：
   - 预置 Redis 连接池与轻量异步任务客户端连接接口，为后续向量化和抓取任务做好连接准备。
5. **Provider 适配层设计**：
   - `BaseLLMProvider` 抽象基类，实现 `OpenAICompatibleProvider`，统一封装聊天完成与连通性测试。
   - `BaseEmbeddingProvider` 抽象基类，实现 `OpenAICompatibleEmbeddingProvider`，统一封装文本向量化接口。
   - `BaseSearchProvider` 抽象基类，定义外部公网搜索标准入参及返回契约。

## Risks / Trade-offs

- **风险 1：pgvector 扩展环境依赖**
  - *缓解措施*：在 `docker-compose.yml` 中选用官方支持 pgvector 的镜像（如 `pgvector/pgvector:pg16`），在 Alembic 初始化迁移脚本中加入 `CREATE EXTENSION IF NOT EXISTS vector;` 确保幂等安全。
- **风险 2：异步数据库测试环境**
  - *缓解措施*：测试环境配置 SQLite 内存库（对基础字段与逻辑测试）或针对 Docker PostgreSQL 容器运行集成测试，隔离测试数据。
