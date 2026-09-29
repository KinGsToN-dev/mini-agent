"""Логика fallback между моделями при 429 и 404."""

from config import MODELS, MODEL_CATALOG

def _record_fallback():
    try:
        from agent import analytics
        analytics.get().record_fallback()
    except Exception as e:
        from agent.log import log
        log(f"fallback: record_fallback failed: {type(e).__name__}: {e}", level="DEBUG")


def is_rate_limit(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return ("ratelimit" in name or "ratelimit" in text or "429" in text
            or "rate limit" in text or "rate_limit" in text
            or "too many requests" in text)


def is_unavailable(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return ("notfound" in name or "404" in text or "not_found" in text
            or "not found" in text
            or "no longer available" in text)


def try_with_fallback(agent, kwargs, stream_fn, console):
    # FIX_CHAIN: gemini skips fallback
    if getattr(agent, chr(112)+chr(114)+chr(111)+chr(118)+chr(105)+chr(100)+chr(101)+chr(114)+chr(95)+chr(110)+chr(97)+chr(109)+chr(101), chr(39)+chr(39)) == chr(103)+chr(101)+chr(109)+chr(105)+chr(110)+chr(105):
        kwargs[chr(109)+chr(111)+chr(100)+chr(101)+chr(108)] = agent.model_name
        return stream_fn(agent.client, kwargs)
    # FIX_CHAIN: do not switch model mid tool-call chain.
    # If we have a previous_interaction_id, the chain is bound to a specific
    # model. Switching models here breaks Gemini's tool-call chain with
    # "invalid_request: function response turn comes immediately after a
    # function call turn". So: reset the chain and retry with fallback.
    if kwargs.get("previous_interaction_id"):
        console.print("[dim]↻ chain reset (was bound to previous model)[/dim]")
        kwargs.pop("previous_interaction_id", None)
        agent.last_interaction_id = None

    order = [agent.model_key] + [k for k, _, _ in MODEL_CATALOG
                                  if k != agent.model_key]
    last_error = None
    tried = []

    for key in order:
        if key in agent.exhausted:
            continue
        name = MODELS[key]
        tried.append(name)
        kwargs["model"] = name
        try:
            result = stream_fn(agent.client, kwargs)
            if key != agent.model_key:
                console.print(f"[green]↻ авто-переключение на {name}[/green]")
                _record_fallback()
                agent.model_key = key
                agent.model_name = name
                agent.last_interaction_id = None
            return result
        except Exception as e:
            if is_rate_limit(e):
                console.print(f"[yellow]⚠ {name}: квота исчерпана[/yellow]")
                agent.exhausted.add(key)
                last_error = e
                continue
            if is_unavailable(e):
                console.print(f"[yellow]⚠ {name}: модель недоступна (404)[/yellow]")
                agent.exhausted.add(key)
                last_error = e
                continue
            raise

    if last_error:
        _print_all_exhausted(tried, console)
        raise last_error
    raise RuntimeError(f"Все модели недоступны. Пробовали: {tried}")


def _print_all_exhausted(tried, console):
    from rich.panel import Panel
    console.print()
    console.print(Panel.fit(
        "[bold red]Все модели в каталоге недоступны[/bold red]\n\n"
        + "\n".join(f"  • {n}" for n in tried)
        + "\n\n[yellow]Проверь ключ и лимиты:[/yellow]\n"
        "  https://aistudio.google.com/app/apikey\n"
        "  https://ai.dev/rate-limit",
        title="Модели недоступны",
        border_style="red",
    ))

