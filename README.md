# FastAPI MCP Server

基于 FastAPI 构建的企业级 Model Context Protocol (MCP) 服务器框架，采用 2025 Streamable HTTP 传输协议规范。开箱即用，专为快速开发 MCP Tools / Resources / Prompts 而设计。

## 核心特性

- **Streamable HTTP 传输** - 遵循 MCP 2025-06-18 规范，单端点 (`/mcp/`) 双向通信，无状态模式无需 `initialize`
- **异步优先** - 基于 FastAPI ASGI，全链路 async/await，高并发低延迟
- **企业级安全** - API Key 鉴权（Bearer / X-API-Key）、Origin 校验、恒定时间比较防时序攻击
- **可观测性** - Structlog 结构化 JSON 日志 + Prometheus 指标（工具粒度耗时/计数/错误率）
- **日志分级输出** - 控制台 + `logs/app.log`（全量）+ `logs/app.log.wf`（WARNING+），自动轮转
- **弹性设计** - httpx 连接池 + Tenacity 指数退避重试 + 优雅关闭
- **开发友好** - `@mcp_tool` 一个装饰器完成工具注册 + 监控埋点，零样板代码

---

## 快速开始

### 1. 环境要求

- Python 3.11+
- pip

### 2. 安装

```bash
# 克隆项目
git clone <your-repo-url>
cd fastapi_mcpserver_base

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

```bash
cp .env.example .env
```

编辑 `.env`，**必须设置 `MCP_API_KEY`**：

```env
MCP_API_KEY=your-secret-api-key      # 必填：MCP 端点鉴权密钥
PORT=8007                             # 服务端口，默认 8000
LOG_LEVEL=INFO                        # 日志级别：DEBUG / INFO / WARNING / ERROR
JSON_LOGS=true                        # true=JSON格式(生产), false=彩色终端(开发)
```

完整配置项见 [.env.example](.env.example)。

### 4. 启动服务

```bash
# 方式一：直接运行
python -m app.main

# 方式二：uvicorn（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8007
```

### 5. 验证服务

```bash
# 健康检查
curl http://localhost:8007/health

# 列出所有 MCP 工具
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'

# 调用 hello_world 工具
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"hello_world","arguments":{"name":"Alice"}},"id":2}'
```

### 6. Docker 部署

```bash
docker build -t fastapi-mcp-server .
docker run -p 8007:8000 -e MCP_API_KEY=your-secret-api-key fastapi-mcp-server
```

---

## 服务端点一览

| 端点 | 方法 | 鉴权 | 说明 |
|------|------|------|------|
| `/` | GET | 否 | API 基本信息 |
| `/health` | GET | 否 | 健康检查（K8s liveness/readiness） |
| `/docs` | GET | 否 | Swagger UI 文档 |
| `/redoc` | GET | 否 | ReDoc 文档 |
| `/metrics` | GET | 否 | Prometheus 指标 |
| `/mcp/` | POST | 是 | MCP JSON-RPC 端点（**必须带末尾 `/`**） |

MCP 端点支持两种鉴权方式：
- `Authorization: Bearer <key>`
- `X-API-Key: <key>`

---

## 项目结构

```
fastapi_mcpserver_base/
├── app/                          # 应用主包
│   ├── main.py                   # FastAPI 入口：中间件、生命周期、路由挂载
│   ├── core/                     # 核心基础设施
│   │   ├── config.py             # Pydantic Settings 配置管理（.env 加载）
│   │   ├── security.py           # API Key 鉴权 + Origin 校验
│   │   ├── logging.py            # Structlog 日志配置（控制台 + 文件分级）
│   │   └── exceptions.py         # 全局异常类 + 异常处理器
│   ├── mcp_server/               # MCP 协议层
│   │   ├── app.py                # FastMCP 实例初始化 + 工具/资源/提示词注册
│   │   └── transport.py          # ASGI 鉴权包装器（API Key 校验在 MCP SDK 之前）
│   ├── tools/                    # ★ 业务工具层（开发者主要工作区）
│   │   ├── base.py               # @mcp_tool 装饰器工厂（注册 + 监控一体化）
│   │   ├── demo.py               # 演示工具：hello_world, echo
│   │   ├── system.py             # 系统工具：get_server_info, fetch_external_data
│   │   ├── resources.py          # MCP 资源：server-info, server-status
│   │   └── prompts.py            # MCP 提示词：code_review, data_analysis
│   └── utils/                    # 通用工具
│       ├── http_client.py        # 异步 HTTP 客户端（连接池 + 重试）
│       └── metrics.py            # Prometheus 指标定义 + 监控装饰器
├── tests/                        # 测试套件
│   ├── conftest.py               # Pytest fixtures（TestClient, api_key 等）
│   ├── test_main.py              # 端点测试
│   ├── test_security.py          # 鉴权测试
│   ├── test_tools.py             # 工具单元测试
│   ├── test_config.py            # 配置加载测试
│   ├── test_crewai.py            # MCP 协议 + CrewAI Agent 集成测试
│   ├── test_mcp_direct.py        # 直接 HTTP 调用 MCP 端点测试
│   ├── unit/                     # 单元测试
│   │   ├── core/test_logging.py
│   │   ├── tools/test_basic.py
│   │   ├── tools/test_business.py
│   │   └── infrastructure/test_http_client.py
│   └── integration/              # 集成测试
│       └── test_api_endpoints.py
├── examples/
│   └── list_tools.py             # 示例：纯 HTTP 调用 MCP 接口
├── docs/                         # 设计文档
├── logs/                         # 日志输出目录（gitignore）
├── .env.example                  # 环境变量模板
├── Dockerfile                    # 多阶段 Docker 构建
├── pyproject.toml                # 项目元数据 + 工具链配置
└── requirements.txt              # Python 依赖
```

---

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────┐
│  Client (CrewAI / curl / MCP Inspector / ...)       │
└────────────────────────┬────────────────────────────┘
                         │ HTTP POST /mcp/
┌────────────────────────▼────────────────────────────┐
│  Interface Layer   (app/main.py)                     │
│  ├─ CORS Middleware                                  │
│  ├─ Request-ID + Latency Middleware                  │
│  ├─ Origin Verification Middleware                   │
│  └─ Prometheus Instrumentator                        │
├──────────────────────────────────────────────────────┤
│  Protocol Layer    (app/mcp_server/)                 │
│  ├─ transport.py   ASGI Auth Wrapper (API Key)       │
│  └─ app.py         FastMCP Instance (Streamable HTTP)│
├──────────────────────────────────────────────────────┤
│  Service Layer     (app/tools/)                      │
│  ├─ @mcp_tool      Tools   (hello_world, echo, ...)  │
│  ├─ @mcp.resource  Resources (server-info, ...)      │
│  └─ @mcp.prompt    Prompts   (code_review, ...)      │
├──────────────────────────────────────────────────────┤
│  Infrastructure    (app/core/ + app/utils/)           │
│  ├─ config.py      Pydantic Settings                 │
│  ├─ logging.py     Structlog + File Rotation         │
│  ├─ security.py    Auth & Origin Verification        │
│  ├─ http_client.py Async HTTP + Retry                │
│  └─ metrics.py     Prometheus Counters/Histograms    │
└──────────────────────────────────────────────────────┘
```

### 请求处理流程

```
Client POST /mcp/ (Bearer token)
  → CORS Middleware
  → Request-ID Middleware (生成/透传 X-Request-ID, 绑定 contextvars)
  → Origin Middleware (跳过 /mcp 路径)
  → Starlette Mount → ASGI transport.py
    → verify_api_key_asgi() → 403 或继续
    → FastMCP Streamable HTTP handler
      → JSON-RPC dispatch (tools/call, resources/read, prompts/get, ...)
      → @mcp_tool → track_tool_execution (Prometheus) → 业务函数
    → SSE / JSON 响应
  → Latency 记录 + X-Request-ID 响应头
```

### 关键设计决策

| 问题 | 方案 | 原因 |
|------|------|------|
| MCP 端点鉴权 | ASGI 层包装而非 FastAPI `Depends()` | `app.mount()` 的子应用无法使用 FastAPI 依赖注入 |
| 请求上下文传递 | `structlog.contextvars` | async 安全，一次绑定全链路可见 |
| 日志分级 | stdlib `RotatingFileHandler` + structlog `ProcessorFormatter` | 多路输出，文件 JSON 便于采集 |
| 工具监控 | 装饰器自动埋点 | 开发者零负担，所有工具自动获得 Prometheus 指标 |

---

## 开发教程：添加自定义 MCP Tool / Resource / Prompt

本框架的核心价值在于让你专注于业务逻辑。以下是开发三种 MCP 能力的完整指南。

### 一、添加 MCP Tool（工具）

工具是 AI Agent 可以调用的函数。这是最常用的扩展点。

#### 步骤 1：在 `app/tools/` 下创建模块

创建 `app/tools/weather.py`：

```python
"""
天气查询工具模块
"""
from app.core.logging import get_logger
from app.mcp_server.app import mcp_tool

logger = get_logger()


@mcp_tool(
    name="get_weather",
    description="查询指定城市的天气信息",
)
async def get_weather(city: str, unit: str = "celsius") -> dict:
    """
    查询天气信息

    Args:
        city: 城市名称
        unit: 温度单位，celsius 或 fahrenheit

    Returns:
        dict: 包含温度、湿度等天气信息
    """
    logger.info("querying_weather", city=city, unit=unit)

    # 你的业务逻辑，例如调用外部天气 API
    from app.utils.http_client import http_client
    data = await http_client.get(
        f"https://api.weather.example.com/v1/current?city={city}&unit={unit}"
    )

    return {
        "city": city,
        "temperature": data["temp"],
        "humidity": data["humidity"],
        "description": data["description"],
    }
```

**要点：**

- 使用 `@mcp_tool(name=..., description=...)` 装饰器，自动完成 MCP 注册 + Prometheus 监控
- 函数参数会自动生成 JSON Schema，成为 MCP `inputSchema`
- 参数类型标注必须写清楚，MCP 客户端依赖此信息
- 支持默认值（`unit="celsius"` 会在 schema 中标记为 optional）
- 返回值会自动序列化为 JSON

#### 步骤 2：注册模块

编辑 `app/mcp_server/app.py`，在导入行添加你的模块：

```python
# 导入工具模块以触发装饰器注册
from app.tools import demo, system, resources, prompts, weather  # 添加 weather
```

#### 步骤 3：编写测试

创建 `tests/test_weather.py`：

```python
import pytest
from unittest.mock import patch, AsyncMock

from app.tools.weather import get_weather


@pytest.mark.asyncio
async def test_get_weather():
    mock_data = {"temp": 22.5, "humidity": 65, "description": "晴"}
    with patch("app.tools.weather.http_client") as mock_client:
        mock_client.get = AsyncMock(return_value=mock_data)
        result = await get_weather("北京")
        assert result["city"] == "北京"
        assert result["temperature"] == 22.5
```

#### 步骤 4：验证

```bash
# 运行测试
pytest tests/test_weather.py -v

# 启动服务后调用
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_weather","arguments":{"city":"北京"}},"id":1}'
```

完成。`@mcp_tool` 一个装饰器自动提供：
- MCP `tools/list` 中展示此工具
- `tools/call` 可调用此工具
- Prometheus 指标自动采集（`mcp_tool_execution_seconds{tool_name="get_weather"}`）
- 结构化日志自动关联 `request_id`

---

### 二、添加 MCP Resource（资源）

资源是 AI Agent 可以读取的静态/动态数据源，类似于 REST API 的 GET 端点。

#### 创建资源

在 `app/tools/resources.py` 中添加（或创建新模块）：

```python
import json
from app.core.logging import get_logger
from app.mcp_server.app import mcp

logger = get_logger()


@mcp.resource(
    "resource://database-schema",
    name="database_schema",
    description="数据库表结构信息",
)
async def database_schema_resource() -> str:
    """返回数据库 schema 信息，供 Agent 理解数据结构"""
    schema = {
        "tables": [
            {
                "name": "users",
                "columns": ["id", "name", "email", "created_at"],
            },
            {
                "name": "orders",
                "columns": ["id", "user_id", "amount", "status"],
            },
        ]
    }
    logger.info("resource_accessed", resource="database_schema")
    return json.dumps(schema, ensure_ascii=False, indent=2)
```

**要点：**

- 使用 `@mcp.resource(uri, name=..., description=...)` 装饰器（注意是 `mcp` 不是 `mcp_tool`）
- URI 格式为 `resource://your-resource-name`
- 返回值必须是 `str`（通常为 JSON 字符串）
- 客户端通过 `resources/list` 发现，通过 `resources/read` 读取

#### 客户端调用

```bash
# 列出所有资源
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"resources/list","params":{},"id":1}'

# 读取资源
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"resource://database-schema"},"id":2}'
```

---

### 三、添加 MCP Prompt（提示词模板）

Prompt 是可参数化的提示词模板，AI Agent 可以获取并填充参数后使用。

#### 创建提示词

在 `app/tools/prompts.py` 中添加：

```python
from app.core.logging import get_logger
from app.mcp_server.app import mcp

logger = get_logger()


@mcp.prompt(name="sql_generator", description="根据自然语言生成 SQL 查询")
async def sql_generator_prompt(
    question: str,
    database_type: str = "PostgreSQL",
) -> str:
    """
    生成 SQL 查询的提示词模板

    Args:
        question: 用户的自然语言问题
        database_type: 数据库类型
    """
    logger.info("prompt_accessed", prompt="sql_generator")
    return (
        f"你是一个 {database_type} 数据库专家。\n\n"
        f"根据以下问题生成准确的 SQL 查询：\n"
        f"问题：{question}\n\n"
        f"要求：\n"
        f"1. 使用标准 {database_type} 语法\n"
        f"2. 添加必要的注释说明\n"
        f"3. 考虑性能优化（索引利用等）\n"
        f"4. 如果涉及聚合，使用合适的 GROUP BY\n"
    )
```

**要点：**

- 使用 `@mcp.prompt(name=..., description=...)` 装饰器
- 函数参数即为模板参数，客户端在 `prompts/get` 时传入
- 返回值为字符串，即最终生成的提示词文本
- 客户端通过 `prompts/list` 发现，通过 `prompts/get` 获取渲染后的内容

#### 客户端调用

```bash
# 列出所有提示词
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"prompts/list","params":{},"id":1}'

# 获取渲染后的提示词
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"prompts/get","params":{"name":"sql_generator","arguments":{"question":"查询最近7天的订单总额","database_type":"MySQL"}},"id":2}'
```

---

### 开发 Checklist

添加任何新功能时，按此清单操作：

```
1. [ ] 在 app/tools/ 下创建或编辑模块
       - Tool:     使用 @mcp_tool(name, description)
       - Resource: 使用 @mcp.resource(uri, name, description)
       - Prompt:   使用 @mcp.prompt(name, description)

2. [ ] 在 app/mcp_server/app.py 的导入行注册模块
       from app.tools import ..., your_module

3. [ ] 编写测试
       tests/test_your_module.py

4. [ ] 运行测试验证
       pytest tests/ -v

5. [ ] 启动服务，用 curl / MCP Inspector / CrewAI 验证
```

---

## 测试

### 单元测试

```bash
# 运行所有测试
pytest tests/ -v

# 排除需要启动服务的集成测试
pytest tests/ -v --ignore=tests/test_crewai.py --ignore=tests/test_mcp_direct.py

# 带覆盖率
pytest tests/ --cov=app --cov-report=html
```

### MCP 集成测试

`tests/test_crewai.py` 包含 12 个校验点，涵盖协议级和 Agent 级测试。需要先启动服务：

```bash
# 终端 1：启动服务
python -m app.main

# 终端 2：运行协议测试（不需要 LLM）
pytest tests/test_crewai.py::TestMCPProtocol -v -s

# 运行 CrewAI Agent 测试（需要 LLM API Key）
export OPENAI_API_KEY=your-key
export OPENAI_API_BASE=https://your-api-base/v1   # 如使用兼容接口
export NO_PROXY=127.0.0.1,localhost                # 如有本地代理需设置
pytest tests/test_crewai.py -v -s
```

集成测试校验点：

| 类别 | 校验内容 |
|------|----------|
| 健康检查 | `/health` 返回 `status: ok` |
| 工具列表 | `tools/list` 返回 4 个工具，每个含 description 和 inputSchema |
| 资源列表 | `resources/list` 返回 2 个资源 |
| 提示词列表 | `prompts/list` 返回 2 个提示词 |
| 工具调用 | `hello_world` / `echo` / `get_server_info` 返回值正确 |
| 资源读取 | `resources/read` 返回有效 JSON |
| 提示词获取 | `prompts/get` 返回渲染后的模板 |
| 鉴权拒绝 | 无 API Key 返回 403 |
| Agent 端到端 | CrewAI Agent 成功通过 MCP 调用工具并返回正确结果 |

---

## 可观测性

### 日志

日志同时输出到三个目标：

| 输出 | 格式 | 级别 | 轮转策略 |
|------|------|------|----------|
| stdout | 由 `JSON_LOGS` 控制 | 配置级别 | - |
| `logs/app.log` | JSON | 配置级别 | 50MB x 10 份 |
| `logs/app.log.wf` | JSON | WARNING+ | 50MB x 10 份 |

日志自动包含以下字段：

```json
{
  "event": "request_completed",
  "request_id": "a1b2c3d4-...",
  "timestamp": "2026-02-17T08:00:00.000000Z",
  "level": "info",
  "method": "POST",
  "path": "/mcp/",
  "status_code": 200,
  "latency_ms": 12.5,
  "filename": "main.py",
  "lineno": 102,
  "func_name": "add_request_id_middleware"
}
```

### Prometheus 指标

访问 `/metrics` 获取，包含：

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `mcp_tool_execution_seconds` | Histogram | tool_name | 工具执行耗时 |
| `mcp_tool_execution_total` | Counter | tool_name, status | 工具执行计数 (success/error) |
| `mcp_tool_errors_total` | Counter | tool_name, error_type | 工具错误计数 |
| `http_requests_total` | Counter | method, status, handler | HTTP 请求总数 |
| `http_request_duration_seconds` | Histogram | method, handler | HTTP 请求耗时 |

### 请求追踪

- 每个请求自动生成 `X-Request-ID`（UUID v4），或透传客户端传入的
- 通过 `structlog.contextvars` 绑定，整个请求链路的所有日志自动携带
- 响应头中返回 `X-Request-ID`，便于客户端关联

---

## 部署

### Docker

```bash
docker build -t fastapi-mcp-server .
docker run -d \
  -p 8007:8000 \
  -e MCP_API_KEY=production-secret-key \
  -e LOG_LEVEL=INFO \
  -e JSON_LOGS=true \
  -v $(pwd)/logs:/app/logs \
  fastapi-mcp-server
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: server
        image: your-registry/fastapi-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          periodSeconds: 10
```

---

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI | >= 0.104 |
| MCP SDK | mcp (FastMCP) | >= 1.0 |
| HTTP 客户端 | httpx | >= 0.25 |
| 结构化日志 | structlog | >= 23.2 |
| 配置管理 | pydantic-settings | >= 2.1 |
| 监控指标 | prometheus-client | >= 0.19 |
| 重试机制 | tenacity | >= 8.2 |
| ASGI 服务器 | uvicorn | >= 0.24 |

---

## 许可证

MIT License

## 参考文档

- [MCP 规范 (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [FastMCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [项目设计文档](./docs/design.md)
