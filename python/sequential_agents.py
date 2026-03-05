import asyncio
import os
from typing import Any
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.orchestrations import SequentialBuilder
from agent_framework import Message, WorkflowEvent
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = AzureOpenAIChatClient(
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        )

    writer = client.as_agent(
        instructions=(
            "You are a concise copywriter. Provide a single, punchy marketing sentence based on the prompt."
        ),
        name="writer",
    )

    reviewer = client.as_agent(
        instructions=(
            "You are a thoughtful reviewer. Give brief feedback on the previous assistant message."
        ),
        name="reviewer",
    )

    translator = client.as_agent(
        instructions=(
            "You are a translator. Translate to french the punchy marketing sentence and the feed back of both previous assistant message."
        ),
        name="translator",
    )

    workflow = SequentialBuilder(participants=[writer, reviewer, translator]).build()

    output_evt: WorkflowEvent | None = None
    async for event in workflow.run("Write a tagline for a new pizza place", stream=True):
        if event.type == "output":
            output_evt = event
        
    if output_evt:
        print("---------Finale sequential conversation---------")
        messages: list[Message] | Any = output_evt.data
        for i, msg in enumerate(messages, start=1):
            name = msg.author_name or ("assistant" if msg.role == "assistant" else "user")
            print(f"{'-' * 60}\n{i:02d} [{name}]\n{msg.text}")

if __name__ == "__main__":
    asyncio.run(main())