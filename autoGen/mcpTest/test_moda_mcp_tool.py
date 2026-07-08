import argparse
import asyncio
import os
import traceback
from typing import Any

from autogen_core import CancellationToken
from autogen_ext.tools.mcp import StreamableHttpServerParams, mcp_server_tools

try:
    BaseExceptionGroup
except NameError:
    from exceptiongroup import BaseExceptionGroup


def print_exception(exc: BaseException, indent: int = 0) -> None:
    prefix = " " * indent
    print(f"{prefix}{type(exc).__name__}: {exc}")

    if isinstance(exc, BaseExceptionGroup):
        for index, child in enumerate(exc.exceptions, start=1):
            print(f"{prefix}--- sub-exception {index} ---")
            print_exception(child, indent + 2)
        return

    print("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))


async def call_tool(tool: Any, args: dict[str, Any]) -> None:
    print(f"\n========== call {tool.name} ==========")
    print(f"args: {args}")

    try:
        result = await tool.run_json(args, CancellationToken())
    except BaseException as exc:
        print("tool call failed:")
        print_exception(exc)
        return

    print("tool call succeeded:")
    print(result)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Directly test ModelScope Jina MCP tools.")
    parser.add_argument("--url", default=os.getenv("MODELSCOPE_MCP_URL"), help="ModelScope MCP URL")
    parser.add_argument("--query", default="人工智能", help="Search query for jina_search")
    parser.add_argument("--count", type=int, default=5, help="Search result count")
    parser.add_argument(
        "--read-url",
        default="https://www.modelscope.cn/mcp/servers/@PsychArch/Jina-AI-MCP-Tools",
        help="URL for jina_reader",
    )
    args = parser.parse_args()

    if not args.url:
        raise RuntimeError("Missing MCP URL. Set MODELSCOPE_MCP_URL or pass --url.")

    server_params = StreamableHttpServerParams(
        url=args.url,
        timeout=30.0,
        sse_read_timeout=300.0,
        terminate_on_close=False,
    )

    tools = await mcp_server_tools(server_params)
    print(f"discovered {len(tools)} tools")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
        print(f"  schema: {tool.schema}")

    by_name = {tool.name: tool for tool in tools}

    if "jina_search" in by_name:
        await call_tool(by_name["jina_search"], {"query": args.query, "count": args.count})
    else:
        print("\njina_search not found")

    if "jina_reader" in by_name:
        await call_tool(by_name["jina_reader"], {"url": args.read_url})
    else:
        print("\njina_reader not found")


if __name__ == "__main__":
    asyncio.run(main())
