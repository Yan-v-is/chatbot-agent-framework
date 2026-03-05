import asyncio
import os

from agent_framework import Message, Content
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAIChatClient(
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        )

agent = client.as_agent(
    name="VisionAgent",
    instructions="You are a helpful agent that can analyze images"
)

# Analyse a local image
with open("python\\images\\apple.jpg", "rb") as f:
    image_bytes = f.read()

local_message = Message(
    role="user",
    contents=[
        Content.from_text(text="What do you see in this image?"),
        Content.from_data(
            data=image_bytes,
            media_type="image/jpeg"
        )
    ]
)

# Analyse image from URL
url_message = Message(
    role="user",
    contents=[
        Content.from_text(text="What do you see in this image?"),
        Content.from_uri(
            uri="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Colombus_Isle.JPG/250px-Colombus_Isle.JPG",
            media_type="image/jpeg"
        )
    ]
)

async def main():
    # Local image
    local_result = await agent.run(local_message)
    print(local_result.text)

    # URL image
    url_result = await agent.run(url_message)
    print(url_result.text)

asyncio.run(main())