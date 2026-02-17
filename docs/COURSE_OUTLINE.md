# MCP Server 开发实战课程大纲

> 时长：约 20 分钟 | 目标受众：有 Python 基础的开发者 | 教学目标：学会用本框架开发 MCP Server

---

## 第一章：开场与背景（2 分钟）

- **1.1** 课程目标：20 分钟学会开发一个可被 AI Agent 调用的 MCP Server
- **1.2** 什么是 MCP（Model Context Protocol）—— AI Agent 与外部工具的标准协议
- **1.3** 为什么需要 MCP Server —— 让 AI 获得"手脚"，调用真实世界的能力
- **1.4** MCP 的三种能力：Tool / Resource / Prompt

## 第二章：项目启动演示（3 分钟）

- **2.1** 环境准备：克隆项目、创建虚拟环境、安装依赖
- **2.2** 配置 `.env`，设置 `MCP_API_KEY`
- **2.3** 启动服务 `python -m app.main`
- **2.4** 现场演示：curl 调用 `tools/list` 和 `tools/call hello_world`
- **2.5** 现场演示：curl 调用 `resources/read` 和 `prompts/get`

## 第三章：架构全景（3 分钟）

- **3.1** 分层架构图讲解：接口层 → 协议层 → 业务层 → 基础设施层
- **3.2** 请求处理流程：一个 MCP 请求从进入到返回经历了什么
- **3.3** 核心目录结构：开发者只需关注 `app/tools/` 目录
- **3.4** 框架帮你做了什么：鉴权、日志、监控、重试——你只写业务代码

## 第四章：读懂现有代码（3 分钟）

- **4.1** `app/mcp_server/app.py`：MCP 实例初始化与模块注册机制
- **4.2** `app/tools/base.py`：`@mcp_tool` 装饰器——一行代码完成注册+监控
- **4.3** `app/tools/demo.py`：解读 `hello_world` 工具的完整实现
- **4.4** `app/tools/resources.py`：解读 `@mcp.resource` 资源注册
- **4.5** `app/tools/prompts.py`：解读 `@mcp.prompt` 提示词注册

## 第五章：实战——开发一个 Tool（4 分钟）

- **5.1** 需求：开发一个"城市天气查询"工具
- **5.2** 第一步：在 `app/tools/` 下创建 `weather.py`
- **5.3** 第二步：编写异步函数，添加 `@mcp_tool` 装饰器
- **5.4** 第三步：在 `app/mcp_server/app.py` 注册模块
- **5.5** 第四步：重启服务，curl 验证 `tools/list` 和 `tools/call`
- **5.6** 总结三步曲：写函数 → 加装饰器 → 注册导入

## 第六章：实战——开发 Resource 和 Prompt（3 分钟）

- **6.1** 三种能力对比：Tool = 动作执行，Resource = 数据读取，Prompt = 提示词模板
- **6.2** 实战：开发一个"API 文档"资源（`@mcp.resource`）
- **6.3** 实战：开发一个"Bug 分析"提示词（`@mcp.prompt`）
- **6.4** curl 验证 `resources/read` 和 `prompts/get`

## 第七章：测试与验证（2 分钟）

- **7.1** 单元测试：pytest + AsyncMock 测试工具函数
- **7.2** 集成测试：12 个校验点覆盖全部 MCP 协议
- **7.3** 现场运行 `pytest tests/test_crewai.py::TestMCPProtocol -v`
- **7.4** 用 CrewAI Agent 端到端验证（可选演示）

## 第八章：总结与进阶（1 分钟）

- **8.1** 回顾：开发 MCP 能力的标准流程
- **8.2** 框架提供的企业级能力：安全鉴权、结构化日志、Prometheus 监控、优雅关闭
- **8.3** 进阶方向：连接数据库、调用第三方 API、对接 CrewAI/LangChain
- **8.4** 课程结束

---

## 时间分配

| 章节 | 内容 | 时长 |
|------|------|------|
| 第一章 | 开场与背景 | 2 分钟 |
| 第二章 | 项目启动演示 | 3 分钟 |
| 第三章 | 架构全景 | 3 分钟 |
| 第四章 | 读懂现有代码 | 3 分钟 |
| 第五章 | 实战——开发 Tool | 4 分钟 |
| 第六章 | 实战——开发 Resource 和 Prompt | 3 分钟 |
| 第七章 | 测试与验证 | 2 分钟 |
| 第八章 | 总结与进阶 | 1 分钟 |
| **合计** | | **约 21 分钟** |
