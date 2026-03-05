import asyncio
import os
from random import randint
from typing import Annotated

from agent_framework import tool
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

class StepOne():
    def __init__(self):
        pass
    async def main(self) -> None:
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

        result = await agent.run("What is the capital of France?")
        print(f"Agent: {result}")

        print("Agent (streaming): ", end="", flush=True)
        async for chunk in agent.run("Tell me a one-sentence fun fact.", stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()
    
class StepTwo():
    def __init__(self):
        pass

    @tool(approval_mode="never_require")
    def get_weather(
        location: Annotated[str, Field(description="The location to get the weather for.")],
    ) -> str:
        """Get the weather for a given location."""
        conditions = ["sunny", "cloudy", "rainy", "stormy"]
        return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."
    
    async def main(self) -> None:
        client = AzureOpenAIChatClient(
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        )

        agent = client.as_agent(
            name="HelloAgent",
            instructions="You are a friendly assistant and you help with weather. Use the get_weather tool if you have to",
            tools=self.get_weather
        )

        result = await agent.run("What is the capital of Italy?")
        print(f"Agent: {result}")

        result = await agent.run("What's the weather like in Rome?")
        print(f"Agent: {result}")


if __name__ == "__main__":
    app = StepTwo()
    asyncio.run(app.main())
