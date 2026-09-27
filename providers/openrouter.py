"""Провайдер OpenRouter с авто-fallback между free моделями."""
import os

from openai import OpenAI
from providers.base import Provider


class OpenRouterProvider(Provider):
    """OpenRouter с fallback-массивом free моделей."""

    def __init__(self, api_key: str, provider_name: str = "openrouter",
                 model_catalog: list = None, default_model: str = None,
                 fallback_models: list = None):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.name = provider_name
        self._catalog = model_catalog or []
        self._default = default_model or "openrouter/free"
        self._fallback_models = fallback_models or []
        self.supports_tools = True

    def list_models(self) -> list:
        return list(self._catalog)

    def default_model(self) -> str:
        return self._default

    def ask(self, model_name: str, messages: list, tools: list = None) -> str:
        kwargs = {
            "model": model_name,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Если primary — не openrouter/free, добавляем fallback-массив
        # OpenRouter поддерживает максимум 3 модели в массиве
        if model_name != "openrouter/free" and self._fallback_models:
            all_models = [model_name] + [
                m for m in self._fallback_models if m != model_name
            ]
            # Обрезаем до 3 моделей (требование OpenRouter)
            all_models = all_models[:3]
            kwargs["extra_body"] = {"models": all_models}

        # Цикл tool-calling
        for iteration in range(10):
            response = self.client.chat.completions.create(**kwargs)
            msg = response.choices[0].message

            if msg.tool_calls:
                # Добавляем ассистента с tool_calls
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

                # Дедупликация
                seen = set()
                unique = []
                for tc in msg.tool_calls:
                    key = (tc.function.name, tc.function.arguments or "")
                    if key in seen:
                        continue
                    seen.add(key)
                    unique.append(tc)

                from tools.registry import execute_tool
                import json
                import time as _time

                for tc in unique:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except Exception:
                        args = {}

                    from rich.console import Console
                    from rich.panel import Panel
                    console = Console()
                    console.print(Panel.fit(
                        f"[bold yellow]{tc.function.name}[/bold yellow]\n[dim]{args}[/dim]",
                        title="tool call", border_style="yellow",
                    ))

                    t0 = _time.time()
                    result = execute_tool(tc.function.name, args)
                    dt = _time.time() - t0

                    if len(result) > 8000:
                        result = result[:8000] + "\n...[обрезано]"

                    preview = result if len(result) < 500 else result[:500] + "..."
                    console.print(Panel.fit(preview, title="tool result", border_style="dim"))
                    console.print(f"[dim]⏱  инструмент {tc.function.name} выполнен за {dt:.2f}с[/dim]")

                    kwargs["messages"].append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
                continue

            return msg.content or "(пустой ответ)"

        return "[превышен лимит итераций tool-calls]"


def create(api_key: str) -> OpenRouterProvider:
    """Создаёт провайдера OpenRouter с каталогом free-моделей."""
    from config import OPENROUTER_MODELS, OPENROUTER_FALLBACKS

    return OpenRouterProvider(
        api_key=api_key,
        provider_name="openrouter",
        model_catalog=OPENROUTER_MODELS,
        default_model="meta-llama/llama-3.3-70b-instruct:free",
        fallback_models=OPENROUTER_FALLBACKS,
    )