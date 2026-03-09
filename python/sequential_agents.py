import asyncio
import os
from typing import Any
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.orchestrations import SequentialBuilder
from agent_framework import Message, WorkflowEvent
from dotenv import load_dotenv

load_dotenv()

class Sequential:
    def __init__(self):
        pass

    async def main(self):
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
        async for event in workflow.run("Write a tagline for the new library in town", stream=True):
            if event.type == "output":
                output_evt = event
            
        if output_evt:
            print("---------Finale sequential conversation---------")
            messages: list[Message] | Any = output_evt.data
            for i, msg in enumerate(messages, start=1):
                name = msg.author_name or ("assistant" if msg.role == "assistant" else "user")
                print(f"{'-' * 60}\n{i:02d} [{name}]\n{msg.text}")

#lass Summarizer(Executor):
#   def __init__(self, id="summarizer", **kwargs):
#           super().__init__(id=id, **kwargs)
#
#   @handler
#   async def summarize(
#       self,
#       conversation: list[Message],
#       ctx: WorkflowContext[list[Message]]
#   ) -> None:
#       users = sum(1 for m in conversation if m.role == "user")
#       assistants = sum(1 for m in conversation if m.role == "assistant")
#       summary = Message(
#           role="assistant",
#           contents=[f"Summary -> users:{users} assistants:{assistants}"]
#       )
#       await ctx.send_message(list(conversation) + [summary])
#
#   async def main(self):
#       client = AzureOpenAIChatClient(
#                       endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
#                       deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
#                       api_key=os.environ["AZURE_OPENAI_API_KEY"],
#                       api_version=os.environ["AZURE_OPENAI_API_VERSION"],
#               )
#       content_agent = client.as_agent(
#           instructions="Produce a concise paragraph answering the user's request.",
#           name="content",
#       )
#
#       summarizer = Summarizer(id = "summarizer")
#       workflow = SequentialBuilder(participants=[content_agent, summarizer]).build()
#
#       output_evt: WorkflowEvent | None = None
#       async for event in workflow.run("Write a tagline for a new pizza place", stream=True):
#           if event.type == "output":
#               output_evt = event
#           
#       if output_evt:
#           print("---------Finale sequential conversation---------")
#           messages: list[Message] | Any = output_evt.data
#           for i, msg in enumerate(messages, start=1):
#               name = msg.author_name or ("assistant" if msg.role == "assistant" else "user")
#               print(f"{'-' * 60}\n{i:02d} [{name}]\n{msg.text}")

if __name__ == "__main__":
    sequential = Sequential()
    asyncio.run(sequential.main())