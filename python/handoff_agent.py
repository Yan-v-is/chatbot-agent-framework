# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Annotated

from agent_framework import (
    AgentResponseUpdate,
    resolve_agent_id,
    tool,
)
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.orchestrations import HandoffBuilder
from dotenv import load_dotenv
load_dotenv()

@tool
def process_refund(order_number: Annotated[str, "Order number to process refund for"]) -> str:
    """Simulated function to process a refund for a given order number."""
    return f"Refund processed successfully for order {order_number}."

@tool
def check_order_status(order_number: Annotated[str, "Order number to check status for"]) -> str:
    """Simulated function to check the status of a given order number."""
    return f"Order {order_number} is currently being processed and will ship in 2 business days."

@tool
def process_return(order_number: Annotated[str, "Order number to process return for"]) -> str:
    """Simulated function to process a return for a given order number."""
    return f"Return initiated successfully for order {order_number}. You will receive return instructions via email."

async def main() -> None:
    chat_client = AzureOpenAIChatClient(
                        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                        deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                        api_key=os.environ["AZURE_OPENAI_API_KEY"],
                        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                )
    
    coordinator_agent = chat_client.as_agent(
        name="coordinator_agent",
        description="Autonomous coordinator that ensures each specialist contributes only when needed.",
        instructions=(
            "You are a coordinator. You break down a user query into a research task and a summary task. "
            "Assign the two tasks to the appropriate specialists, one after the other."
        ),
    )

    writer_agent = chat_client.as_agent(
        name="writer_agent",
        description="Creates a first-draft article or long-form content.",
        instructions=(
            "You are a research specialist that explores topics thoroughly using web search. "
            "When given a research task, break it down into multiple aspects and explore each one. "
            "Continue your research across multiple responses - don't try to finish everything in one "
            "response. After each response, think about what else needs to be explored. When you have "
            "covered the topic comprehensively (3 aspects), return control to the "
            "coordinator. Keep each individual response focused on one aspect."
        ),
    )

    
    summary_agent = chat_client.as_agent(
        name="summary_agent",
        description="Summarizes multi‑aspect research.",
        instructions=(
            "You are a summarization specialist. "
            "You MUST NOT perform any new research. "
            "You MUST produce a coherent summary of ALL aspects explored "
            "by the research agent. "
            "After producing your full written summary, ALWAYS end your message with "
            "the exact token: RESEARCH_COMPLETE "
        )
    )

    
    workflow = (
        HandoffBuilder(
            name="autonomous_iteration_handoff",
            participants = [coordinator_agent, writer_agent, summary_agent],
            termination_condition=lambda conv: any(
                        "RESEARCH_COMPLETE" in (msg.text or "")
                        for msg in conv
                    ),
        )
        .with_start_agent(coordinator_agent)
        .add_handoff(coordinator_agent, [writer_agent, summary_agent])
        .add_handoff(writer_agent, [coordinator_agent])
        .add_handoff(summary_agent, [coordinator_agent])
        .with_autonomous_mode(
            turn_limits={
                resolve_agent_id(coordinator_agent): 2,
                resolve_agent_id(writer_agent): 10,
                resolve_agent_id(summary_agent): 2,
            }
        )
        .build()
    )

    request = "Research the city of Grenoble thoroughly across multiple aspects. Explore only one aspect per response and continue until 3 aspects have been covered, then return control."
    print("Request:", request)

    last_response_id: str | None = None
    async for event in workflow.run(request, stream=True):
        if event.type == "handoff_sent":
            print(f"\nHandoff Event: from {event.data.source} to {event.data.target}\n")
        elif event.type == "output":
            data = event.data
            if isinstance(data, AgentResponseUpdate):
                if not data.text:
                    continue
                rid = data.response_id
                if rid != last_response_id:
                    if last_response_id is not None:
                        print("\n")
                    print(f"{data.author_name}:", end=" ", flush=True)
                    last_response_id = rid
                print(data.text, end="", flush=True)
            elif event.type == "output":
                pass


if __name__ == "__main__":
    asyncio.run(main())