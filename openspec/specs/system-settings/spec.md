# system-settings Specification

## Overview
系统设置模块负责多外部服务适配器（Provider Adapters）的凭证与参数配置，解耦大语言模型、向量嵌入、公网搜索与对象存储等底层基础设施，保障环境可配置与独立自持。

## Requirements

### Requirement: 统一大模型（LLM）接入配置
系统必须提供标准化的 OpenAI 兼容接口配置能力，避免绑定特定厂商。

#### Scenario: 配置对话模型 Provider
- **WHEN** 用户在设置中填写 LLM API Base URL、API Key、模型名称（如 `gpt-4o`、`deepseek-chat` 或本地 Ollama 模型）
- **THEN** 系统持久化保存配置并提供“连通性测试”功能，测试成功后作为系统统一的 AI 对话与优化底层驱动。

### Requirement: Embedding 向量嵌入模型配置
系统必须支持独立配置用于语义召回的向量模型接口与向量维度。

#### Scenario: 配置 Embedding 服务
- **WHEN** 用户配置 Embedding API 终端、密钥、模型标识（如 `text-embedding-3-small`）及向量维度（如 1536 维）
- **THEN** 系统验证其连通性并自动与底层 pgvector 数据表列定义对齐。

### Requirement: 公网搜索服务（Web Search Provider）配置
系统必须支持接入公网实时搜索服务接口或具备联网搜索能力的模型。

#### Scenario: 接入搜索 Provider
- **WHEN** 用户在设置中配置外部搜索服务（如 Tavily, Serper, Bing 搜索 API，或具备原生联网能力的模型）
- **THEN** AI 补充搜索模块根据此配置发起外部信息检索并结构化获取网页引用。

### Requirement: 存储服务适配配置
系统必须支持媒体资源与附件的灵活存储适配，支持本地磁盘或 S3 兼容对象存储。

#### Scenario: 切换存储适配器
- **WHEN** 用户配置存储类型为本地文件目录（Local Path）或 S3 兼容协议（Endpoint, Bucket, Access Key, Secret Key）
- **THEN** 编辑器图片上传、附件保存及备份包生成自动路由到目标存储服务中。
