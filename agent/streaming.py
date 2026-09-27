"""Обработка стриминговых событий Interactions API."""

import json
from rich.console import Console

console = Console()

def stream_interaction(client, kwargs):
    interaction_id = None
    text_parts = []
    function_calls = []
    step_map = {}

    stream = client.interactions.create(**kwargs)

    for event in stream:

        etype = getattr(event, "event_type", None)

        # Обработка ошибок API
        if etype == "error":
            err = getattr(event, "error", None)
            code = getattr(err, "code", "unknown") if err else "unknown"
            msg = getattr(err, "message", str(err)) if err else "unknown error"
            raise RuntimeError(f"{code}: {msg}")
        if etype == "interaction.created":
            interaction_id = getattr(event.interaction, "id", None)

        elif etype == "step.start":
            step = getattr(event, "step", None)
            if step and getattr(step, "type", None) == "function_call":
                idx = getattr(event, "index", 0)
                step_map[idx] = {
                    "name": getattr(step, "name", None),
                    "id": getattr(step, "id", None),
                    "args_buffer": "",
                }

        elif etype == "step.delta":
            delta = getattr(event, "delta", None)
            if not delta:
                continue
            dtype = getattr(delta, "type", None)
            if dtype == "text":
                chunk = getattr(delta, "text", "") or ""
                if chunk:
                    text_parts.append(chunk)
                    import sys
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
            elif dtype == "arguments_delta":
                idx = getattr(event, "index", 0)
                if idx in step_map:
                    step_map[idx]["args_buffer"] += getattr(delta, "arguments", "") or ""

        elif etype in ("interaction.completed", "interaction.complete"):
            for info in step_map.values():
                if info.get("name"):
                    raw = info.get("args_buffer") or "{}"
                    try:
                        args = json.loads(raw)
                    except Exception:
                        args = {}
                    function_calls.append({
                        "name": info["name"],
                        "id": info["id"],
                        "arguments": args,
                    })

    return interaction_id, "".join(text_parts), function_calls