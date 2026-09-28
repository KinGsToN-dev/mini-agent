"""Общая обёртка для OpenAI-совместимых API.

Groq — поддерживает OpenAI-формат tools.
Mistral — НЕ поддерживает (свой формат), поэтому для Mistral tools отключаются.
"""

from openai import OpenAI
from providers.base import Provider


class OpenAICompatProvider(Provider):
    """Провайдер на базе OpenAI-совместимого API."""

    def __init__(self, api_key: str, base_url: str, provider_name: str,
                 model_catalog: list, default_model: str,
                 supports_tools: bool = True):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.name = provider_name
        self._catalog = model_catalog
        self._default = default_model
        self.supports_tools = supports_tools

    def list_models(self) -> list:
        return list(self._catalog)

    def default_model(self) -> str:
        return self._default

    def ask(self, model_name: str, messages: list,
            tools: list = None) -> str:
        kwargs = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 4000,   # чтобы не обрезалось
        }

        # Для Mistral tools не поддерживаются — просто игнорируем
        if tools and self.supports_tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        for _ in range(10):
            response = self.client.chat.completions.create(**kwargs)
            msg = response.choices[0].message

            if msg.tool_calls:
                kwargs["messages"].append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                })

                from tools.registry import execute_tool
                import json
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except Exception as e:
                        from agent.log import log
                        log(f"openai_compat: bad JSON args for {tc.function.name}: {e}", level="WARNING")
                        args = {}
                    result = execute_tool(tc.function.name, args)
                    if len(result) > 8000:
                        result = result[:8000] + "\n...[обрезано]"
                    kwargs["messages"].append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
                continue

            return msg.content or "(пустой ответ)"

        return "[превышен лимит итераций tool-calls]"
