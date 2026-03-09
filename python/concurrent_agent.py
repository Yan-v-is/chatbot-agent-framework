import asyncio
import os
from typing import Any
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework import Message, WorkflowEvent
from agent_framework import (
    AgentExecutorRequest,
    AgentExecutorResponse,
    Agent,
    Executor,
    WorkflowContext,
    handler,
)
from dotenv import load_dotenv

load_dotenv()

class ResearcherExec(Executor):
    agent: Agent

    def __init__(self, client: AzureOpenAIChatClient, id: str = "researcher"):
        agent = client.as_agent(
            instructions=(
                "You're an expert market and product researcher. Given a prompt, provide concise, factual insights,"
                " opportunities, and risks."
            ),
            name=id,
        )
        super().__init__(agent=agent, id=id)
        self.agent = agent

    @handler
    async def run(self, request: AgentExecutorRequest, ctx: WorkflowContext[AgentExecutorResponse]) -> None:
        response = await self.agent.run(request.messages)
        full_conversation = list(request.messages) + list(response.messages)
        await ctx.send_message(AgentExecutorResponse(self.id, response, full_conversation=full_conversation))

class MarketerExec(Executor):
    agent: Agent

    def __init__(self, client: AzureOpenAIChatClient, id: str = "marketer"):
        agent = client.as_agent(
            instructions=(
                "You're a creative marketing strategist. Craft compelling value propositions and target messaging"
                " aligned to the prompt."
            ),
            name=id,
        )
        super().__init__(agent=agent, id=id)
        self.agent = agent

    @handler
    async def run(self, request: AgentExecutorRequest, ctx: WorkflowContext[AgentExecutorResponse]) -> None:
        response = await self.agent.run(request.messages)
        full_conversation = list(request.messages) + list(response.messages)
        await ctx.send_message(AgentExecutorResponse(self.id, response, full_conversation=full_conversation))

class LegalExec(Executor):
    agent: Agent

    def __init__(self, client: AzureOpenAIChatClient, id: str = "legal"):
        agent = client.as_agent(
            instructions=(
                "You're a cautious legal/compliance reviewer. Highlight constraints, disclaimers, and policy concerns"
            " based on the prompt."
            ),
            name=id,
        )
        super().__init__(agent=agent, id=id)
        self.agent = agent

    @handler
    async def run(self, request: AgentExecutorRequest, ctx: WorkflowContext[AgentExecutorResponse]) -> None:
        response = await self.agent.run(request.messages)
        full_conversation = list(request.messages) + list(response.messages)
        await ctx.send_message(AgentExecutorResponse(self.id, response, full_conversation=full_conversation))


async def main_agents():
    client = AzureOpenAIChatClient(
                        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                        deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                        api_key=os.environ["AZURE_OPENAI_API_KEY"],
                        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                )

    researcher = client.as_agent(
        instructions=(
            "You're an expert market and product researcher. Given a prompt, provide concise, factual insights,"
            " opportunities, and risks."
        ),
        name="researcher",
    )

    marketer = client.as_agent(
        instructions=(
            "You're a creative marketing strategist. Craft compelling value propositions and target messaging"
            " aligned to the prompt."
        ),
        name="marketer",
    )

    legal = client.as_agent(
        instructions=(
            "You're a cautious legal/compliance reviewer. Highlight constraints, disclaimers, and policy concerns"
            " based on the prompt."
        ),
        name="legal",
    )

    workflow = ConcurrentBuilder(participants =[researcher, marketer, legal]).build()

    output_evt: WorkflowEvent | None = None
    async for event in workflow.run("We are launching a new budget-friendly electric bike for urban commuters.", stream= True):
        if event.type == "output":
                output_evt = event

    if output_evt:
        print("===== Final Aggregated Conversation with Agents =====")
        messages: list[Message] | Any = output_evt.data
        for i, msg in enumerate(messages, start=1):
            name = msg.author_name if msg.author_name else "user"
            print(f"{'-' * 60}\n\n{i:02d} [{name}]:\n{msg.text}")

async def main_executors():
    client = AzureOpenAIChatClient(
                        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                        deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                        api_key=os.environ["AZURE_OPENAI_API_KEY"],
                        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                )

    researcher = ResearcherExec(client)
    marketer = MarketerExec(client)
    legal = LegalExec(client)
    workflow = ConcurrentBuilder(participants =[researcher, marketer, legal]).build()

    output_evt: WorkflowEvent | None = None
    async for event in workflow.run("We are launching a new budget-friendly electric bike for urban commuters.", stream= True):
        if event.type == "output":
                output_evt = event

    if output_evt:
        print("===== Final Aggregated Conversation with Executors =====")
        messages: list[Message] | Any = output_evt.data
        for i, msg in enumerate(messages, start=1):
            name = msg.author_name if msg.author_name else "user"
            print(f"{'-' * 60}\n\n{i:02d} [{name}]:\n{msg.text}")


if __name__ == "__main__":
    asyncio.run(main_agents())
    asyncio.run(main_executors())