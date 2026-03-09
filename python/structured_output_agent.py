import asyncio
import os

from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class PersonInfo(BaseModel):
    """Information about a person."""
    name: str | None = None
    age: int | None = None
    occupation: str | None = None

class CityInfo(BaseModel):
    """A structured output for testing purposes."""

    city: str
    description: str
    population: int

async def non_streaming():
    print("=== Non Streaming example ===")
    client = AzureOpenAIChatClient(
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            )

    agent = client.as_agent(
        name="PersonAgent",
        instructions="You are a helpful agent that describes persons in a sctructured format."
    )

    query = "Please provide information about John Smith, who is a 35-year-old software engineer."
    print(f"User: {query}")

    response = await agent.run(
        query, options={"response_format": PersonInfo}
    )

    if response.value:
        person_info = response.value
        print("Person Agent:")
        print(f"Name: {person_info.name}")
        print(f"Age: {person_info.age}")
        print(f"Occupation: {person_info.occupation}")
    else:
        print(f"Failed to parse response: {response.text}")

async def streaming() -> None:
    print("=== Streaming example ===")

    client = AzureOpenAIChatClient(
                endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            )

    agent = client.as_agent(
        name="CityAgent",
        instructions="You are a helpful agent that describes persons in a sctructured format."
    )

    query = "Tell me about Tokyo, Japan, and how many people live there"
    print(f"User: {query}")

    # Stream updates in real time using ResponseStream
    stream = agent.run(query, stream=True, options={"response_format": CityInfo})
    async for update in stream:
        if update.text:
            print(update.text, end="", flush=True, )
    print()

    # get_final_response() returns the AgentResponse with structured output parsed
    result = await stream.get_final_response()

    if structured_data := result.value:
        print("Structured Output (from streaming with ResponseStream):")
        print(f"City: {structured_data.city}")
        print(f"Description: {structured_data.description}")
        print(f"Size: {structured_data.population} peoples")
    else:
        print(f"Failed to parse response: {result.text}")


async def main() -> None:
    print("=== OpenAI Responses Agent with Structured Output ===")

    await non_streaming()
    await streaming()

if __name__ == "__main__":
    asyncio.run(main())