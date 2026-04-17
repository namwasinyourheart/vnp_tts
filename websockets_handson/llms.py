import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(
    model: str = os.getenv("DEFAULT_MODEL"),
    api_key: str = os.getenv("OPENAI_API_KEY"),
    base_url: str = os.getenv("OPENAI_API_BASE"),
) -> ChatOpenAI:
    return ChatOpenAI(model=model, api_key=api_key, base_url=base_url)
