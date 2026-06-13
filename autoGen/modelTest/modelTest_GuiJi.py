import argparse

from autogen_core.models import UserMessage
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential

async def main(apikey: str):
    client = AzureAIChatCompletionClient(
        model="Qwen/Qwen3-VL-8B-Instruct",
        endpoint="https://api.siliconflow.cn/v1",
        # To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings.
        # Create your PAT token by following instructions here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
        credential=AzureKeyCredential(apikey),
        model_info={
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
        "structured_output": False
        },
    )

    result = await client.create([UserMessage(content="What is the capital of France?", source="user")])
    print(result)
    await client.close()

import asyncio

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Azure AI model")
    parser.add_argument("--apikey", type=str, required=True, help="GitHub PAT token")
    args = parser.parse_args()
    asyncio.run(main(args.apikey))


