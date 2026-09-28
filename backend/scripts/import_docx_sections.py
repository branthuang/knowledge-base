"""
Import sections from docs/名词解释.docx into the knowledge base.
Rules:
- Every Level-1 heading is an individual knowledge item.
- Under the Level-1 heading "名词", each Level-2 heading is an individual knowledge item.
Converts content to structured BlockItem trees, tags, sources, and builds vector embeddings.
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

SECTIONS_DATA = [
    # 1. 平台 (Level-1)
    {
        "title": "平台",
        "category": "技术类",
        "tags": ["平台架构", "跨境电商", "Wshop", "Xshop", "Zshop", "Flyshopon"],
        "summary": "LF 公司旗下核心电商独立站平台矩阵（Wshop、Xshop、Zshop、Flyshopon）定位、控制中心与主题归属说明。",
        "favorite": False,
        "markdown": """# 平台

LF 公司电商独立站业务生态包含以下核心平台：

## wshop平台
最早期主集群中平台。主集群包括 wshop，mshop，shoprise，shoprose 等多个平台域名。

## Xshop 平台
Lumora 主题当前只用于 xshop。xshop 没有独立控制中心，和 wshop 是同一个。

## Zshop 平台
zshop 只投放一页商店，但反过来一页商店是可以用于所有平台。理论上，zshop 是一个独立部署的私有化环境，所有资源都是独立的。zshop 使用的是阿里云集群。zshop 有独立的控制中心。

## Flyshopon 平台
位于新集群 2026。私有化独立部署平台，资源访问镜像到 wshop 平台存储桶。
""",
    },

    # 2. 集群 (Level-1)
    {
        "title": "集群",
        "category": "技术类",
        "tags": ["集群", "基础设施", "AWS", "阿里云", "平台架构"],
        "summary": "系统基础设施三大集群拓扑架构（主集群、Zshop 阿里云集群、新集群 2026）以及各平台在云厂商、控制中心、存储资源、一页商店支持等维度的全景对比。",
        "favorite": True,
        "markdown": """# 集群

系统基础设施划分为三大核心集群：

## 1. 主集群
包括：wshop, mshop, shoprize, shoproze, xshop 等多个平台。主要部署于 AWS 体系。

## 2. zshop阿里云集群
只有平台 zshop。独立控制中心。

## 3. 新集群2026
只有平台 flyshopon。私有化独立部署平台。资源访问镜像到 wshop 平台存储桶。阿里云集群。没有独立控制中心，和 wshop 是同一个。

---

## 多集群多平台技术维度对比

| 评估维度 | 新集群2026/flyshopon | Wshop 平台 | Xshop 平台 | Zshop 平台 |
| :--- | :--- | :--- | :--- | :--- |
| **平台定位** | 私有化集群 | 主平台 (历史主平台) | Lumora 主题平台 | 一页商店独立平台 |
| **部署方式** | 私有化独立部署 | 公共平台 | 依赖 Wshop | 私有化独立部署 |
| **云厂商** | 阿里云 (Aliyun) | AWS (亚马逊云) | AWS (亚马逊云) | 阿里云 (Aliyun) |
| **控制中心** | 与 Wshop 共用 | 与 Xshop、新集群2026共用 | 与 Wshop 共用 | 独立控制中心 |
| **存储资源** | 业务写入仍使用 wshop s3 存储桶，CDN 资源优先从 OSS 存储桶读取。OSS 已开启镜像回源，资源未命中时会自动回源至对应的 S3 存储桶获取。<br>存储桶：`esashop-{}`、`esashop-s3`、`esashop-assets`、`esashop-extensions`、`esashop-theme-assets-v2` | 独立 AWS S3 | 复用 Wshop 资源 | 存储使用独立 OSS 存储桶，读写均直接访问该存储桶；图片文件存储桶有特殊处理：读取未命中时自动回源至 Wshop 存储桶。要推进处理掉，不能回源。(一页商店有跨集群问题)<br>存储桶：`wshop4`、`wshop4-s3`、`wshop4-extensions`、`wshop4-theme-assets-v2` |
| **平台域名** | `flyshopon` | `wshop`、`mshop`、`shoprise`、`shoprose` 等 | `xshop` | `wshop4-theme-assets-v2` 等 |
| **一页商店支持** | 支持 | 支持 | 支持 | 核心业务，肯定支持 |
| **前端主题支持** | 与 Wshop 保持一致 | 主题 V1/V2 | 专有 Lumora 主题 | 主要使用一页商店 |
""",
    },

    # 3. CF账号 (Level-1)
    {
        "title": "CF账号",
        "category": "技术类",
        "tags": ["Cloudflare", "CF账号", "CDN", "Snippets"],
        "summary": "Cloudflare (CF) 三大独立账号规划、Zone 分布以及针对静态资源的 Snippets 片段重写与回源策略。",
        "favorite": False,
        "markdown": """# CF账号

Cloudflare 共使用 3 个账号实现业务解耦与流量特征隔离：

- **账号 1**：Zone 为 `spashoptech.com`，当前作为一页商店主账号使用，店铺域名可直接接入，无需额外修改解析。
- **账号 2**：Zone 为 `wshopnow.com`，历史上用于兼容店铺域名接入一页商店，目前仅用于兼容已完成解析迁移的存量店铺。
- **账号 3**：Zone 为 `zenshopon.com`。针对特定静态资源路径实施精细化重写规则：
  - `/cdn/shop/theme1/assets/`：禁用 worker 路由，使用 snippets 片段代码进行 URI 重写和回源。
  - `/cdn/shop/theme2/assets/`：禁用 worker 路由，使用 snippets 片段代码进行 URI 重写和回源。
  - `/cdn/platform/extensions/`：禁用 worker 路由，使用 snippets 片段代码进行 URI 重写和回源。
""",
    },

    # 4. CF(cloud flare) (Level-1)
    {
        "title": "CF(cloud flare)",
        "category": "技术类",
        "tags": ["Cloudflare", "SSL for SaaS", "Custom Hostname", "CNAME", "Snippets", "Zone"],
        "summary": "Cloudflare 核心功能与边缘网络概念详解，包含 SSL for SaaS、自定义主机名、CNAME、回退源、Snippets 及 Zone。",
        "favorite": False,
        "markdown": """# CF(cloud flare)

Cloudflare 边缘加速与网络管理核心机制：

## SSL for SaaS
SSL for SaaS（SaaS 版 SSL）是 CDN、云厂商或 SaaS 平台提供的一种能力，用于让 SaaS 平台的客户使用自己的域名，同时自动获得 HTTPS 证书。
domain 不需要是该 zone 的子域名，只要在 zone 下创建一条 `custom_hostname` 记录，CF 就会给这个外部域名签发证书并接受流量、转发到 `custom_origin_server`。

## 自定义主机名 (Custom Hostname)
允许用户使用自己的域名，通过平台方提供的 SSL 证书和 CDN 服务进行访问。
> Custom Hostname = 用户自己的域名（CNAME 到你的平台），平台代为管理 SSL 证书和访问路由。

## CNAME
> 将一个域名指向另一个域名。

CNAME 本身不直接指向 IP，而是指向另一个域名，由 DNS 再继续解析目标域名对应的 IP。

## 回退源 (Fallback Origin / Custom Origin Server)
当外部自定义主机名将流量路由到 Cloudflare 时，Cloudflare 将请求代理转发到的后端服务源站地址。

## snippets
短而强大的 JavaScript 片段。目前在系统中有用于实现静态资源路由重写，并指定访问存储 S3 地址。

## zone
> 一个域名及其所有 DNS 配置的管理单元。
""",
    },

    # 5. CLOUD FRONT (Level-1)
    {
        "title": "CLOUD FRONT",
        "category": "技术类",
        "tags": ["CloudFront", "AWS", "CDN"],
        "summary": "AWS CloudFront 全球内容分发网络（CDN）在系统多平台静态资源分发与边缘访问中的定位与能力。",
        "favorite": False,
        "markdown": """# CLOUD FRONT

AWS CloudFront 是亚马逊云 (AWS) 提供的全球分布式内容分发网络 (CDN) 服务。

在系统架构中，CloudFront 承担以下核心职责：
- **静态资源高速分发**：为 Wshop、Xshop 等托管在 AWS S3 的前端资产、图片及静态单页提供低延迟全球边缘缓存加速。
- **与网关策略协同**：配合平台域名绑定策略与入口网关，进行动静态资源流量分流与就近访问优化。
""",
    },

    # 6. 域名绑定策略 (Level-1)
    {
        "title": "域名绑定策略",
        "category": "技术类",
        "tags": ["域名绑定", "网关", "CDN", "流量路由"],
        "summary": "店铺域名接入与流量调度策略，支持 Gateway（网关直接接入）与 CDN 边缘分发两种模式。",
        "favorite": False,
        "markdown": """# 域名绑定策略

平台店铺域名接入调度策略主要分为两类：

> Gateway or CDN

- **Gateway 模式**：域名解析直接指向入口网关（如 OpenResty 或 Ingress），适用于需要精细化租户识别、动态鉴权或直接回源的业务场景。
- **CDN 模式**：域名通过 CNAME 接入 Cloudflare 或 ESA 等边缘网络，由 CDN 进行边缘缓存加速、SSL 证书自动签发后再回源到集群网关。
""",
    },

    # 7. SLS日志 (Level-1)
    {
        "title": "SLS日志",
        "category": "技术类",
        "tags": ["SLS", "日志服务", "监控运维", "阿里云"],
        "summary": "阿里云日志服务 (SLS) 在各集群环境中的 Project 与 Region 地域规划分布。",
        "favorite": False,
        "markdown": """# SLS日志

系统业务日志与容器日志接入阿里云日志服务 (SLS) 的规划分布如下：

| 日志业务领域 | SLS Project | Region 地域 | Logstore / 详情 |
| :--- | :--- | :--- | :--- |
| **wshop 主集群** | `wshop-sz` | 华南1（深圳）`cn-shenzhen` | 系统业务日志 |
| **一页商店 / 翻译 / 转化助手** | `aliyun-us-east` | 美国（弗吉尼亚）`us-east-1` | `k8s-log-cf03fa158280a4b3f954b380e0ec858a1` |
""",
    },

    # 8. 一页商店 (Level-1)
    {
        "title": "一页商店",
        "category": "技术类",
        "tags": ["一页商店", "Spa", "电商应用"],
        "summary": "面向快速出单与极速转化的 Spa 单页电商应用形态及多平台支撑说明。",
        "favorite": False,
        "markdown": """# 一页商店

一页商店是系统面向高转化率与单品爆款打造的 **Spa 单页电商应用**。

- **核心定位**：极简购买链路，单页面内完成商品展示、变体选择与即时结账转化。
- **跨平台支持**：虽然 Zshop 平台专注于投放一页商店，但一页商店能力具备通用性，可泛化应用于所有电商平台（Wshop、Xshop、Zshop、Flyshopon）。
- **运行环境**：以 Zshop 阿里云集群作为其独立部署的私有化核心承载环境。
""",
    },

    # 9. 主题单页 (Level-1)
    {
        "title": "主题单页",
        "category": "技术类",
        "tags": ["主题单页", "前端", "资源管理"],
        "summary": "商品详情页多模板机制及静态资源预上传、相对路径规范说明。",
        "favorite": False,
        "markdown": """# 主题单页

主题单页支持商品详情页多模板自由组合与渲染：

- **资源上传机制**：中台在添加主题单页时，会预先调用控制中心接口完成静态资源上传。待资源完全上传成功后，才会进行主题单页的正式创建与关联。
- **静态资源路径规范**：主题单页资源采用统一的相对路径规范组织：
  `/cdn/page/{hash1}/{hash2}/{资源文件名}`
""",
    },

    # 10. 联邦管理 (Level-1)
    {
        "title": "联邦管理",
        "category": "技术类",
        "tags": ["联邦管理", "集群管理", "多租户"],
        "summary": "多独立集群与平台通过协同规则实现统筹管理的治理架构。",
        "favorite": False,
        "markdown": """# 联邦管理

> 多个独立集群或平台，通过规则进行协同管理的模式。

在多集群（主集群、Zshop 阿里云集群、新集群 2026）和多平台矩阵共存的架构下，联邦管理负责：
- 规范跨集群资源依赖与数据回源边界（如控制 OSS 镜像回源 S3 的访问策略）。
- 统一多租户配置与入口网关调度策略。
- 确保不同云厂商基础设施间平稳协同与演进。
""",
    },

    # 11. 竞品 (Level-1)
    {
        "title": "竞品",
        "category": "公司知识类",
        "tags": ["竞品分析", "Shopify", "LT", "BYD", "一页商店"],
        "summary": "行业竞品调研分析，包含 LT（Shopify 极速静态铺货）与 BYD（漏斗单页转化）商业模式与技术打法借鉴。",
        "favorite": False,
        "markdown": """# 竞品

行业代表性竞品模式调研与打法借鉴：

## LT 竞品模式
- **核心定位**：以 Shopify 为主体、采用单页模式快速发布大量商品的一类竞争对手。
- **代表站点**：`www.alaskatag.com`、`eurshap.com`、`homewore.com`、`paxcd.com`、`melbob.com`、`syytop.com`、`lapupoo.com`、`blackenx.com`、`londonwind.com`、`poinnte.com`、`shopcomebuy.com`、`gotysles.com`、`lilacois.com` 等。
- **业务打法**：采用极低成本、极高效率的标准化运作，初级人员即可完成页面制作。
- **标准流程**：制作设计稿 → 生成静态 HTML → 发布静态资源到 Shopify → 上传图片 → 将 HTML 转换为自定义 Liquid 模版。
- **AI 赋能**：已全面引入 AI 自动化生成工具（如 D2C）快速铺货，抢占市场份额。

## BYD 竞品模式
- **核心定位**：采用单页模式与漏斗（Funnel）引导机制搭建的一类竞品站点。
- **示例路径**：`https://m.acssart.com/funnel/news-garden-hose-nozzle-high-pressure-washer-with-3-high-pressure-nozzles`
- **内部适配进展**：内部目前正推进将 BYD 内容无缝适配到一页商店体系，涵盖结账页装修配置映射、新增业务模块的导入脚本支持等。
""",
    },

    # 12. D2C (名词下 Level-2)
    {
        "title": "D2C",
        "category": "技术类",
        "tags": ["名词解释", "D2C", "AI工具", "Shopify", "静态页面"],
        "summary": "LT 旗下用于快速生成静态页面 ZIP 包并上品到 Shopify 平台的 AI 自动化生产工具。",
        "favorite": False,
        "markdown": """# D2C

D2C 是 LT 团队使用的一款 **AI 静态页面生成工具**。

- **产物形态**：直接使用工具输出纯静态页面 ZIP 压缩包。
- **业务用途**：LT 利用该产物直接批量上品到 Shopify 等电商平台的店铺上，实现极低成本、标准化的快速铺货上线流程。
""",
    },

    # 13. 水合 (名词下 Level-2)
    {
        "title": "水合",
        "category": "技术类",
        "tags": ["名词解释", "水合", "Hydration", "SSR", "前端开发"],
        "summary": "前端 Nuxt/SSR 服务端渲染页面在客户端被 JavaScript 接管、激活交互与事件绑定的 Hydration 机制。",
        "favorite": False,
        "markdown": """# 水合 (Hydration)

“水合”在前端开发中通常是指 **Hydration (Hydrate)**。在本项目体系中特指 **Nuxt / Vue 的 SSR 页面水合机制**。

## 核心原理解析
1. **服务端生成 HTML (SSR)**：Node/Nuxt 服务器预先将页面组件渲染成纯 HTML 字符串并返回给浏览器。
2. **首屏瞬间呈现**：浏览器加载 HTML 后，用户立即可看到完整的页面骨架与内容。
3. **客户端 JS 接管**：前端 JavaScript 运行时在后台加载完毕后，介入并“接管”这些已渲染的静态 HTML。
4. **激活交互状态**：完成事件监听绑定（如按钮点击、滚动事件）、组件响应式状态初始化及动态动画挂载。

> 这一“接管静态 HTML 并激活交互”的完整过程，即称为“水合 (Hydration)”。
""",
    },

    # 14. SSR / CSR (名词下 Level-2)
    {
        "title": "SSR / CSR",
        "category": "技术类",
        "tags": ["名词解释", "SSR", "CSR", "前端架构", "渲染模式"],
        "summary": "服务端渲染 (SSR) 与客户端渲染 (CSR) 技术差异、首屏直出性能及水合绑定机制详解。",
        "favorite": False,
        "markdown": """# SSR / CSR

前端两大主流渲染模式技术对比：

## SSR (Server-Side Rendering) 服务端渲染
- **工作机制**：服务器接收请求后，在后端直接构建渲染好完整的 HTML 结构并返回给客户端。
- **示例输出**：
  ```html
  <h1>iPhone 17</h1>
  <p>$999</p>
  ```
- **核心优势**：用户进入页面后首屏内容立即可见，SEO 友好。
- **水合接管**：HTML 展示后，Vue/React 加载前端 JS，完成点击事件、动态动画、状态管理的挂载绑定，此过程即为“水合（Hydration）”。

## CSR (Client-Side Rendering) 客户端渲染
- **工作机制**：服务器仅返回一个轻量级 HTML 外壳和 JavaScript 脚本包。
- **页面构建**：浏览器端执行 JS 代码，通过 API 异步请求数据并动态创建 DOM 节点渲染页面。
""",
    },

    # 15. SSL for SaaS 功能 (名词下 Level-2)
    {
        "title": "SSL for SaaS 功能",
        "category": "技术类",
        "tags": ["名词解释", "SSL for SaaS", "Cloudflare", "自定义域名", "HTTPS证书"],
        "summary": "Cloudflare SSL for SaaS 能力解析：支持客户绑定自有域名并自动签发、管理和续期 SSL 证书。",
        "favorite": False,
        "markdown": """# SSL for SaaS 功能

Cloudflare 的 **SSL for SaaS** 功能是专门面向 SaaS 平台客户接入自定义域名的核心边缘解决方案。

## 典型应用场景
- **平台默认域名**：`shop.example.com`
- **客户自有独立域名**：`www.customer.com`
- **业务诉求**：客户希望将 `https://www.customer.com` CNAME 指向平台，并由平台自动提供安全加密访问。

## 核心能力
- **自动签发 SSL 证书**：客户完成 CNAME 记录配置后，Cloudflare 自动完成免费 SSL/TLS 证书签发。
- **自动证书续期**：免去人工维护和证书过期的风险。
- **海量自定义域名支持**：平台可通过 API 或控制台批量管理数以万计的第三方客户域名接入。
- **智能回退源 (Custom Origin Server)**：统一将客户域名访问流量精准代理路由至平台源站服务器。
""",
    },

    # 16. AWS abuse 风险 (名词下 Level-2)
    {
        "title": "AWS abuse 风险",
        "category": "技术类",
        "tags": ["名词解释", "AWS", "Abuse", "风控", "云安全"],
        "summary": "云厂商 AWS 对账号、CDN、域名或存储桶违规滥用风险的判定及多租户架构中的防护规避措施。",
        "favorite": False,
        "markdown": """# AWS abuse 风险

## 风险定义
**AWS abuse 风险** 指亚马逊云 (AWS) 监控判定用户账号、域名、CDN (CloudFront)、服务器 (EC2) 或存储桶 (S3) 等资源存在被滥用、侵权、违规或遭遇恶意投诉的风险。

## 业务影响与防护应对
- **潜在风险**：在多租户电商独立站体系中，若某一个商户或域名发生违规投诉，可能触发云厂商对整个主账号资源的限制甚至封禁。
- **架构隔离策略**：
  - 通过新集群（如阿里云主集群）与旧集群进行多租户物理与逻辑隔离。
  - 使用 ESA / OpenResty 分配独立的边缘出口 IP 与域名接入通道。
  - 避免单个高风险商户影响整体公共主集群的稳定运行。
""",
    },

    # 17. ESA (名词下 Level-2)
    {
        "title": "ESA",
        "category": "技术类",
        "tags": ["名词解释", "ESA", "流量网关", "CNAME", "阿里云"],
        "summary": "边缘安全加速 (Edge Security Acceleration) 核心作用、域名回源解析、多集群隔离与配置规范。",
        "favorite": False,
        "markdown": """# ESA (边缘安全加速)

**ESA** 是 LF 公司内部用于新集群（如阿里云主集群）的域名绑定与流量路由服务。主要功能是通过配置 CNAME 解析将店铺域名指向特定入口（如 OpenResty 或 Ingress），实现流量的灵活调度与资源访问控制。

## 核心作用

### 1. 域名解析与回源管理
- 通过绑定店铺域名至 ESA，添加 CNAME 记录指向集群入口（如 `o.flyshopon.com` 或 `c.flyshopon.com`），实现流量路由。例如将 `dictatedexp69.fffzzz.top` 解析至 ESA 后，请求可路由至 OpenResty 或 Ingress 入口。
- 支持动态调整回源地址，无需修改域名解析即可完成流量切换（如从 OpenResty 入口无感切换至 Ingress 入口）。

### 2. 多集群隔离与资源配置
- 作为阿里云主集群专属入口，与旧集群实现网络隔离，需独立配置环境变量、密钥及资源桶（如 OSS 桶镜像回源至 S3）。
- 新集群店铺创建时需选择 `esa` 域名绑定策略，并添加 `use_tmp_esa` 标签，由基础设施团队完成配置。

### 3. SSL 证书与安全验证
- 自动生成免费 SSL 证书，无需商户手动配置 TXT 记录验证域名所有权，极大简化上线部署流程。

---

## 配置要点
- **域名绑定**：需提供完整店铺域名（如 `auntiemai2.shoplance.xyz`），由基础设施团队在 ESA 中配置 CNAME 解析。
- **路径规则**：支持自定义回源路径（如 `/cdn/shop/files/` 映射至 OSS 桶），需同步配置 CDN 路由与资源隔离策略。
- **兼容性**：需确保与现有系统（如主题 V1 静态资源、一页商店）的路径规则兼容，避免跨域或 404 错误。

---

## 典型应用场景
- **新集群迁移**：作为阿里云主集群承接 AWS 流量的核心入口，支持店铺平滑迁移与动态切流。
- **多租户隔离**：通过独立的 ESA 实例与出口 IP，满足非运营店铺的特征隔离需求，降低审核风险。
- **团队协作**：ESA 的配置需与基础设施团队紧密协作，确保域名解析、资源路径与集群环境的一致性。
""",
    },

    # 18. OpenResty (名词下 Level-2)
    {
        "title": "OpenResty",
        "category": "技术类",
        "tags": ["名词解释", "OpenResty", "网关", "NLB", "Valkey", "Wshop"],
        "summary": "Wshop 与阿里云集群核心流量入口网关定位、路由特性、双写升级 Valkey 及运维演进记录。",
        "favorite": False,
        "markdown": """# OpenResty

**OpenResty** 是 LF 内部 Wshop 项目集群的关键流量入口网关。

## 核心定位与基础能力
- **核心入口**：Wshop 集群的两大店铺流量入口之一（另一个为 Ingress），具备店铺精准识别能力。
- **缓存体系**：使用 Zhuhu Redis 缓存存储店铺域名、版本信息，同时支持 OpenResty 租户识别。

## 流量路由相关特性
- **新集群入口承接**：可作为新集群（如阿里云主集群）ESA 服务的流量入口。在店铺域名绑定 ESA 并配置 CNAME 解析后，流量即可路由至 OpenResty 入口。
- **动态切流**：支持动态调整回源地址，无需修改域名解析，即可在 OpenResty 入口与 Ingress 入口之间完成流量切换。
- **跨集群专线**：阿里云集群内的 OpenResty 部署在 `aliyun-us-cluster`，上游对接 IP 为 `47.252.36.130` 的阿里云负载均衡，能够承接 `*.o`（`shopride.top` / `shoprose.net`）的托管域名，以及主集群 `zhyxgate` 通过 `endtoalywaf` 策略过来的特殊跨集群链路。
- **API 路由回源**：店铺接口路由 `/api/` 统一通过店铺 OpenResty 入口进行回源处理。

## 运维演进里程碑记录
- **2026 年 4 月 (4.6 ~ 4.12)**：团队完成新建 OpenResty 的 NLB 入口工作，逐步将早期 CLB 类型入口的流量灰度切换至新的 NLB 入口，同时完成非生产平台 o 域名到 NLB 入口的解析切换。
- **2026 年 8 月 ~ 9 月**：团队启动将 OpenResty 升级至 **Valkey** 的技术演进方案，落地流程为：
  1. 控制中心新旧实例双写；
  2. 将 `wshop-openresty` 服务切流至新实例；
  3. 下线旧实例。
- **2026 年 9 月第二周**：团队完成内部网关和 OpenResty 的硬编码问题修复，推进完成 OpenResty 的新实例替换。

## 架构方案评价
使用 Wshop OpenResty 作为单页店铺入口的方案架构清晰，对流量管理友好，能够显著提升流量网关的能力，同时通过标准化配置降低运维复杂度。
""",
    },
]


async def main():
    print(f">>> Starting batch ingestion for {len(SECTIONS_DATA)} sections from 名词解释.docx...")
    async with AsyncSessionLocal() as session:
        # 1. Resolve or create categories
        categories = await list_categories(session)
        cat_map = {c.name: c.id for c in categories}

        if "技术类" not in cat_map:
            new_cat = await create_category(
                session,
                CategoryCreate(
                    name="技术类",
                    description="系统架构、基础设施与工程开发技术指南",
                    icon="code",
                    color="#2563EB",
                ),
            )
            cat_map["技术类"] = new_cat.id

        if "公司知识类" not in cat_map:
            new_cat = await create_category(
                session,
                CategoryCreate(
                    name="公司知识类",
                    description="公司业务、运营规范与行业竞品分析",
                    icon="building",
                    color="#10B981",
                ),
            )
            cat_map["公司知识类"] = new_cat.id

        # 2. Resolve or create tags
        existing_tags = await list_tags(session)
        tag_map = {t.name: t.id for t in existing_tags}

        all_needed_tags = set()
        for sec in SECTIONS_DATA:
            all_needed_tags.update(sec["tags"])

        for tname in sorted(all_needed_tags):
            if tname not in tag_map:
                new_t = await create_tag(session, TagCreate(name=tname, color="#3B82F6"))
                tag_map[tname] = new_t.id
                print(f"Created new tag: #{tname}")

        # 3. Create items and index vectors
        indexer = IndexService()
        imported_items = []

        for idx, sec in enumerate(SECTIONS_DATA, start=1):
            category_id = cat_map[sec["category"]]
            tag_ids = [tag_map[t] for t in sec["tags"]]

            blocks = markdown_to_blocks(sec["markdown"])

            k_data = KnowledgeCreate(
                title=sec["title"],
                summary=sec["summary"],
                blocks_json=[b.model_dump() for b in blocks],
                category_id=category_id,
                tag_ids=tag_ids,
                source_type="file",
                status="published",
                favorite=sec.get("favorite", False),
                sources=[
                    SourceInfoCreate(
                        type="file",
                        url="",
                        title="名词解释.docx",
                        file_name="名词解释.docx",
                        metadata_json={
                            "source_file": "docs/名词解释.docx",
                            "section": sec["title"],
                            "rule": "L1 heading or L2 under 名词",
                            "imported_by": "docx_section_ingestion",
                        },
                    )
                ],
            )

            item = await create_knowledge(session, k_data)
            chunk_count = await indexer.index_knowledge_item(session, item)
            imported_items.append((item.id, item.title, chunk_count))
            print(f"[{idx:2d}/{len(SECTIONS_DATA)}] Created & Indexed '{item.title}' (ID: {item.id}, {chunk_count} chunks)")

        print("\n" + "=" * 60)
        print(f"Successfully imported and indexed all {len(imported_items)} knowledge points!")
        print("=" * 60)
        for item_id, title, chunks in imported_items:
            print(f"- {title} (ID: {item_id}, Chunks: {chunks})")


if __name__ == "__main__":
    asyncio.run(main())
