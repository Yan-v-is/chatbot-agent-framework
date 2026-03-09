import asyncio
import os
from typing import cast
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.orchestrations import GroupChatBuilder
from agent_framework import Message, AgentResponseUpdate
from agent_framework import (
    Agent,
)
from dotenv import load_dotenv

load_dotenv()
async def main():

    client = AzureOpenAIChatClient(
                        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                        deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                        api_key=os.environ["AZURE_OPENAI_API_KEY"],
                        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                )

    # Create a researcher agent
    researcher = Agent(
        name="Researcher",
        description="Collects relevant background information.",
        instructions="Gather concise facts that help answer the question. Be brief and factual.",
        client=client,
    )
    # Create a writer agent
    writer = Agent(
        name="Writer",
        description="Synthesizes polished answers using gathered information.",
        instructions="Compose clear, structured answers using any notes provided. Be comprehensive.",
        client=client,
    )

    # Create orchestrator agent for speaker selection
    orchestrator_agent = Agent(
        name="Orchestrator",
        description="Coordinates multi-agent collaboration by selecting speakers",
        instructions="""
    You coordinate a team conversation to solve the user's task.

    Guidelines:
    - Start with Researcher to gather information
    - Then have Writer synthesize the final answer
    - Only finish after both have contributed meaningfully
    """,
        client=client,
    )

    # Build group chat with agent-based orchestrator
    workflow = GroupChatBuilder(
        participants=[researcher, writer],
        # Set a hard termination condition: stop after 4 assistant messages
        # The agent orchestrator will intelligently decide when to end before this limit but just in case
        termination_condition=lambda messages: sum(1 for msg in messages if msg.role == "assistant") >= 4,
        orchestrator_agent=orchestrator_agent,
    ).build()

    task = "What are the key benefits of async/await in Python?"

    print(f"Task: {task}\n")
    print("=" * 80)

    final_conversation: list[Message] = []
    last_executor_id: str | None = None

    # Run the workflow
    async for event in workflow.run(task, stream=True):
        if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
            # Print streaming agent updates
            eid = event.executor_id
            if eid != last_executor_id:
                if last_executor_id is not None:
                    print()
                print(f"[{eid}]:", end=" ", flush=True)
                last_executor_id = eid
            print(event.data, end="", flush=True)
        elif event.type == "output":
            # Workflow completed - data is a list of Message
            final_conversation = cast(list[Message], event.data)

    if final_conversation:
        print("\n\n" + "=" * 80)
        print("Final Conversation:")
        for msg in final_conversation:
            author = getattr(msg, "author_name", "Unknown")
            text = getattr(msg, "text", str(msg))
            print(f"\n[{author}]\n{text}")
            print("-" * 80)

    print("\nWorkflow completed.")

if __name__ == "__main__":
    asyncio.run(main())