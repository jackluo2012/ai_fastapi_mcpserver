# MCP Server 开发实战 —— 教学演讲逐字稿

> 配套课程大纲：[COURSE_OUTLINE.md](./COURSE_OUTLINE.md)
> 时长：约 20 分钟 | 建议配合屏幕录制，在 IDE + 终端之间切换演示

---

## 第一章：开场与背景

### 1.1 课程目标

大家好，欢迎来到 MCP Server 开发实战课程。

在接下来大约 20 分钟的时间里，我会带大家学会一件事：**用我们这个框架，快速开发一个可以被 AI Agent 调用的 MCP Server**。

课程结束后，你将能够独立开发 MCP 的三种核心能力：Tool、Resource 和 Prompt。整个过程非常简单，核心就是"写一个函数，加一个装饰器"。

### 1.2 什么是 MCP

那首先我们来理解一个概念：什么是 MCP？

MCP，全称 Model Context Protocol，是 Anthropic 在 2024 年底提出的一个开放协议。你可以把它理解成 **AI 世界的 USB 接口**。

我们知道，大语言模型，无论是 GPT、Claude 还是通义千问，它们本身只能处理文本。它们不能查数据库，不能调 API，不能操作文件系统。MCP 就是解决这个问题的。它定义了一套标准协议，让 AI Agent 可以通过这个协议去调用外部的工具和数据。

### 1.3 为什么需要 MCP Server

打个比方：大语言模型是一个很聪明的大脑，但它没有手脚。而 MCP Server 就是给这个大脑装上手脚。

当你开发了一个 MCP Server，并且在上面注册了工具，任何支持 MCP 协议的 AI Agent——比如 Claude Desktop、CrewAI、Cursor——都可以直接调用你的工具。你写一次，到处可用。

### 1.4 MCP 的三种能力

MCP 协议定义了三种核心能力，这也是我们今天要学的三样东西：

第一种是 **Tool**，工具。这是最常用的，就是让 AI 可以执行某个动作。比如查天气、发邮件、操作数据库。AI Agent 会自主决定什么时候调用哪个工具。

第二种是 **Resource**，资源。这是让 AI 可以读取的数据。比如你的数据库表结构、配置文件、API 文档。它是只读的，类似于一个 GET 接口。

第三种是 **Prompt**，提示词模板。这是预定义的、可参数化的提示词。比如"代码审查模板"、"SQL 生成模板"。AI Agent 可以获取这些模板，填入参数后使用。

好，概念就讲这么多。接下来我们直接动手。

---

## 第二章：项目启动演示

### 2.1 环境准备

> 【切换到终端】

我们先把项目跑起来。假设你已经克隆了项目代码。

首先创建虚拟环境，激活，然后安装依赖：

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.2 配置环境变量

然后我们需要配置一下环境变量。复制一份模板文件：

```bash
cp .env.example .env
```

打开 `.env` 文件，这里面最关键的是 `MCP_API_KEY`，这是 MCP 端点的鉴权密钥。我们设成一个测试值，比如 `my-secret-key`。其他配置暂时用默认值就行。

```
MCP_API_KEY=my-secret-key
PORT=8007
```

### 2.3 启动服务

现在启动服务：

```bash
python -m app.main
```

> 【等待启动日志出现】

可以看到控制台输出了启动日志：`application_started`，服务跑在 8007 端口上。注意看这些日志都是结构化的 JSON 格式，包含时间戳、事件名、文件名、行号，这些在排查问题的时候非常有用。

### 2.4 调用 MCP 工具

> 【新开一个终端标签页】

现在我们来调用 MCP 端点。先列出所有注册的工具：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

> 【展示返回结果】

可以看到返回了四个工具：`hello_world`、`echo`、`get_server_info`、`fetch_external_data`。每个工具都有名称、描述和输入参数的 JSON Schema。

现在我们来调用 `hello_world`：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"hello_world","arguments":{"name":"同学们"}},"id":2}'
```

返回了：`Hello, 同学们! Enterprise MCP Server is running.`。工具调用成功了。

### 2.5 调用资源和提示词

同样的方式，我们可以读取资源：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"resources/list","params":{},"id":3}'
```

返回了两个资源：`server_info` 和 `server_status`。

再看提示词：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"prompts/list","params":{},"id":4}'
```

返回了两个提示词模板：`code_review` 和 `data_analysis`。

好，我们的服务跑通了，三种能力都工作正常。接下来我们来理解一下这个框架的整体架构。

---

## 第三章：架构全景

### 3.1 分层架构

> 【切换到 IDE，打开 README.md 的架构图部分】

我们的框架采用经典的四层架构。从上到下看：

最上面是**接口层**，就是 `app/main.py`。它负责 HTTP 中间件，包括 CORS 跨域、请求 ID 生成、耗时统计、Prometheus 指标采集。这些你都不用管，框架帮你处理好了。

第二层是**协议层**，在 `app/mcp_server/` 目录下。这里做两件事：一是 API Key 鉴权，所有到 `/mcp/` 的请求都必须带合法的 API Key，否则直接返回 403。二是把请求交给 MCP SDK 处理，SDK 负责 JSON-RPC 协议的解析和路由。

第三层是**业务层**，在 `app/tools/` 目录下。**这就是你作为开发者主要工作的地方。** 你的工具、资源、提示词都写在这里。

最底层是**基础设施层**，包括配置管理、日志系统、HTTP 客户端、监控指标。这些都是框架提供的通用能力。

### 3.2 请求处理流程

我来描述一个请求的完整旅程。当 AI Agent 发一个 POST 请求到 `/mcp/`：

首先经过 CORS 中间件，然后 Request-ID 中间件会生成一个唯一的请求 ID 并绑定到日志上下文——这意味着这个请求后续产生的所有日志，都会自动带上这个 ID，方便追踪。

然后请求到达 MCP 传输层，这里会校验 API Key。校验通过后，请求进入 MCP SDK，SDK 解析 JSON-RPC 请求体，根据 method 字段分发到对应的处理函数——你注册的工具、资源或提示词。

你的函数执行完毕后，结果原路返回，最终作为 HTTP 响应发回给客户端。

### 3.3 开发者只需关注 app/tools/

> 【在 IDE 中展开 app/tools/ 目录】

再说一遍重点：作为开发者，你日常工作只涉及一个目录——`app/tools/`。这里面有五个文件：

- `base.py` —— 装饰器定义，你不需要改它
- `demo.py` —— 演示工具，hello_world 和 echo
- `system.py` —— 系统工具，获取服务器信息、调用外部 API
- `resources.py` —— MCP 资源定义
- `prompts.py` —— MCP 提示词模板

### 3.4 框架帮你做了什么

你可能会问，那框架帮我做了什么？我列几个关键的：

**第一，安全鉴权。** 所有 MCP 请求自动验证 API Key，无需你写任何鉴权代码。

**第二，结构化日志。** 每条日志自动包含时间戳、请求 ID、文件名、行号。日志同时写入控制台和文件，WARNING 以上的还会单独写一份 `.wf` 文件。

**第三，Prometheus 监控。** 每个工具的执行次数、耗时、错误率，自动采集到 Prometheus 指标中。

**第四，HTTP 客户端。** 内置了带连接池和自动重试的异步 HTTP 客户端，你需要调外部 API 的时候直接用就行。

好，架构就讲到这。接下来我们进入代码阅读环节。

---

## 第四章：读懂现有代码

### 4.1 MCP 实例初始化

> 【打开 app/mcp_server/app.py】

我们先看这个文件，它是整个 MCP 服务器的入口。

```python
mcp = FastMCP(
    "Enterprise-Demo-MCP",
    streamable_http_path="/",
    stateless_http=True,
)
```

这里创建了一个 FastMCP 实例。`stateless_http=True` 是一个关键配置——它表示我们的服务是无状态的，客户端不需要先发 `initialize` 请求，可以直接调用 `tools/list`、`tools/call`。这对于 HTTP 部署来说非常方便。

然后看下面两行：

```python
mcp_tool = create_mcp_tool_decorator(mcp)
from app.tools import demo, system, resources, prompts
```

第一行创建了我们的 `@mcp_tool` 装饰器。第二行导入了所有工具模块。注意，**必须在 mcp 实例创建之后再导入工具模块**，因为工具模块在被导入时会执行装饰器，把工具注册到 mcp 实例上。

这就是"导入即注册"的模式。所以当你新增了一个工具模块，只需要在这行导入语句中加上你的模块名就行了。

### 4.2 @mcp_tool 装饰器

> 【打开 app/tools/base.py】

我们来看 `@mcp_tool` 装饰器做了什么。核心就这几行：

```python
def decorator(func):
    # 先应用监控装饰器
    monitored_func = track_tool_execution(tool_name=name)(func)
    # 再应用MCP工具装饰器
    return mcp_instance.tool(name=name, description=description)(monitored_func)
```

它做了两件事：第一，包了一层 Prometheus 监控——你的工具每次被调用，执行时间、成功还是失败，都会自动记录。第二，调用 MCP SDK 的 `mcp.tool()` 把函数注册为 MCP 工具。

所以 `@mcp_tool` 这一个装饰器，帮你同时完成了"注册"和"监控"两件事。

### 4.3 hello_world 工具

> 【打开 app/tools/demo.py】

现在来看一个最简单的工具实现：

```python
from app.mcp_server.app import mcp_tool

@mcp_tool(
    name="hello_world",
    description="基础连通性测试工具，返回问候语",
)
async def hello_world(name: str = "World") -> str:
    logger.info("executing_hello_world", user_name=name)
    return f"Hello, {name}! Enterprise MCP Server is running."
```

就这么简单。我来拆解一下：

**第一行**，从 `mcp_server.app` 导入 `mcp_tool` 装饰器。

**装饰器参数**，`name` 是工具在 MCP 协议中的名称，AI Agent 调用时用这个名字。`description` 是工具描述，AI Agent 靠这个描述来决定什么时候该调用这个工具，所以描述要写清楚。

**函数签名**，参数 `name: str = "World"` 会自动生成 JSON Schema，告诉 AI Agent 这个工具接受一个字符串参数 `name`，默认值是 `World`。类型标注非常重要，MCP 客户端依赖它来知道怎么传参。

**返回值**，直接返回字符串就行，框架会帮你序列化成 MCP 响应格式。

### 4.4 Resource 资源

> 【打开 app/tools/resources.py】

再看资源的写法：

```python
from app.mcp_server.app import mcp

@mcp.resource(
    "resource://server-info",
    name="server_info",
    description="服务器基本信息和配置",
)
async def server_info_resource() -> str:
    info = {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        ...
    }
    return json.dumps(info, ensure_ascii=False, indent=2)
```

注意两个区别：第一，资源用的是 `@mcp.resource` 而不是 `@mcp_tool`。第二，装饰器的第一个参数是 URI，格式是 `resource://你的资源名`。第三，返回值必须是字符串，一般我们返回 JSON 字符串。

### 4.5 Prompt 提示词

> 【打开 app/tools/prompts.py】

提示词的写法：

```python
@mcp.prompt(name="code_review", description="代码审查提示词模板")
async def code_review_prompt(code: str, language: str = "python") -> str:
    return (
        f"请对以下 {language} 代码进行审查...\n"
        f"代码：\n```{language}\n{code}\n```"
    )
```

提示词用 `@mcp.prompt` 装饰器。函数的参数就是模板参数——这里 `code` 和 `language` 会变成 MCP 客户端在 `prompts/get` 时需要传入的参数。返回值是渲染后的完整提示词文本。

好，现有代码我们都过了一遍。现在进入最重要的环节——实战开发。

---

## 第五章：实战——开发一个 Tool

### 5.1 需求

假设我们要开发一个"城市天气查询"工具。AI Agent 传入一个城市名，我们返回天气信息。当然，在真实场景中你会调用真正的天气 API，这里我们用模拟数据来演示。

### 5.2 创建模块

> 【在 IDE 中右键 app/tools/ 目录，新建文件 weather.py】

在 `app/tools/` 下创建一个新文件 `weather.py`：

```python
"""
天气查询工具模块
"""
from app.core.logging import get_logger
from app.mcp_server.app import mcp_tool

logger = get_logger()

# 模拟天气数据（实际开发中替换为真实 API 调用）
MOCK_WEATHER = {
    "北京": {"temperature": 5, "humidity": 35, "description": "晴"},
    "上海": {"temperature": 12, "humidity": 65, "description": "多云"},
    "广州": {"temperature": 20, "humidity": 80, "description": "小雨"},
}


@mcp_tool(
    name="get_weather",
    description="查询指定城市的当前天气信息，包括温度、湿度和天气状况",
)
async def get_weather(city: str) -> dict:
    """
    查询天气信息

    Args:
        city: 城市名称，例如"北京"、"上海"
    """
    logger.info("querying_weather", city=city)

    weather = MOCK_WEATHER.get(city)
    if not weather:
        return {"error": f"暂不支持城市：{city}", "supported": list(MOCK_WEATHER.keys())}

    return {
        "city": city,
        "temperature": weather["temperature"],
        "humidity": weather["humidity"],
        "description": weather["description"],
        "unit": "celsius",
    }
```

我来讲几个要点：

第一，导入 `mcp_tool` 装饰器和 `get_logger`。这是固定写法，每个工具模块都一样。

第二，`@mcp_tool` 的 `description` 参数要写得详细。AI Agent 是根据这个描述来判断何时调用你的工具的。如果描述写得含糊，AI 可能就不会正确调用。

第三，函数参数 `city: str` 必须有类型标注。这个类型标注会被 MCP SDK 自动转成 JSON Schema，告诉客户端应该传什么类型的参数。

第四，返回值可以是 `dict`、`str`、`list` 等任何可 JSON 序列化的类型。框架会帮你处理序列化。

### 5.3 注册模块

> 【打开 app/mcp_server/app.py】

文件写好了，但现在 MCP 服务器还不知道它的存在。我们需要在 `app/mcp_server/app.py` 中注册。

找到导入行，加上 `weather`：

```python
from app.tools import demo, system, resources, prompts, weather
```

就加这一个单词，`weather`。

### 5.4 验证

> 【切换到终端】

现在重启服务：

```bash
# Ctrl+C 停掉旧服务，然后重新启动
python -m app.main
```

然后验证。先看工具列表里有没有我们新加的：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

可以看到，工具列表里多了一个 `get_weather`，description 和 inputSchema 都自动生成好了。

现在调用它：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_weather","arguments":{"city":"北京"}},"id":2}'
```

返回了：北京，温度 5 度，湿度 35%，晴。完美。

### 5.5 总结三步曲

我们来回顾一下。开发一个 MCP Tool 只需要三步：

**第一步**，在 `app/tools/` 下写一个 async 函数，加上 `@mcp_tool` 装饰器。

**第二步**，在 `app/mcp_server/app.py` 的导入行加上你的模块名。

**第三步**，重启服务，完成。

就这么简单。你的工具自动获得了 MCP 注册、Prometheus 监控指标、结构化日志——全都是框架帮你做的。

---

## 第六章：实战——开发 Resource 和 Prompt

### 6.1 三种能力对比

在开发之前，我先帮大家区分一下这三种能力适用的场景：

**Tool** 是"动作"。AI Agent 调用它来执行操作——查数据库、发请求、写文件。它有输入参数，会产生副作用。

**Resource** 是"数据"。AI Agent 读取它来获取信息——表结构、配置文件、API 文档。它是只读的，没有输入参数（只有 URI），适合提供上下文信息。

**Prompt** 是"模板"。AI Agent 获取它来得到预定义的提示词——代码审查模板、报告生成模板。它有参数，但返回的是提示词文本，不是执行结果。

简单记忆：Tool 让 AI "做事"，Resource 让 AI "看数据"，Prompt 让 AI "知道怎么说"。

### 6.2 开发一个 Resource

> 【在 app/tools/resources.py 末尾追加代码】

我们在 `resources.py` 文件末尾加一个新资源：

```python
@mcp.resource(
    "resource://api-docs",
    name="api_docs",
    description="系统 API 接口文档",
)
async def api_docs_resource() -> str:
    """返回系统的 API 接口文档"""
    docs = {
        "endpoints": [
            {"path": "/health", "method": "GET", "description": "健康检查"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus 指标"},
            {"path": "/mcp/", "method": "POST", "description": "MCP JSON-RPC 端点"},
        ],
        "auth": "Bearer Token via Authorization header",
    }
    logger.info("resource_accessed", resource="api_docs")
    return json.dumps(docs, ensure_ascii=False, indent=2)
```

注意，资源用的装饰器是 `@mcp.resource`——这里的 `mcp` 是直接从 `app.mcp_server.app` 导入的 FastMCP 实例，不是 `mcp_tool`。

因为我们是在已有的 `resources.py` 文件里加代码，这个文件已经在 `app.py` 中注册过了，所以不需要再改导入行。

### 6.3 开发一个 Prompt

> 【在 app/tools/prompts.py 末尾追加代码】

同样，在 `prompts.py` 末尾加一个新提示词：

```python
@mcp.prompt(name="bug_analysis", description="Bug 分析提示词模板")
async def bug_analysis_prompt(
    error_message: str,
    stack_trace: str = "",
    context: str = "",
) -> str:
    """
    生成 Bug 分析提示词

    Args:
        error_message: 错误信息
        stack_trace: 堆栈跟踪（可选）
        context: 补充上下文（可选）
    """
    logger.info("prompt_accessed", prompt="bug_analysis")
    prompt = f"请分析以下 Bug 并提供修复建议：\n\n"
    prompt += f"错误信息：{error_message}\n"
    if stack_trace:
        prompt += f"\n堆栈跟踪：\n```\n{stack_trace}\n```\n"
    if context:
        prompt += f"\n补充上下文：{context}\n"
    prompt += "\n请从以下角度分析：\n"
    prompt += "1. 根本原因\n2. 影响范围\n3. 修复方案\n4. 预防措施"
    return prompt
```

同样的，提示词用 `@mcp.prompt` 装饰器。函数参数就是模板参数。返回纯文本字符串。

### 6.4 验证

> 【终端演示】

重启服务后，验证资源：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"resource://api-docs"},"id":1}'
```

返回了我们定义的 API 文档内容。

验证提示词：

```bash
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"prompts/get","params":{"name":"bug_analysis","arguments":{"error_message":"KeyError: user_id","stack_trace":"File app.py line 42"}},"id":2}'
```

返回了渲染好的 Bug 分析提示词，包含了我们传入的错误信息和堆栈。

好，三种能力我们都开发并验证过了。

---

## 第七章：测试与验证

### 7.1 单元测试

> 【打开 tests/test_tools.py】

我们的框架自带了完善的测试套件。对于工具的单元测试非常简单，因为工具函数本质上就是普通的 async 函数：

```python
@pytest.mark.asyncio
async def test_hello_world():
    result = await demo.hello_world("Test")
    assert "Hello" in result
    assert "Test" in result
```

直接 await 调用，然后做断言就行。

如果你的工具调用了外部 API，可以用 `unittest.mock` 来 mock：

```python
@pytest.mark.asyncio
async def test_fetch_data():
    with patch("app.utils.http_client.http_client._client") as mock:
        mock.get = AsyncMock(return_value=mock_response)
        result = await system.fetch_external_data("https://api.example.com")
        assert "data" in result
```

### 7.2 集成测试

> 【打开 tests/test_crewai.py】

我们还提供了集成测试文件 `test_crewai.py`，里面有 12 个校验点，覆盖了 MCP 协议的所有关键功能：

工具列表、资源列表、提示词列表、工具调用、资源读取、提示词获取、鉴权拒绝——全部都有验证。

这些测试分成两部分。第一部分是协议测试，直接通过 HTTP 调用 MCP 端点，不需要 LLM，非常快：

### 7.3 运行测试

> 【终端演示】

```bash
pytest tests/test_crewai.py::TestMCPProtocol -v -s
```

> 【展示 11 passed 结果】

11 个协议测试全部通过。每个 `[PASS]` 后面都显示了具体验证的内容。

### 7.4 CrewAI 端到端验证

第二部分是 CrewAI Agent 测试。它会启动一个真正的 AI Agent，让它通过 MCP 协议调用我们的工具。这需要配置 LLM API Key。

如果配置好了 `OPENAI_API_KEY`，运行全部测试就能看到 AI Agent 自主调用 `hello_world` 工具并返回正确结果。这个就不现场演示了，大家可以课后按照 README 中的说明自行验证。

---

## 第八章：总结与进阶

### 8.1 回顾

好，我们来做一个快速的回顾。今天我们学了什么？

开发一个 MCP 能力，标准流程就四步：

第一，在 `app/tools/` 下写一个 async 函数。Tool 用 `@mcp_tool`，Resource 用 `@mcp.resource`，Prompt 用 `@mcp.prompt`。

第二，如果是新文件，在 `app/mcp_server/app.py` 的导入行加上模块名。

第三，重启服务。

第四，用 curl 或测试用例验证。

就这么简单。

### 8.2 框架提供的企业级能力

虽然开发过程简单，但底下的框架帮你处理了大量企业级需求：

**安全方面**，API Key 鉴权、Origin 校验、恒定时间比较防时序攻击，这些全自动。

**可观测性方面**，Structlog 结构化日志、请求 ID 全链路追踪、Prometheus 工具粒度指标，开箱即用。

**可靠性方面**，httpx 连接池管理、Tenacity 指数退避重试、5 秒优雅关闭，全部内置。

**部署方面**，多阶段 Docker 构建、非 root 用户运行、健康检查端点，生产可用。

### 8.3 进阶方向

学完今天的基础之后，你可以往几个方向深入：

第一，**连接真实数据源**。比如在工具里接入数据库查询、调用第三方 API。框架内置的 `http_client` 已经帮你处理好了连接池和重试。

第二，**对接 AI Agent 框架**。我们的 MCP Server 可以直接被 CrewAI、LangChain、Claude Desktop 等任何支持 MCP 协议的 Agent 调用。

第三，**阅读设计文档**。`docs/design.md` 里有详细的架构设计说明，帮助你理解框架的每一个设计决策。

### 8.4 课程结束

好，今天的课程就到这里。核心就一句话：**写一个函数，加一个装饰器，你就拥有了一个可以被全世界 AI Agent 调用的能力。**

感谢大家的观看，有问题可以在项目的 Issue 中提出。祝大家开发顺利。
