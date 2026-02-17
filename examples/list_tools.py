#!/usr/bin/env python3
"""
示例：通过 HTTP 直接调用 MCP 服务器的工具列表和工具执行

运行方式：
    1. 先启动服务：python -m app.main
    2. 运行本脚本：python examples/list_tools.py

环境变量：
    MCP_URL: MCP 服务地址（默认 http://localhost:8000/mcp/）
    MCP_API_KEY: API Key（默认 your-secret-api-key-here-change-in-production）
"""
import json
import os
import sys
import urllib.request

# MCP 服务地址（必须带末尾斜杠）
MCP_URL = (
    os.getenv("MCP_URL", "http://localhost:8000/mcp/") or "http://localhost:8000/mcp/"
).rstrip("/") + "/"
MCP_API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key-here-change-in-production")


def mcp_request(method: str, params: dict = None, req_id: int = 1) -> dict:
    """发送 JSON-RPC 请求到 MCP 端点"""
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

    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print(f"MCP Server: {MCP_URL}")
    print("=" * 50)

    # 1. 列出所有工具
    print("\n1. 获取工具列表 (tools/list)")
    try:
        result = mcp_request("tools/list")
    except Exception as e:
        print(f"   请求失败（请确认服务已启动）: {e}")
        return 1

    tools = result.get("result", {}).get("tools", [])
    print(f"   找到 {len(tools)} 个工具:")
    for i, tool in enumerate(tools, 1):
        name = tool.get("name", "unknown")
        desc = tool.get("description", "")
        print(f"   {i}. {name}: {desc}")

    # 2. 调用 hello_world 工具
    print("\n2. 调用 hello_world 工具")
    try:
        result = mcp_request(
            "tools/call",
            {"name": "hello_world", "arguments": {"name": "FastMCP用户"}},
            req_id=2,
        )
        content = result.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", str(content[0]))
            print(f"   结果: {text}")
        else:
            print(f"   结果: {result}")
    except Exception as e:
        print(f"   调用失败: {e}")

    # 3. 调用 echo 工具
    print("\n3. 调用 echo 工具")
    try:
        result = mcp_request(
            "tools/call",
            {"name": "echo", "arguments": {"text": "Hello from example!"}},
            req_id=3,
        )
        content = result.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", str(content[0]))
            print(f"   结果: {text}")
    except Exception as e:
        print(f"   调用失败: {e}")

    print("\nOK: 所有示例执行完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
