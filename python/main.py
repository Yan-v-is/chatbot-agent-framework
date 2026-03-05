import asyncio
import os

from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = AzureOpenAIChatClient(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )

    agent = client.as_agent(
        name="HelloAgent",
        instructions="You are a friendly assistant. Keep your answers brief.",
    )
    print(agent)

    result = await agent.run("What is the capital of France?")
    print(f"Agent: {result}")

    print("Agent (streaming): ", end="", flush=True)
    async for chunk in agent.run("Tell me a one-sentence fun fact.", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()
    

if __name__ == "__main__":
    asyncio.run(main())
