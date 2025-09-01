import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


def get_openai_api_key() -> str:
    """Return OpenAI API key or empty string if unset."""
    return os.getenv("OPENAI_API_KEY", "")


def get_serper_api_key() -> str:
    """Return Serper.dev API key.

    Supports either provider-specific `SERPER_API_KEY` or generic `SERP_API_KEY`.
    """
    return os.getenv("SERPER_API_KEY") or os.getenv("SERP_API_KEY", "")


def get_searchapi_api_key() -> str:
    """Return SearchAPI.io API key.

    Supports either provider-specific `SEARCHAPI_API_KEY` or generic `SERP_API_KEY`.
    """
    return os.getenv("SEARCHAPI_API_KEY") or os.getenv("SERP_API_KEY", "")
