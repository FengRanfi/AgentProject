import asyncio
import argparse
import os
import sys
from typing import Any

from autogen_ext.tools.mcp import (
    StreamableHttpServerParams,
    mcp_server_tools,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent


def serialize(value: Any) -> Any:
    """Convert AutoGen/Pydantic objects into JSON-serializable values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    if isinstance(value, dict):
        return value

    return {"repr": repr(value)}


async def main(apikey: str, target_url: str, max_length: int, raw: bool) -> None:
    mcp_url = os.getenv("MODELSCOPE_MCP_URL")

    if not mcp_url:
        raise RuntimeError(
            "缺少 MODELSCOPE_MCP_URL 环境变量。\n"
            "请先执行：export MODELSCOPE_MCP_URL='你的魔搭MCP地址'"
        )

    server_params = StreamableHttpServerParams(
        url=mcp_url,
        timeout=30.0,
        sse_read_timeout=300.0,
        terminate_on_close=False,
    )

    # 创建模型客户端(使用硅基流动的模型，支持 function calling)
    # 硅基流动使用 OpenAI 兼容的 API，所以使用 OpenAIChatCompletionClient
    # 建议：如果 Qwen2.5-7B 效果不好，可以尝试更强大的模型：
    # - Qwen/Qwen2.5-72B-Instruct
    # - deepseek-ai/DeepSeek-V2.5
    model_client = OpenAIChatCompletionClient(
        model="Qwen/Qwen2.5-72B-Instruct",  # 使用更强大的模型，function calling 更稳定
        base_url="https://api.siliconflow.cn/v1",  # 硅基流动的 API endpoint
        api_key=apikey,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": True,  # 添加这个字段以消除警告
        },
    )

    try:
        # 使用 mcp_server_tools 从 MCP 服务器获取 Tool 对象
        tools = await mcp_server_tools(server_params)

        if not tools:
            print("连接成功，但 MCP Server 没有返回任何工具。")
            await model_client.close()
            return

        print(f"连接成功，共发现 {len(tools)} 个工具：\n")

        for index, tool in enumerate(tools, start=1):
            print(f"===== 工具 {index} =====")
            print(f"工具类型: {type(tool)}")
            print(f"工具对象: {tool}")
            print(f"工具名称: {tool.name}")
            print(f"工具描述: {tool.description}")
            # 打印工具的所有属性
            print(f"工具属性: {[attr for attr in dir(tool) if not attr.startswith('_')]}")
            # 尝试获取 schema
            if hasattr(tool, 'schema'):
                print(f"工具 schema: {tool.schema}")
            if hasattr(tool, 'parameters'):
                print(f"工具参数: {tool.parameters}")
            print()

        if not any(tool.name == "fetch" for tool in tools):
            print("当前 MCP Server 没有返回 fetch 工具，无法执行网页读取任务。")
            await model_client.close()
            return

        # 创建 AssistantAgent,传入模型客户端和 MCP 工具
        agent = AssistantAgent(
            name="fetch_agent",
            model_client=model_client,
            tools=tools,  # 将 MCP Tool 对象传递给 Agent
            system_message=(
                "你是一个网页读取助手。你只能使用 fetch 工具读取用户明确提供的 URL，"
                "不要把 fetch 当成搜索引擎，也不要构造 Google/Bing 搜索 URL。"
                "如果用户没有提供 URL，应要求用户提供明确 URL。"
            ),
            reflect_on_tool_use=True,  # 关闭反思功能以简化流程
            model_client_stream=True,  # 关闭流式输出以避免工具调用兼容性问题
            tool_call_summary_format="{result}",  # 简化工具调用摘要格式
        )

        # 运行一个网页读取任务示例
        print("\n开始执行网页读取任务...\n")
        
        # 添加调试：测试模型是否能正确生成工具调用
        print("========== 测试模型工具调用能力 ==========")
        from autogen_core.models import UserMessage, SystemMessage
        test_messages = [
            SystemMessage(
                content=(
                    "你是一个网页读取助手。你只能使用 fetch 工具读取用户明确提供的 URL，"
                    "不要把 fetch 当成搜索引擎。"
                )
            ),
            UserMessage(
                content=(
                    f"请使用 fetch 工具读取这个网页：{target_url}。"
                    f"参数 raw={raw}, max_length={max_length}。"
                ),
                source="user",
            ),
        ]
        test_response = await model_client.create(
            messages=test_messages,
            tools=tools,  # 传入工具定义
        )
        print(f"测试响应类型: {type(test_response)}")
        print(f"测试响应对象所有属性: {dir(test_response)}")
        print(f"finish_reason: {test_response.finish_reason}")
        print(f"content: '{test_response.content}'")
        print(f"usage: {test_response.usage}")
        
        # 检查是否有 tool_calls 属性
        if hasattr(test_response, 'tool_calls'):
            print(f"有 tool_calls 属性")
            print(f"tool_calls 值: {test_response.tool_calls}")
            print(f"tool_calls 类型: {type(test_response.tool_calls)}")
            if test_response.tool_calls:
                print(f"工具调用数量: {len(test_response.tool_calls)}")
                for idx, tc in enumerate(test_response.tool_calls):
                    print(f"工具调用 {idx+1}: {tc}")
            else:
                print("tool_calls 为空或 None")
        else:
            print("没有 tool_calls 属性")
        
        # 检查其他可能的字段
        for attr in ['function_call', 'tool_call', 'calls']:
            if hasattr(test_response, attr):
                print(f"发现 {attr} 属性: {getattr(test_response, attr)}")
        
        print("========== 测试结束 ==========\n")
        
        # 使用 run() 而不是 run_stream() 来获取完整结果
        result = await agent.run(
            task=(
                f"请使用 fetch 工具读取这个网页：{target_url}。"
                f"参数 raw={raw}, max_length={max_length}。"
                "读取后直接返回工具结果摘要。"
            )
        )
        
        print("\n========== 任务执行结果 ==========")
        print(f"任务完成，共产生 {len(result.messages)} 条消息")
        
        for i, message in enumerate(result.messages, 1):
            print(f"\n----- 消息 {i} -----")
            print(f"类型: {type(message).__name__}")
            # 打印完整的消息结构（JSON格式）
            print(f"完整消息结构:\n{message.model_dump_json(indent=2)}")
            
            # 检查是否有工具调用
            if hasattr(message, 'tool_calls'):
                print(f"工具调用: {message.tool_calls}")
            if hasattr(message, 'function_call'):
                print(f"函数调用: {message.function_call}")
            if hasattr(message, 'content'):
                print(f"内容: {message.content}")
            if hasattr(message, 'source'):
                print(f"来源: {message.source}")
        
        print("\n========== 最终响应 ==========")
        # 获取最后一条消息的内容
        if result.messages:
            last_message = result.messages[-1]
            if hasattr(last_message, 'content'):
                print(last_message.content)

        # 关闭模型客户端连接
        await model_client.close()

    except Exception as exc:
        print(
            f"MCP 连接失败：{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        await model_client.close()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 MCP fetch 工具读取指定网页")
    parser.add_argument("--apikey", type=str, required=True, help="硅基流动 API Key")
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.douban.com",
        help="要用 fetch 工具读取的网页 URL",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=5000,
        help="fetch 返回的最大字符数",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="返回原始 HTML，而不是简化后的 Markdown",
    )
    args = parser.parse_args()
    asyncio.run(main(args.apikey, args.url, args.max_length, args.raw))
