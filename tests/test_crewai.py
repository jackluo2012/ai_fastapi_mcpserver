"""
MCP 服务器集成测试
分两部分：
  1. 直接 HTTP/JSON-RPC 调用 MCP 端点，验证 tools/resources/prompts 注册和执行
  2. 通过 CrewAI Agent 调用 MCP 工具，验证端到端链路

运行前：
  1）启动服务 python -m app.main
  2）设置 OPENAI_API_KEY（CrewAI 部分需要 LLM）

运行方式：
  pytest tests/test_crewai.py -v -s
  或 python tests/test_crewai.py
"""
import json
import os
import sys
import urllib.request

# 绕过系统代理：macOS 系统代理（如 Clash）会导致 CrewAI 内部 httpx 请求 localhost 被拦截返回 502
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")

import pytest

# ---------- 通用配置 ----------
# 集成测试连接实际运行的服务器，需要使用服务器的真实 API Key。
# conftest.py 会将 MCP_API_KEY 覆盖为测试值，因此这里直接从 .env 读取。
def _load_env_value(key: str, default: str) -> str:
    """从项目 .env 文件读取配置，忽略 conftest 对环境变量的覆盖。"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return default


MCP_API_KEY = _load_env_value("MCP_API_KEY", "kkk")
_server_port = _load_env_value("PORT", "8007")
MCP_URL = os.getenv("MCP_URL", f"http://127.0.0.1:{_server_port}/mcp/").rstrip("/") + "/"
HEALTH_URL = MCP_URL.replace("/mcp/", "/health")

# 预期注册的工具、资源、提示词
EXPECTED_TOOLS = {"hello_world", "echo", "get_server_info", "fetch_external_data"}
EXPECTED_RESOURCES = {"server_info", "server_status"}
EXPECTED_PROMPTS = {"code_review", "data_analysis"}

# 绕过系统代理（macOS 可能配置了 HTTP 代理导致 localhost 请求被拦截为 502）
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _mcp_request(method: str, params: dict = None, req_id: int = 1) -> dict:
    """发送 JSON-RPC 请求到 MCP 端点，返回解析后的 JSON 响应。
    服务器可能返回 application/json 或 text/event-stream（SSE），需兼容处理。
    """
    body = json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": req_id}
    ).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {MCP_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    with _opener.open(req, timeout=15) as resp:
        assert resp.getcode() == 200, f"MCP 请求 {method} 返回非 200: {resp.getcode()}"
        raw = resp.read().decode("utf-8")

    # 兼容 SSE 格式：提取 "data: {...}" 行中的 JSON
    if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                return json.loads(line[len("data:"):].strip())
        raise ValueError(f"SSE 响应中未找到 data 行: {raw[:300]}")
    return json.loads(raw)


def _health_check() -> dict:
    """调用 /health 端点确认服务运行中。"""
    req = urllib.request.Request(HEALTH_URL, method="GET")
    with _opener.open(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ========================================================================
# Part 1: 直接 MCP 协议测试（不依赖 LLM / CrewAI）
# ========================================================================

class TestMCPProtocol:
    """直接通过 JSON-RPC 验证 MCP 服务端各项功能"""

    def test_health_endpoint(self):
        """校验点 1：/health 返回正常状态"""
        data = _health_check()
        assert data["status"] == "ok", f"健康检查状态异常: {data}"
        assert "version" in data
        assert "service" in data
        print(f"  [PASS] /health -> status={data['status']}, version={data['version']}")

    def test_tools_list(self):
        """校验点 2：tools/list 返回所有预期工具"""
        resp = _mcp_request("tools/list")
        tools = resp.get("result", {}).get("tools", [])
        tool_names = {t["name"] for t in tools}

        assert tool_names >= EXPECTED_TOOLS, (
            f"缺少工具: {EXPECTED_TOOLS - tool_names}, 实际: {tool_names}"
        )
        # 验证每个工具都有 description 和 inputSchema
        for t in tools:
            assert t.get("description"), f"工具 {t['name']} 缺少 description"
            assert t.get("inputSchema"), f"工具 {t['name']} 缺少 inputSchema"
        print(f"  [PASS] tools/list -> {len(tools)} 个工具: {sorted(tool_names)}")

    def test_resources_list(self):
        """校验点 3：resources/list 返回所有预期资源"""
        resp = _mcp_request("resources/list")
        resources = resp.get("result", {}).get("resources", [])
        resource_names = {r["name"] for r in resources}

        assert resource_names >= EXPECTED_RESOURCES, (
            f"缺少资源: {EXPECTED_RESOURCES - resource_names}, 实际: {resource_names}"
        )
        print(f"  [PASS] resources/list -> {len(resources)} 个资源: {sorted(resource_names)}")

    def test_prompts_list(self):
        """校验点 4：prompts/list 返回所有预期提示词"""
        resp = _mcp_request("prompts/list")
        prompts = resp.get("result", {}).get("prompts", [])
        prompt_names = {p["name"] for p in prompts}

        assert prompt_names >= EXPECTED_PROMPTS, (
            f"缺少提示词: {EXPECTED_PROMPTS - prompt_names}, 实际: {prompt_names}"
        )
        print(f"  [PASS] prompts/list -> {len(prompts)} 个提示词: {sorted(prompt_names)}")

    def test_tool_call_hello_world(self):
        """校验点 5：tools/call hello_world 正确返回问候语"""
        resp = _mcp_request(
            "tools/call",
            {"name": "hello_world", "arguments": {"name": "测试用户"}},
            req_id=10,
        )
        content = resp.get("result", {}).get("content", [])
        assert len(content) > 0, f"hello_world 未返回内容: {resp}"

        text = content[0].get("text", "")
        assert "测试用户" in text, f"返回内容不包含用户名: {text}"
        assert "Hello" in text, f"返回内容不包含 Hello: {text}"
        print(f"  [PASS] tools/call hello_world -> {text}")

    def test_tool_call_echo(self):
        """校验点 6：tools/call echo 精确回显"""
        echo_msg = "MCP集成测试回显消息_12345"
        resp = _mcp_request(
            "tools/call",
            {"name": "echo", "arguments": {"text": echo_msg}},
            req_id=11,
        )
        content = resp.get("result", {}).get("content", [])
        assert len(content) > 0, f"echo 未返回内容: {resp}"

        text = content[0].get("text", "")
        assert text == echo_msg, f"echo 不精确: 期望 '{echo_msg}', 实际 '{text}'"
        print(f"  [PASS] tools/call echo -> {text}")

    def test_tool_call_get_server_info(self):
        """校验点 7：tools/call get_server_info 返回有效服务器信息"""
        resp = _mcp_request(
            "tools/call",
            {"name": "get_server_info", "arguments": {}},
            req_id=12,
        )
        content = resp.get("result", {}).get("content", [])
        assert len(content) > 0, f"get_server_info 未返回内容: {resp}"

        text = content[0].get("text", "")
        info = json.loads(text)
        assert "project_name" in info, f"缺少 project_name: {info}"
        assert "version" in info, f"缺少 version: {info}"
        assert "timestamp" in info, f"缺少 timestamp: {info}"
        assert info["project_name"] == "Enterprise MCP Server"
        print(f"  [PASS] tools/call get_server_info -> v{info['version']}, ts={info['timestamp']}")

    def test_resource_read_server_info(self):
        """校验点 8：resources/read 读取 server-info 资源"""
        resp = _mcp_request(
            "resources/read",
            {"uri": "resource://server-info"},
            req_id=20,
        )
        contents = resp.get("result", {}).get("contents", [])
        assert len(contents) > 0, f"server-info 资源未返回内容: {resp}"

        text = contents[0].get("text", "")
        info = json.loads(text)
        assert info["project_name"] == "Enterprise MCP Server"
        assert "mcp_endpoint" in info
        print(f"  [PASS] resources/read server-info -> {info['project_name']}")

    def test_resource_read_server_status(self):
        """校验点 9：resources/read 读取 server-status 资源"""
        resp = _mcp_request(
            "resources/read",
            {"uri": "resource://server-status"},
            req_id=21,
        )
        contents = resp.get("result", {}).get("contents", [])
        assert len(contents) > 0, f"server-status 资源未返回内容: {resp}"

        text = contents[0].get("text", "")
        status = json.loads(text)
        assert status["status"] == "running"
        assert "timestamp" in status
        print(f"  [PASS] resources/read server-status -> {status['status']}")

    def test_prompt_get_code_review(self):
        """校验点 10：prompts/get 获取 code_review 提示词"""
        resp = _mcp_request(
            "prompts/get",
            {"name": "code_review", "arguments": {"code": "print('hi')", "language": "python"}},
            req_id=30,
        )
        messages = resp.get("result", {}).get("messages", [])
        assert len(messages) > 0, f"code_review 提示词未返回消息: {resp}"

        text = messages[0].get("content", {}).get("text", "")
        assert "python" in text, f"提示词未包含 language: {text[:100]}"
        assert "print('hi')" in text, f"提示词未包含 code: {text[:100]}"
        print(f"  [PASS] prompts/get code_review -> {len(text)} chars")

    def test_auth_rejected_without_key(self):
        """校验点 11：无 API Key 时 MCP 端点返回 403"""
        body = json.dumps(
            {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 99}
        ).encode("utf-8")
        req = urllib.request.Request(
            MCP_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with _opener.open(req, timeout=5) as resp:
                pytest.fail(f"应返回 403，但返回了 {resp.getcode()}")
        except urllib.error.HTTPError as e:
            assert e.code == 403, f"期望 403，实际 {e.code}"
            print(f"  [PASS] 无 API Key -> 403 Forbidden")


# ========================================================================
# Part 2: CrewAI Agent 端到端测试（需要 LLM）
# ========================================================================

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="未设置 OPENAI_API_KEY，CrewAI Agent 需要 LLM",
)
class TestCrewAIIntegration:
    """通过 CrewAI Agent 调用 MCP 工具的端到端测试"""

    def test_crewai_hello_world(self):
        """校验点 12：CrewAI Agent 调用 hello_world 工具并返回包含用户名的结果"""
        from crewai import Agent, Crew, Task
        from crewai.llm import LLM
        from crewai.mcp import MCPServerHTTP

        llm = LLM(
            model="qwen-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
        )

        # CrewAI 从 URL 派生 OpenAI function name，需用 localhost（字母开头）而非 127.0.0.1（数字开头）
        crewai_mcp_url = MCP_URL.replace("127.0.0.1", "localhost")

        agent = Agent(
            role="MCP Agent",
            goal="Use the MCP hello_world tool to greet the user by name. You MUST call the hello_world tool and return its exact output.",
            backstory="你是一个通过 MCP 调用远程工具的助手，负责根据用户输入调用合适的 MCP 工具并返回结果。",
            llm=llm,
            mcps=[
                MCPServerHTTP(
                    url=crewai_mcp_url,
                    headers={"Authorization": "Bearer " + MCP_API_KEY},
                    streamable=True,
                    cache_tools_list=True,
                ),
            ],
        )

        task = Task(
            description=(
                "请使用 hello_world 工具，传入用户的名字来问候用户。"
                "用户的名字是：张三。"
                "请直接返回工具的输出结果，不要修改。"
            ),
            expected_output="包含 '张三' 的问候语",
            agent=agent,
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff(inputs={"user_input": "张三"})

        # 基本断言：结果不为空
        assert result is not None, "CrewAI 返回了 None"
        result_str = str(result)
        assert len(result_str) > 0, "CrewAI 返回了空结果"

        # 核心断言：结果中应包含用户名（LLM 应该调用了 hello_world 并返回结果）
        assert "张三" in result_str, (
            f"结果中未包含用户名 '张三'，实际结果: {result_str[:200]}"
        )
        print(f"  [PASS] CrewAI hello_world -> {result_str[:150]}")


# ========================================================================
# 命令行入口
# ========================================================================

if __name__ == "__main__":
    # 先运行直接协议测试
    print("=" * 60)
    print("Part 1: MCP 协议直接测试")
    print("=" * 60)

    protocol_tests = TestMCPProtocol()
    test_methods = [m for m in dir(protocol_tests) if m.startswith("test_")]
    passed = 0
    failed = 0
    for method_name in sorted(test_methods):
        try:
            getattr(protocol_tests, method_name)()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {method_name}: {e}")
            failed += 1

    print(f"\nPart 1 结果: {passed} 通过, {failed} 失败")

    # CrewAI 端到端测试
    print("\n" + "=" * 60)
    print("Part 2: CrewAI Agent 端到端测试")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("  [SKIP] 未设置 OPENAI_API_KEY")
    else:
        try:
            crewai_tests = TestCrewAIIntegration()
            crewai_tests.test_crewai_hello_world()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] test_crewai_hello_world: {e}")
            failed += 1

    print(f"\n总结: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)
