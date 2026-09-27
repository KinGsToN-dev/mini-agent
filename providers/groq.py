"""Провайдер Groq."""

from providers.openai_compat import OpenAICompatProvider


GROQ_MODELS = [
    ("gpt-oss-20b",  "openai/gpt-oss-20b",   "быстрая, работает с tools"),
    ("gpt-oss-120b", "openai/gpt-oss-120b",  "умная, путает tools"),
    ("qwen-27b",     "qwen/qwen3.8-27b",     "медленная, лимит 7000 ITPM"),
    ("allam",        "allam-2-7b",           "очень быстрая, без tools"),
]

DEFAULT_GROQ = "gpt-oss-20b"


def create(api_key: str) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        provider_name="groq",
        model_catalog=GROQ_MODELS,
        default_model=DEFAULT_GROQ,
    )
