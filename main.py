import os

import hikari
import lightbulb
import miru

from google import genai
from groq import AsyncGroq

from dotenv import load_dotenv

import bot as bot_pkg
from internal.config import logger

load_dotenv()

bot = hikari.GatewayBot(
    token=os.getenv("DISCORD_BOT_TOKEN"),
    intents=hikari.Intents.ALL_UNPRIVILEGED,
)
inter_client = miru.Client(bot)
client = lightbulb.client_from_app(bot)


async def load_extensions(_: hikari.StartingEvent):
    await client.load_extensions_from_package(bot_pkg)
    await client.start()


bot.subscribe(hikari.StartingEvent, load_extensions)

try:
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_TOKEN"))
    groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_TOKEN"))
except Exception as e:
    logger.error(f"Failed to initialize API clients: {e}")
    raise

registry = client.di.registry_for(lightbulb.di.Contexts.DEFAULT)
registry.register_value(type(bot), bot)
registry.register_value(type(inter_client), inter_client)
registry.register_value(type(client), client)
registry.register_value(type(groq_client), groq_client)
registry.register_value(type(gemini_client), gemini_client)


def main():
    required_env_vars = [
        "DISCORD_BOT_TOKEN",
        "GEMINI_API_TOKEN",
        "GROQ_API_TOKEN",
        "IMAGE_GEN_TOKEN",
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        return

    logger.info("Starting bot")
    bot.run()


if __name__ == "__main__":
    main()
