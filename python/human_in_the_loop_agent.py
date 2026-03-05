# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from collections.abc import AsyncIterable
from dataclasses import dataclass

from agent_framework import (
    AgentExecutorRequest,
    AgentExecutorResponse,
    AgentResponseUpdate,
    Executor,
    Message,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowEvent,
    handler,
    response_handler,
)
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

@dataclass
class HumanFeedbackRequest:
    """Request sent to the human for feedback on the agent's guess."""

    prompt: str


class GuessOutput(BaseModel):
    """Structured output from the agent. Enforced via response_format for reliable parsing."""

    guess: int


class TurnManager(Executor):
    """Coordinates turns between the agent and the human.

    Responsibilities:
    - Kick off the first agent turn.
    - After each agent reply, request human feedback with a HumanFeedbackRequest.
    - After each human reply, either finish the game or prompt the agent again with feedback.
    """

    def __init__(self, id: str | None = None):
        super().__init__(id=id or "turn_manager")

    @handler
    async def start(self, _: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        """Start the game by asking the agent for an initial guess.

        Contract:
        - Input is a simple starter token (ignored here).
        - Output is an AgentExecutorRequest that triggers the agent to produce a guess.
        """
        user = Message("user", text="Start by making your first guess.")
        await ctx.send_message(AgentExecutorRequest(messages=[user], should_respond=True))

    @handler
    async def on_agent_response(
        self,
        result: AgentExecutorResponse,
        ctx: WorkflowContext,
    ) -> None:
        agent_value = result.agent_response.value
        if agent_value is None:
            raise RuntimeError(
                "AgentResponse.value is None. Ensure that the agent is invoked with "
                "options={'response_format': GuessOutput} so structured output is available."
            )
        last_guess = agent_value.guess

        # Craft a precise human prompt that defines higher and lower relative to the agent's guess.
        prompt = (
            f"The agent guessed: {last_guess}. "
            "Type one of: higher (your number is higher than this guess), "
            "lower (your number is lower than this guess), correct, or exit."
        )
        # Send a request with a prompt as the payload and expect a string reply.
        await ctx.request_info(
            request_data=HumanFeedbackRequest(prompt=prompt),
            response_type=str,
        )

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanFeedbackRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        """Continue the game or finish based on human feedback."""
        reply = feedback.strip().lower()

        if reply == "correct":
            await ctx.yield_output("Guessed correctly!")
            return

        # Provide feedback to the agent to try again.
        # response_format=GuessOutput on the agent ensures JSON output, so we just need to guide the logic.
        last_guess = original_request.prompt.split(": ")[1].split(".")[0]
        feedback_text = (
            f"Feedback: {reply}. Your last guess was {last_guess}. "
            f"Use this feedback to adjust and make your next guess (1-100)."
        )
        user_msg = Message("user", text=feedback_text)
        await ctx.send_message(AgentExecutorRequest(messages=[user_msg], should_respond=True))


async def process_event_stream(stream: AsyncIterable[WorkflowEvent]) -> dict[str, str] | None:
    """Process events from the workflow stream to capture human feedback requests."""
    # Track the last author to format streaming output.
    last_response_id: str | None = None

    requests: list[tuple[str, HumanFeedbackRequest]] = []
    async for event in stream:
        if event.type == "request_info" and isinstance(event.data, HumanFeedbackRequest):
            requests.append((event.request_id, event.data))
        elif event.type == "output":
            if isinstance(event.data, AgentResponseUpdate):
                update = event.data
                response_id = update.response_id
                if response_id != last_response_id:
                    if last_response_id is not None:
                        print()  # Newline between different responses
                    print(f"{update.author_name}: {update.text}", end="", flush=True)
                    last_response_id = response_id
                else:
                    print(update.text, end="", flush=True)
            else:
                print(f"\n{event.executor_id}: {event.data}")

    # Handle any pending human feedback requests.
    if requests:
        responses: dict[str, str] = {}
        for request_id, request in requests:
            print(f"\nHITL: {request.prompt}")
            # Instructional print already appears above. The input line below is the user entry point.
            # If desired, you can add more guidance here, but keep it concise.
            answer = input("Enter higher/lower/correct/exit: ").lower()
            if answer == "exit":
                print("Exiting...")
                return None
            responses[request_id] = answer
        return responses

    return None


async def main() -> None:
    """Run the human-in-the-loop guessing game workflow."""
    # Create agent and executor
    guessing_agent = AzureOpenAIChatClient(
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    ).as_agent(
        name="GuessingAgent",
        instructions=(
            "You guess a number between 1 and 100. "
            "If the user says 'higher' or 'lower', adjust your next guess. "
            'You MUST return ONLY a JSON object exactly matching this schema: {"guess": <integer 1..100>}. '
            "No explanations or additional text."
        
        ),
    )
    turn_manager = TurnManager(id="turn_manager")

    # Build a simple loop: TurnManager <-> AgentExecutor.
    workflow = (
        WorkflowBuilder(start_executor=turn_manager)
        .add_edge(turn_manager, guessing_agent)  # Ask agent to make/adjust a guess
        .add_edge(guessing_agent, turn_manager)  # Agent's response comes back to coordinator
    ).build()

    stream = workflow.run("start", stream=True, options={"response_format": GuessOutput})

    pending_responses = await process_event_stream(stream)
    while pending_responses is not None:
        # Run the workflow until there is no more human feedback to provide,
        # in which case this workflow completes.
        stream = workflow.run(stream=True, responses=pending_responses, options={"response_format": GuessOutput})
        pending_responses = await process_event_stream(stream)


if __name__ == "__main__":
    asyncio.run(main())