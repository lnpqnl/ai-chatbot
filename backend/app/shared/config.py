import os

from dotenv import load_dotenv

load_dotenv()


def get_llm_provider_name() -> str:
    return os.getenv("LLM_PROVIDER", "mock")


def get_openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "")


def get_openai_base_url() -> str:
    return os.getenv("OPENAI_BASE_URL", "")


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4")
