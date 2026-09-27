"""Абстрактный интерфейс провайдера LLM."""


class Provider:
    """Базовый интерфейс."""
    name: str = "base"

    def list_models(self) -> list:
        raise NotImplementedError

    def default_model(self) -> str:
        raise NotImplementedError

    def ask(self, model_name: str, messages: list,
            tools: list = None) -> str:
        raise NotImplementedError
