# 知识库管理系统 (Knowledge Base) 部署与运维维护手册

> **致后续维护 AI / 工程师**：  
> 本文档记录了本系统的生产容器架构、网络拓扑、持久化数据规范、更新发布流程以及常见故障排查手册。在对生产服务器执行任何操作前，**请务必通读本文档特别是“安全红线与端口避让原则”**。

---

## 1. 生产环境总览与拓扑架构

### 1.1 主机与访问信息
- **部署服务器**：`192.168.46.161` (OS: Linux x86_64, Docker: 24.0.6, Docker Compose: v2.21.0)
- **SSH 运维账号**：`phper@192.168.46.161`（已配置免密公钥认证）
- **远程工程根目录**：`/home/phper/wwwroot/knowledge-base`
- **前端 Web 访问地址**：[http://192.168.46.161:3010](http://192.168.46.161:3010)
- **后端 API 文档直连**：[http://192.168.46.161:8090/docs](http://192.168.46.161:8090/docs)
- **前端代理文档入口**：[http://192.168.46.161:3010/docs](http://192.168.46.161:3010/docs)

### 1.2 ⚠️ 关键红线：宿主机既有多系统端口避让
161 主机属于多项目共享服务器，**同时运行着多套关键业务系统**。操作时**严禁**修改或占用以下端口与容器：
| 既有系统 / 容器名 | 已占用端口 | 严禁行为 |
| :--- | :--- | :--- |
| **`laradock_nginx_1`** | `80`, `81`, `443` | 严禁占用 80/81/443 |
| **`laradock_workspace_1`** | `3000`, `3001`, `5173`, `8001`, `8080`, `2222` | **绝对不可使用 3000 端口** |
| **`work-ledger-web`** | `5174` | 严禁占用 5174 |
| **`work-ledger-server`** | `8088` | 严禁占用 8088 |
| **`mysql8_container` / `work-ledger-mysql`** | `3306`, `3307` | 严禁冲突 MySQL 端口 |
| **Redis 实例集群** | `6379`, `6479` ~ `6979` | 严禁占用 Redis 端口组 |

### 1.3 本项目端口与网络规范
- **宿主机分配端口**：
  - 前端 Web 端口：**`3010`**（映射至容器内 `3000`）
  - 后端 API 端口：**`8090`**（映射至容器内 `8000`）
- **独立网络**：系统运行在专属独立桥接网络 **`kb-network`** 下，前后端容器通过容器名互联，与宿主机上其他 Docker 网络完全隔离。

---

## 2. 系统容器架构与通信机制

```
  [客户端浏览器 / 用户终端]
           │
           ├───> http://192.168.46.161:3010 (访问页面 /api /docs)
           │          │
           │          ▼
           │   ┌──────────────────────────────────────────────┐
           │   │  kb-frontend 容器 (Next.js 14 Standalone)     │
           │   │  监听: 0.0.0.0:3000                          │
           │   │  SSR 与 页面渲染                             │
           │   │  /api/* 与 /docs 动态反向代理                 │
           │   └──────┬───────────────────────────────────────┘
           │          │  kb-network 内部直连
           │          │  (http://backend:8000)
           │          ▼
           │   ┌──────────────────────────────────────────────┐
           └───┼─>│  kb-backend 容器 (FastAPI / Python 3.11)     │
       直连API │  监听: 0.0.0.0:8000 (对外暴露 8090)          │
       (:8090) │  业务逻辑 / 向量检索 / 权限与分类             │
               └──────┬───────────────────────────────────────┘
                      │
                      ▼
               挂载宿主机卷:
               - ./data:/app/data (SQLite: knowledge_base.db)
               - ./storage:/app/storage (本地文件存储)
```

### 2.1 Next.js 独立运行与反向代理机制
- 前端使用 Next.js `output: 'standalone'` 极简镜像运行。
- 在构建时，Next.js 会把 `next.config.js` 中的 `rewrites` 规则固化。为确保容器内能够解析后端，`Dockerfile` 与 `docker-compose.yml` 必须传入构建参数：
  ```dockerfile
  ARG BACKEND_INTERNAL_URL=http://backend:8000
  ENV BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL}
  ```
- 客户端在浏览器中发起的所有 `/api/*` 请求会先发送到当前页面的同源前端端口 `3010`，由 Next.js 服务端内部转发给 `kb-backend`，**天然规避浏览器跨域 (CORS) 问题**。

---

## 3. 数据持久化与数据库规范

### 3.1 数据存储分布
- **数据库形态**：当前生产运行单体嵌入式 **SQLite 3**（开启 WAL 模式），零外部依赖，极低内存消耗。
- **宿主机路径**：`/home/phper/wwwroot/knowledge-base/data/knowledge_base.db`
- **容器挂载路径**：`/app/data/knowledge_base.db`
- **附件存储路径**：宿主机 `/home/phper/wwwroot/knowledge-base/storage` -> 容器内 `/app/storage`

### 3.2 核心数据表清单
| 数据表 | 作用说明 |
| :--- | :--- |
| `knowledge_items` | 知识点主表（标题、摘要、正文 Block 结构、状态、归档标识等） |
| `categories` | 知识分类层级树（技术类、公司知识类等） |
| `tags` | 标签字典表（支持颜色、分类聚合与悬浮编辑） |
| `knowledge_tags` | 知识点与标签的多对多绑定关系表 |
| `embedding_chunks` | 向量化切片表（包含内容分块与向量索引） |
| `knowledge_sources` | 导入源记录表 |
| `assets` | 静态上传资产元数据表 |
| `search_sessions` | 搜索历史与检索会话表 |

---

## 4. 日常运维命令速查 (Cheat Sheet)

### 4.1 容器状态与日志
```bash
# 进入远程项目目录
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && docker compose ps"

# 查看后端实时日志 (最近 100 行)
ssh phper@192.168.46.161 "docker logs -f --tail 100 kb-backend"

# 查看前端实时日志
ssh phper@192.168.46.161 "docker logs -f --tail 100 kb-frontend"

# 查看资源占用
ssh phper@192.168.46.161 "docker stats --no-stream kb-frontend kb-backend"
```

### 4.2 容器启停与重启
```bash
# 平滑重启所有服务
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && docker compose restart"

# 仅重启后端
ssh phper@192.168.46.161 "docker restart kb-backend"

# 仅重启前端
ssh phper@192.168.46.161 "docker restart kb-frontend"

# 停止整个服务（保留数据卷）
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && docker compose down"

# 启动并后台运行
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && docker compose up -d"
```

### 4.3 数据备份与恢复
#### 备份数据库
```bash
# 线上安全备份（建议在容器内或宿主机利用 sqlite3 备份命令规避锁）
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && \
  sqlite3 data/knowledge_base.db '.backup data/knowledge_base_backup_\$(date +%Y%m%d_%H%M%S).db'"
```

#### 从本地同步数据库至远程
```bash
rsync -avz ./data/knowledge_base.db phper@192.168.46.161:/home/phper/wwwroot/knowledge-base/data/
```

#### 检查数据库记录总数
```bash
ssh phper@192.168.46.161 "docker exec kb-backend sqlite3 /app/data/knowledge_base.db \"SELECT 'knowledge_items', count(*) FROM knowledge_items UNION ALL SELECT 'tags', count(*) FROM tags UNION ALL SELECT 'categories', count(*) FROM categories;\""
```

---

## 5. 持续交付与更新流程 (CI/CD / Release)

当本地代码有新功能或 Bugfix 时，后续 AI / 工程师应严格遵循以下发布规范：

### 步骤 1：本地构建与代码检查
```bash
# 1. 前端类型与构建校验
cd frontend && npm run build

# 2. 后端单元测试
PYTHONPATH=backend pytest backend/tests -q
```

### 步骤 2：代码增量同步到远程
使用 `rsync` 排除无关本地临时文件，推送代码至远程目录：
```bash
rsync -avz \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '.venv' \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  ./ phper@192.168.46.161:/home/phper/wwwroot/knowledge-base/
```

### 步骤 3：远程镜像构建与容器平滑重拉
```bash
# 若仅修改了前端：
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && docker compose up -d --build frontend"

# 若仅修改了后端：
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && docker compose up -d --build backend"

# 若前后端均有变动：
ssh phper@192.168.46.161 "cd /home/phper/wwwroot/knowledge-base && docker compose up -d --build"
```

### 步骤 4：自动化健康探测与功能回归
```bash
# 1. 验证后端健康状态
curl -s http://192.168.46.161:8090/api/health

# 2. 验证前端透传接口
curl -s http://192.168.46.161:3010/api/categories

# 3. 验证既有系统不受影响
curl -I -s http://192.168.46.161:5174/ | head -n 1
curl -I -s http://192.168.46.161:80/ | head -n 1
```

---

## 6. 常见故障排查手册 (Troubleshooting)

### 故障 1：访问前端接口报 `500 Internal Server Error` (ECONNREFUSED 127.0.0.1:8000)
- **根因分析**：Next.js 在构建阶段打包了默认的 `http://127.0.0.1:8000` 代理地址，导致容器内反向代理试图连接前端容器自身的 8000 端口而非后端容器。
- **解决办法**：
  检查 `frontend/Dockerfile` 中是否包含：
  ```dockerfile
  ARG BACKEND_INTERNAL_URL=http://backend:8000
  ENV BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL}
  ```
  检查 `docker-compose.yml` 中 `frontend.build.args` 是否包含 `BACKEND_INTERNAL_URL=http://backend:8000`。修复后重新执行 `docker compose up -d --build frontend`。

### 故障 2：后端容器一直处于 `unhealthy` 状态
- **根因分析**：后端容器在 10 秒启动期内健康探针 `curl -f http://localhost:8000/api/health` 失败。
- **排查步骤**：
  1. 查看后端日志：`docker logs kb-backend --tail 100`。
  2. 检查 SQLite 数据库文件权限是否可写：`ls -la /home/phper/wwwroot/knowledge-base/data/`。
  3. 进入容器手动执行探针：`docker exec kb-backend curl -i http://localhost:8000/api/health`。

### 故障 3：宿主机端口冲突报错 (`port is already allocated`)
- **排查步骤**：
  1. 查看是谁占用了端口：
     ```bash
     ssh phper@192.168.46.161 "netstat -tlpn | grep -E '3010|8090'"
     ```
  2. 严禁杀掉已有的系统进程！修改本项目 `docker-compose.yml` 或 `.env.production` 中的宿主机端口映射（例如换为 `3011` / `8091`）。

---

## 7. 仓库与代码版本控制
- **远程 GitHub 仓库**：`git@github.com:branthuang/knowledge-base.git`
- **主分支**：`master`
- 所有生产部署相关的配置变更（`Dockerfile`, `docker-compose.yml`, `DEPLOYMENT.md`）必须同步提交至 Git，严禁私自脱离版本控制。
