"""
直接用 HTTP 调用本服务 MCP 端点，验证服务端正常（不依赖 CrewAI）。
需先启动服务：python -m app.main
"""
import json
import os
import sys
import urllib.request

# 必须带末尾斜杠
MCP_URL = (os.getenv("MCP_URL", "http://localhost:8007/mcp/") or "http://localhost:8007/mcp/").rstrip("/") + "/"
MCP_API_KEY = os.getenv("MCP_API_KEY", "kkk")


def main():
    body = json.dumps({"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}).encode("utf-8")
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
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.getcode()
            data = resp.read().decode("utf-8")
    except Exception as e:
        print("请求失败（请确认服务已启动且无代理干扰）:", e)
        return 1
    if code != 200:
        print("status:", code, "body:", data[:300])
        return 1
    assert "hello_world" in data or "result" in data, data[:300]
    print("OK: MCP 端点 POST tools/list 返回 200")
    return 0


if __name__ == "__main__":
    sys.exit(main())
