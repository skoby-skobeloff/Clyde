import os
import logging
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("lunalai")
data_logger = logging.getLogger("lunalai.stats")

db_file = os.getenv("STATS_DB")

chat_histories: Dict[int, List[str]] = {}

MAX_DISCORD_MESSAGE_LENGTH = 2000
MAX_CHAT_HISTORY = 30
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_PROMPT = """
You are {}, a Discord chatbot.

You are aware of the following:
- You are currently in the #{} channel.
- You are currently in the {} server.
- The current time and date is {}.

IMPORTANT: Blank placeholders are equivalent to {{}}. 
Do not mention the server or the channel if it is {{}}.

Your personality reflects your name. Try to make up a personality that matches your name.
"""


MODELS = {
    "gemini": [
        # Gemini 3.0 series
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        # Gemini 2.5 series
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ],
    "gemma": [
        # Gemma 2 models have been decommissioned.
        # Gemma 3 series
        "gemma-3-1b-it",
        "gemma-3-4b-it",
        "gemma-3-12b-it",
        "gemma-3-27b-it",
        "gemma-3n-e2b-it",
        "gemma-3n-e4b-it",
    ],
    "other": [
        # Qwen models
        "qwen/qwen3-32b",
        # Llama 3.x series
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        # Llama 4 series
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-7b-16e-instruct",
        # Moonshot AI models
        "moonshotai/kimi-k2-instruct-0905",
        # OpenAI open source models
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        # Groq in-house models
        "groq/compound",
        "groq/compound-mini",
    ],
}

DEFAULT_IMAGE_MODEL = "gpt-image-1.5"
IMAGE_MODELS = {
    "gpt-image-1.5": "gpt-image-1.5",
    "nano-banana": "gemini-2.5-flash-image",
    "nano-banana-pro": "gemini-3-pro-image-preview",
}

PROMPT_PRESETS = {
    "default": DEFAULT_PROMPT,
    "gpt": "You are GPT-5.2, a large language model from OpenAI. Refer to yourself as ChatGPT.",
    "casual": "Respond casually, no need to use overly verbose responses.",
    "discord": "You are a Discord user, respond lowercase only, no punctuation, and treat yourself like you're on IRC.",
    "programmer": "You are a programming assistant who will provide suggestions to codes given and attempt to rework when asked.",
    "storyteller": "You will make creative stories about the given topics, tell the user said story.",
}