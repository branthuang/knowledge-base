"""
Import Feishu wiki documentation into knowledge base system.
Converts content to structured BlockItem tree, tags, sources and builds vector index.
"""

import asyncio
import os
import sys

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import AsyncSessionLocal
from app.services.category_service import list_categories, create_category
from app.services.tag_service import list_tags, create_tag
from app.services.knowledge_service import create_knowledge
from app.services.index_service import IndexService
from app.services.block_parser import markdown_to_blocks
from app.schemas.knowledge import KnowledgeCreate, SourceInfoCreate
from app.schemas.category import CategoryCreate
from app.schemas.tag import TagCreate

DOCUMENT_MARKDOWN = """# LF 电商独立站多平台架构与集群基础设施全景技术指南

本文档全面梳理 LF 公司旗下多电商平台矩阵（Wshop、Xshop、Zshop、Flyshopon）、集群基础设施拓扑、Cloudflare 边缘多账号网络规划、ESA 与 OpenResty 流量网关调度机制、一页商店体系及竞品技术方案。

---

## 1. 平台矩阵定位与特性概览

LF 业务生态内包含以下四大核心电商独立站平台：

- **Wshop 平台**：最早期主集群核心平台，承载 `wshop`、`mshop`、`shoprise`、`shoprose` 等多个主力平台域名。
- **Xshop 平台**：专用于 `Lumora` 主题的业务平台。Xshop 没有独立的控制中心，与 Wshop 共用同一套管理后台。
- **Zshop 平台**：专用于投放一页商店（但反过来一页商店能力可泛化用于所有平台）。理论上 Zshop 是独立部署的私有化环境，所有计算与存储资源完全独立，部署在阿里云集群，拥有独立的控制中心。
- **Flyshopon 平台**：部署于「新集群 2026」的私有化独立部署平台，面向特定新业务线与多租户特征隔离。

---

## 2. 集群拓扑与环境分布

系统后台基础设施按物理与逻辑隔离划分为三大集群：

### 2.1 主集群 (Main Cluster)
- **承载平台**：`wshop`、`mshop`、`shoprize`、`shoproze`、`xshop` 等多个平台。
- **基础设施**：主要部署于 AWS 体系，属于历史核心公共集群。

### 2.2 Zshop 阿里云集群 (Aliyun Zshop Cluster)
- **承载平台**：仅部署 `zshop`。
- **核心特点**：拥有独立控制中心与独立的计算资源。

### 2.3 新集群 2026 (New Cluster 2026)
- **承载平台**：仅部署 `flyshopon`。
- **核心特点**：阿里云集群私有化独立部署平台，控制中心与 Wshop 共用；存储资源通过 OSS 镜像回源映射到 Wshop S3 存储桶。

---

## 3. 多平台多维度核心技术架构对比

| 评估维度 | 新集群 2026 (flyshopon) | Wshop 平台 | Xshop 平台 | Zshop 平台 |
| :--- | :--- | :--- | :--- | :--- |
| **平台定位** | 私有化独立集群 | 核心主平台 (历史主平台) | Lumora 主题专属平台 | 一页商店独立私有化平台 |
| **部署方式** | 私有化独立部署 | 公共平台部署 | 依赖 Wshop 部署 | 私有化独立部署 |
| **云基础设施** | 阿里云 (Aliyun) | 亚马逊云 (AWS) | 亚马逊云 (AWS) | 阿里云 (Aliyun) |
| **控制中心** | 与 Wshop 共用 | 与 Xshop、新集群2026 共用 | 与 Wshop 共用 | 独立控制中心 |
| **存储资源策略** | 业务写入仍使用 Wshop S3 桶，CDN 优先从 OSS 读取；未命中时 OSS 自动镜像回源 S3。<br>存储桶：`esashop-{}`、`esashop-s3`、`esashop-assets`、`esashop-extensions`、`esashop-theme-assets-v2` | 独立 AWS S3 存储桶 | 完全复用 Wshop 存储资源 | 独立 OSS 存储桶，读写均直接访问该桶；图片文件未命中时历史曾回源 Wshop，目前正推进彻底切断跨集群回源。<br>存储桶：`wshop4`、`wshop4-s3`、`wshop4-extensions`、`wshop4-theme-assets-v2` |
| **平台域名** | `flyshopon` | `wshop`、`mshop`、`shoprise`、`shoprose` 等 | `xshop` | `wshop4-theme-assets-v2` 等 |
| **一页商店支持** | 支持 | 支持 | 支持 | 核心原生业务支撑 |
| **前端主题支持** | 与 Wshop 保持一致 | 支持主题 V1 / V2 | 专有 Lumora 主题 | 主要面向一页商店 Spa |

---

## 4. Cloudflare (CF) 多账号规划与边缘网络策略

Cloudflare 作为系统第一道全球 CDN 加速与 DDoS 防护屏障，规划了 3 个独立账号实现业务解耦与流量特征隔离：

- **账号 1 (Zone: `spashoptech.com`)**：当前作为**一页商店主账号**使用。店铺域名可直接接入，无需客户额外修改 DNS 解析。
- **账号 2 (Zone: `wshopnow.com`)**：历史上用于兼容店铺域名接入一页商店，目前主要用于维护已完成解析迁移的历史存量店铺。
- **账号 3 (Zone: `zenshopon.com`)**：针对特定静态资源路径实施精细化规则：
  - `/cdn/shop/theme1/assets/`：禁用 Worker 路由，使用 Snippets 片段代码进行 URI 重写和回源 S3。
  - `/cdn/shop/theme2/assets/`：禁用 Worker 路由，使用 Snippets 片段代码进行 URI 重写和回源 S3。
  - `/cdn/platform/extensions/`：禁用 Worker 路由，使用 Snippets 片段代码进行 URI 重写和回源 S3。

### 核心网络概念规范
- **SSL for SaaS (自定义主机名 Custom Hostname)**：支持客户将自有域名通过 CNAME 接入平台，Cloudflare 自动完成证书免费签发、自动续期并路由至自定义回退源 (Custom Origin Server)。
- **Cloudflare Snippets**：执行在边缘节点的高性能微型 JavaScript 片段，用于实现轻量级 URI 重写与动态指定存储源站。
- **AWS Abuse 风险防控**：通过多租户特征隔离与出口代理，避免因单个店铺异常引起整体云资源账号受限。

---

## 5. 流量网关调度：ESA 与 OpenResty

### 5.1 边缘安全加速 (ESA - Edge Security Acceleration)
ESA 是内部用于新集群（如阿里云主集群）的域名绑定与流量调度服务，核心能力包括：
- **域名解析与回源调度**：店铺域名通过 CNAME 指向 ESA 入口（`o.flyshopon.com` 或 `c.flyshopon.com`），ESA 在上层灵活调度到 OpenResty 或 Ingress，支持无感动态热切。
- **多租户与多集群隔离**：作为阿里云主集群专属入口，新集群店铺配置添加 `use_tmp_esa` 标签。
- **资源路径映射**：如 `/cdn/shop/files/` 自动重定向映射到专属 OSS 存储桶。

### 5.2 核心入口网关 OpenResty
OpenResty 是 Wshop 及阿里云集群的关键流量网关，具备店铺与租户精准识别能力：
- **架构部署**：阿里云集群的 OpenResty 部署于 `aliyun-us-cluster`，上游挂接负载均衡 IP `47.252.36.130`，承接 `*.o` 托管域名以及主集群 `zhyxgate` 跨集群专线流量。
- **店铺与状态缓存**：使用 Redis 缓存存储店铺域名、版本与多租户信息；目前系统已启动向 `Valkey` 升级的双写迁移方案。
- **业务路由分发**：所有店铺接口路由 `/api/` 均统一经由店铺 OpenResty 入口处理并回源后端服务。

---

## 6. 一页商店、渲染水合与日志监控体系

### 6.1 一页商店与主题单页机制
- **Spa 应用**：支持轻量单页极速转化。
- **主题单页 (多模板详情页)**：中台在添加主题单页时，预先调用控制中心接口完成静态资源上传；单页静态资源采用相对路径组织规范：
  `/cdn/page/{hash1}/{hash2}/{资源文件名}`

### 6.2 前端渲染与水合 (Hydration)
- **SSR (服务端渲染)**：Node/Nuxt 服务器直接返回构建好的纯 HTML 结构，客户端首屏即时可见。
- **水合过程 (Hydration)**：浏览器加载渲染 HTML 后，Vue/React 前端运行时加载 JS 代码接管页面，激活事件监听、组件状态与动态动画。

### 6.3 阿里云日志服务 (SLS) 规划
| 日志业务领域 | SLS Project | Region 地域 | Logstore |
| :--- | :--- | :--- | :--- |
| **Wshop 主集群** | `wshop-sz` | 华南1 (深圳) `cn-shenzhen` | 系统业务日志 |
| **一页商店 / 翻译 / 转化助手** | `aliyun-us-east` | 美国 (弗吉尼亚) `us-east-1` | `k8s-log-cf03fa158280a4b3f954b380e0ec858a1` |

---

## 7. 行业竞品模式调研与打法借鉴

- **LT 竞品模式**：以 Shopify 体系为主、采用极速单页铺货打法的一类竞争对手（如 `www.alaskatag.com`、`eurshap.com` 等）。其核心模式是通过 AI 自动化工具（**D2C**）生成纯静态页面 ZIP 包，直接上品到 Shopify 迅速抢占市场，流程极度标准化低成本。
- **BYD 竞品模式**：采用漏斗单页（Funnel）引导模式（如 `m.acssart.com/funnel/...`）。内部目前正在推进将 BYD 优秀的结账页装修逻辑与自定义模块导入脚本无缝适配进一页商店。
"""


async def main():
    print(">>> Starting standard Feishu document import...")
    async with AsyncSessionLocal() as session:
        # 1. Categories
        categories = await list_categories(session)
        target_category = next((c for c in categories if c.name == "技术类"), None)
        if not target_category:
            target_category = await create_category(
                session,
                CategoryCreate(
                    name="技术类",
                    description="系统架构、基础设施与工程开发技术指南",
                    icon="code",
                    color="#2563EB",
                ),
            )
            print(f"Created category: {target_category.name} ({target_category.id})")
        else:
            print(f"Using category: {target_category.name} ({target_category.id})")

        # 2. Tags
        needed_tags = [
            "平台架构",
            "集群",
            "Cloudflare",
            "OpenResty",
            "ESA",
            "一页商店",
            "跨境电商",
        ]
        all_tags = await list_tags(session)
        existing_tags_map = {t.name: t.id for t in all_tags}

        tag_ids = []
        for tname in needed_tags:
            if tname in existing_tags_map:
                tag_ids.append(existing_tags_map[tname])
            else:
                new_t = await create_tag(session, TagCreate(name=tname, color="#3B82F6"))
                tag_ids.append(new_t.id)
                print(f"Created tag: #{tname}")

        # 3. Parse Markdown into structured BlockItem tree
        blocks = markdown_to_blocks(DOCUMENT_MARKDOWN)
        print(f"Parsed {len(blocks)} structured blocks from Markdown.")

        # 4. Construct KnowledgeCreate
        k_data = KnowledgeCreate(
            title="LF 电商独立站多平台架构与集群基础设施全景技术指南",
            summary="详尽梳理 LF 公司旗下 Wshop、Xshop、Zshop、Flyshopon 多平台体系与集群架构（主集群/阿里云/新集群2026），涵盖 Cloudflare 多账号网络规划、SSL for SaaS、ESA 与 OpenResty 流量网关调度、一页商店机制及竞品（LT/BYD）全景技术指南。",
            blocks_json=[b.model_dump() for b in blocks],
            category_id=target_category.id,
            tag_ids=tag_ids,
            source_type="url",
            status="published",
            favorite=True,
            sources=[
                SourceInfoCreate(
                    type="url",
                    url="https://liaofeng.feishu.cn/wiki/EJ7xwuSLWiZ6XBkuH9rcaCKNn8g",
                    title="飞书知识库 - 平台与集群基础设施",
                    metadata_json={
                        "doc_token": "EJ7xwuSLWiZ6XBkuH9rcaCKNn8g",
                        "origin": "feishu_wiki",
                        "imported_by": "knowledge_inflow_pipeline",
                    },
                )
            ],
        )

        # 5. Create knowledge item
        item = await create_knowledge(session, k_data)
        print(f"Created knowledge item in DB: id={item.id}, title={item.title}")

        # 6. Index item into vector embedding chunks
        indexer = IndexService()
        chunk_count = await indexer.index_knowledge_item(session, item)
        print(f"Successfully generated {chunk_count} vector chunks and indexed knowledge item.")

        print(">>> Document successfully imported and indexed into knowledge base!")
        print(f"Knowledge ID: {item.id}")


if __name__ == "__main__":
    asyncio.run(main())
