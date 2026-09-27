"""Провайдер Mistral. Tools не поддерживаются (свой формат API)."""

from providers.openai_compat import OpenAICompatProvider


MISTRAL_MODELS = [
    ("codestral", "codestral-latest",      "для кода, 2000/день"),
    ("large",     "mistral-large-latest",  "требует data-training"),
    ("small",     "mistral-small-latest",  "требует data-training"),
    ("nemo",      "open-mistral-nemo",     "может не работать"),
]

DEFAULT_MISTRAL = "codestral"


def create(api_key: str) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        api_key=api_key,
        base_url="https://api.mistral.ai/v1",
        provider_name="mistral",
        model_catalog=MISTRAL_MODELS,
        default_model=DEFAULT_MISTRAL,
        supports_tools=False,   # ⬅️ Mistral не принимает OpenAI-формат tools
    )
