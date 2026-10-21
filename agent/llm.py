"""The LLM: Groq (very fast inference of open models)."""

import os

from langchain_groq import ChatGroq


def get_llm() -> ChatGroq:
    # Reads GROQ_API_KEY from the environment.
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
    )
