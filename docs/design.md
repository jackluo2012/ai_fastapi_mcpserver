# FastAPI MCP Streamable HTTP 服务器设计文档

## 1. 项目概述

本项目旨在构建一个基于FastAPI的企业级Model Context Protocol (MCP)服务器，采用2025年最新发布的Streamable HTTP传输协议规范。该服务器为AI Agent提供标准化的工具调用、资源访问和提示词管理能力，同时满足企业级应用对安全性、可观测性和高并发的需求。

### 1.1 核心特性

- **Streamable HTTP协议**：遵循MCP Streamable HTTP规范，采用单端点双向通信架构
- **异步优先**：基于FastAPI ASGI的高并发异步处理能力
- **企业级安全**：API Key鉴权、Origin校验、零信任安全模型
- **可观测性**：结构化日志（Structlog）和Prometheus指标监控
- **弹性设计**：自动重试、连接池管理、超时熔断机制

## 2. 架构设计

### 2.1 设计原则

| 原则 | 描述 | 实现策略 |
|------|------|----------|
| **异步优先** | 所有I/O操作必须是非阻塞的 | 基于Python asyncio和FastAPI的async def语法 |
| **可观测性驱动** | 系统必须提供透明的内部状态 | Prometheus指标导出与结构化JSON日志 |
| **零信任安全** | 默认不信任任何调用方 | 强制API Key鉴权，严格校验Origin标头 |
| **弹性设计** | 系统应具备自我恢复能力 | 指数退避重试机制，连接池管理与超时熔断 |

### 2.2 系统分层架构

```
┌─────────────────────────────────────┐
│   接口接入层 (Interface Layer)      │
│   - FastAPI Router                  │
│   - HTTP请求处理                     │
│   - API Key鉴权                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   协议适配层 (Protocol Layer)        │
│   - MCP SDK封装                      │
│   - JSON-RPC消息处理                 │
│   - Session管理                      │
│   - SSE连接升级                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   业务逻辑层 (Service Layer)         │
│   - Tools (工具)                     │
│   - Resources (资源)                  │
│   - Prompts (提示词)                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   基础设施层 (Infrastructure Layer)  │
│   - AsyncHttpClient                  │
│   - Observability Adapter            │
│   - Structured Logger                │
└─────────────────────────────────────┘
```

### 2.3 核心组件

1. **接口接入层**
   - 处理 `/mcp` 路径的POST和GET请求
   - 执行TLS终结、CORS策略校验
   - API Key初步验证

2. **协议适配层**
   - 封装MCP SDK核心逻辑
   - 管理 `Mcp-Session-Id` 生命周期
   - 处理SSE连接升级

3. **业务逻辑层**
   - 工具、资源、提示词的具体实现
   - 通过装饰器注册到MCP服务器实例
   - 纯Python函数，不感知HTTP协议细节

4. **基础设施层**
   - `AsyncHttpClient`：封装httpx，提供异步HTTP调用能力
   - `Observability Adapter`：收集指标并暴露 `/metrics` 端点
   - `Structured Logger`：基于Structlog的日志外观模式

## 3. Streamable HTTP传输层

### 3.1 统一端点设计

根据Streamable HTTP规范，服务器提供单一端点 `/mcp`：

- **POST请求**：客户端发送JSON-RPC消息（调用工具、列出资源等）
- **GET请求**：建立SSE事件流（服务器到客户端的单向消息通道）

### 3.2 会话管理

- **Session ID生成**：客户端发送 `InitializeRequest` 时，服务器生成UUIDv4格式的Session ID
- **Session保持**：后续请求通过 `Mcp-Session-Id` 头部携带Session ID
- **状态存储**：单实例使用内存存储，多副本部署使用Redis等分布式缓存

### 3.3 SSE流式处理

- 检测到 `Accept: text/event-stream` 头时升级为SSE模式
- 利用FastAPI的 `StreamingResponse` 处理流式响应
- 定期发送保活心跳包防止负载均衡器超时断开

## 4. 安全架构

### 4.1 API Key鉴权

- **传输方式**：支持 `X-API-Key` 头部或 `Authorization: Bearer <key>` 格式
- **验证机制**：使用 `secrets.compare_digest()` 进行恒定时间比较，防御时序攻击
- **验证位置**：在请求处理最前端通过FastAPI Security依赖项拦截

### 4.2 网络安全策略

- **Origin校验**：严格检查HTTP请求的Origin头部，匹配预定义允许域名列表
- **CORS配置**：通过FastAPI CORSMiddleware配置，禁止使用通配符 `allow_origins=["*"]`
- **DNS重绑定防护**：严格校验Origin，防止DNS重绑定攻击

## 5. 可观测性

### 5.1 结构化日志

- **日志框架**：基于Structlog，输出JSON格式日志
- **上下文绑定**：自动注入Request-ID（Correlation ID），实现全链路追踪
- **标准化字段**：`event`（事件名称）、`severity`（严重等级）、`module`（模块名）、`latency_ms`（耗时）

### 5.2 Prometheus指标监控

**基础HTTP指标**：
- `http_requests_total`：请求总数（按method、handler、status标签）
- `http_request_duration_seconds`：请求处理延迟分布

**MCP特有指标**：
- `mcp_tool_execution_total`：工具执行总数（按tool_name、status标签）
- `mcp_tool_duration_seconds`：工具执行耗时直方图
- `mcp_tool_errors_total`：工具错误计数（按tool_name、error_type标签）

## 6. 基础设施工具

### 6.1 异步HTTP客户端

- **实现**：封装 `httpx.AsyncClient` 作为全局单例
- **生命周期管理**：通过FastAPI lifespan事件管理连接池的创建和销毁
- **连接池优化**：配置 `max_keepalive_connections=50`、`max_connections=100`

### 6.2 弹性设计

- **重试策略**：使用Tenacity库实现指数退避重试（最多3次）
- **故障限定**：仅对网络超时、连接错误、503等可重试异常进行重试
- **超时配置**：默认30秒超时，可根据业务需求调整

## 7. 项目结构

```
fastapi-mcp-server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # 应用入口与生命周期管理
│   ├── core/                      # 核心配置与基础组件
│   │   ├── config.py              # Pydantic Settings环境变量管理
│   │   ├── security.py            # API Key鉴权逻辑
│   │   ├── logging.py             # Structlog配置
│   │   └── exceptions.py          # 全局异常处理
│   ├── mcp_server/                # MCP协议具体实现
│   │   ├── app.py                 # MCP实例初始化与工具注册
│   │   └── transport.py           # Streamable HTTP传输层封装
│   ├── tools/                     # 业务工具逻辑（按领域划分）
│   │   ├── __init__.py
│   │   ├── base.py                # 工具基类与通用装饰器
│   │   ├── demo.py                # Hello World示例
│   │   └── system.py              # 系统级工具
│   └── utils/                     # 通用工具库
│       ├── http_client.py         # 封装的Httpx客户端
│       └── metrics.py             # Prometheus指标定义
├── tests/                         # 单元与集成测试
├── Dockerfile                     # 容器构建文件
├── pyproject.toml                 # 依赖管理
└── .env.example                   # 环境变量模板
```

## 8. 关键技术实现

### 8.1 配置管理

使用Pydantic `BaseSettings` 从环境变量加载配置，确保类型安全：

```python
class Settings(BaseSettings):
    MCP_API_KEY: str              # API密钥
    ALLOWED_ORIGINS: list[str]     # 允许的Origin列表
    LOG_LEVEL: str = "INFO"        # 日志级别
    JSON_LOGS: bool = True         # JSON日志格式
    PROMETHEUS_ENABLED: bool = True
```

### 8.2 鉴权实现

在ASGI层面包装MCP应用，确保所有请求在进入MCP SDK处理前完成鉴权：

```python
async def protected_mcp_app(scope, receive, send):
    # 提取并验证API Key
    # 验证通过后移交给MCP SDK处理
```

### 8.3 监控装饰器

通过装饰器模式实现工具执行的自动监控：

```python
@track_tool_execution(tool_name="hello_world")
async def hello_world(name: str) -> str:
    # 工具实现
    # 自动记录执行时间、错误等指标
```

## 9. 部署与扩展

### 9.1 容器化

- **多阶段构建**：减小镜像体积，提高安全性
- **生产级ASGI服务器**：使用Uvicorn，在Kubernetes中通过Deployment配置副本数
- **环境变量**：通过环境变量注入配置，避免硬编码

### 9.2 横向扩展

- **无状态设计**：推荐保持MCP工具的无状态性，支持随机负载均衡
- **会话粘性**：如需有状态特性，可通过Kubernetes Ingress配置Session Affinity
- **状态外置**：复杂状态存储到Redis等外部存储

## 10. 技术栈

- **Web框架**：FastAPI (ASGI)
- **MCP SDK**：modelcontextprotocol/python-sdk
- **HTTP客户端**：httpx (异步)
- **日志**：structlog
- **监控**：prometheus-fastapi-instrumentator, prometheus_client
- **重试**：tenacity
- **配置管理**：pydantic-settings
- **容器运行时**：Uvicorn

## 11. 参考规范

- [MCP Streamable HTTP Transport Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 12. 后续优化方向

1. **性能优化**：连接池参数调优、异步数据库驱动集成
2. **安全增强**：JWT Token支持、Rate Limiting、请求签名验证
3. **可观测性**：分布式追踪（OpenTelemetry）、APM集成
4. **高可用**：健康检查、优雅关闭、故障转移机制
