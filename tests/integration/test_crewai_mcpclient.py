import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径，以便能够导入项目模块
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 绕过系统代理：macOS 可能配置了 HTTP 代理（如 Clash），导致 httpx 请求 localhost 被拦截返回 502
# CrewAI 内部使用 httpx，httpx 默认通过 urllib.request.getproxies() 读取系统代理设置
# 设置 NO_PROXY 使 httpx 对 localhost/127.0.0.1 跳过代理
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")

from crewai import Agent, Task, Crew
from crewai.mcp import MCPServerHTTP
from crewai.llm import LLM


def _load_env_value(key: str, default: str) -> str:
    """从项目 .env 文件读取配置值。"""
    env_path = os.path.join(str(project_root), ".env")
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return default


MCP_API_KEY = _load_env_value("MCP_API_KEY", "kkk")
_server_port = _load_env_value("PORT", "8007")
MCP_URL = f"http://localhost:{_server_port}/mcp/"

hello_agent = Agent(
    role="Hello Agent",
    goal="Say hello to the world",
    backstory="You are a helpful assistant that can use the hello_world tool to say hello to the world",
    mcps=[MCPServerHTTP(
        url=MCP_URL,
        headers={"Authorization": f"Bearer {MCP_API_KEY}"},
        streamable=True,
        cache_tools_list=True,
    )],
    llm=LLM(
        model="qwen-turbo",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
    ),
)

hello_task = Task(
    description="Say hello to the world, and the user input is {user_input}",
    expected_output="use the hello_world tool to say hello to the world",
    agent=hello_agent,
)

crew = Crew(
    agents=[hello_agent],
    tasks=[hello_task],
    verbose=True,
)

result = crew.kickoff(inputs={"user_input": "I'm Xiao"})
print(result)