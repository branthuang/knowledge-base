## 1. 工程骨架与本地基础设施环境配置

- [x] 1.1 编写 `docker-compose.yml`，编排 PostgreSQL 16 (集成 pgvector 扩展) 与 Redis 7 容器服务及持久化卷
- [x] 1.2 创建 `backend/` 基础目录骨架与依赖声明文件（`pyproject.toml` / `requirements.txt`），包含 FastAPI、SQLAlchemy 2.0、asyncpg、pgvector、pydantic-settings、redis、pytest-asyncio 等
- [x] 1.3 创建 `frontend/` 基础目录骨架并初始化 package 配置，建立前后端清晰边界与根目录 `.gitignore`

## 2. 系统核心配置与数据库持久层底座

- [x] 2.1 实现后端系统全局配置模块 `backend/app/core/config.py`，支持环境变量及 `.env` 解析
- [x] 2.2 实现异步数据库引擎与会话工厂 `backend/app/db/session.py`，支持健康检查与连接池
- [x] 2.3 实现 Redis 连接池管理模块 `backend/app/core/redis.py`

## 3. 核心实体 ORM 数据模型与 Alembic 迁移

- [x] 3.1 基于 SQLAlchemy 2.0 实现核心实体 ORM：`Category`, `Tag`, `KnowledgeTag`, `KnowledgeItem`, `KnowledgeSource`, `SearchSession`, `EmbeddingChunk`, `Asset`
- [x] 3.2 配置 Alembic 异步迁移环境，编写初始化迁移脚本（包含启用 `pgvector` 扩展与建表语句）
- [x] 3.3 实现系统初始化数据种子逻辑，自动写入预置顶级分类“技术类”与“公司知识类”

## 4. 基础设施适配层（Provider Adapters）

- [ ] 4.1 定义与实现 LLM Provider 抽象基类及 OpenAI 兼容适配器 `OpenAICompatibleProvider`，支持连通性检测
- [ ] 4.2 定义与实现 Embedding Provider 抽象基类及 OpenAI 兼容适配器 `OpenAICompatibleEmbeddingProvider`
- [ ] 4.3 定义 Search Provider 协议接口与数据契约 `SearchCitation`, `SearchResult`

## 5. 基础设施健康检查与自动化测试验收

- [ ] 5.1 实现 FastAPI 应用入口 `backend/app/main.py` 与 `/api/health` 健康检查接口（检测 API、数据库与 Redis 状态）
- [ ] 5.2 编写针对配置加载、数据库模型映射、种子数据及 Provider 接口的自动化测试套件
- [ ] 5.3 运行全部测试与静态检查，验证验收标准并生成端到端环境验证记录
