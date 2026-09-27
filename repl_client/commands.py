"""Команды REPL-клиента (через HTTP)."""

from rich.console import Console
from rich.table import Table

from repl_client.client import AgentClient, AgentClientError

console = Console()


HELP_TEXT = """[bold]Команды REPL-клиента:[/bold]
  /help            — справка
  /status          — статус сервера (провайдер, модель, режим)
  /providers       — список провайдеров и их доступность
  /provider <name> — сменить провайдера (gemini | groq | mistral | openrouter)
  /provider        — текущий провайдер
  /model <name>    — сменить модель в текущем провайдере
  /model           — текущая модель
  /reset           — сбросить сессию (забыть историю диалога)
  /forget          — сбросить кэш исчерпанных моделей
  /exit, /quit     — выход из клиента (сервер остаётся работать)

[dim]Сервер работает в отдельном процессе. Клиент только общается по HTTP.[/dim]
"""


def handle_command(user_input: str, client: AgentClient) -> bool:
    """
    Обрабатывает команду.
    Возвращает True, если команда обработана.
    Бросает SystemExit при /exit.
    """
    if user_input in ("/exit", "/quit"):
        console.print("[dim]Выход из клиента. Сервер продолжает работать.[/dim]")
        raise SystemExit(0)

    if user_input == "/help":
        console.print(HELP_TEXT)
        return True

    if user_input == "/status":
        try:
            s = client.status()
        except AgentClientError as e:
            console.print(f"[red]{e}[/red]")
            return True
        console.print(
            f"[cyan]Провайдер:[/cyan] {s.get('provider')}\n"
            f"[cyan]Модель:[/cyan]    {s.get('model')}\n"
            f"[cyan]Режим:[/cyan]     {s.get('mode')}\n"
            f"[cyan]Роутер:[/cyan]    {s.get('router_enabled')}\n"
            f"[cyan]Сессий:[/cyan]    {s.get('sessions')}"
        )
        return True

    if user_input == "/providers":
        try:
            data = client.providers()
        except AgentClientError as e:
            console.print(f"[red]{e}[/red]")
            return True

        table = Table(title=f"Провайдеры (текущий: {data.get('current')})")
        table.add_column("Провайдер", style="cyan")
        table.add_column("Доступен", justify="center")
        table.add_column("Текущий", justify="center")

        for p in data.get("providers", []):
            available = "✅" if p.get("available") else "❌"
            current = "← " if p.get("is_current") else ""
            table.add_row(p.get("name", "?"), available, current)

        console.print(table)
        return True

    if user_input.startswith("/provider"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            try:
                s = client.status()
                console.print(f"Текущий провайдер: [cyan]{s.get('provider')}[/cyan]")
            except AgentClientError as e:
                console.print(f"[red]{e}[/red]")
            return True

        provider = parts[1].strip()
        try:
            data = client.switch_provider(provider)
            console.print(f"[green]Провайдер:[/green] {data.get('provider')}, "
                          f"модель: [cyan]{data.get('model')}[/cyan]")
        except AgentClientError as e:
            console.print(f"[red]{e}[/red]")
        return True

    if user_input.startswith("/model"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            try:
                s = client.status()
                console.print(f"Текущая модель: [cyan]{s.get('model')}[/cyan] "
                              f"(провайдер: {s.get('provider')})")
            except AgentClientError as e:
                console.print(f"[red]{e}[/red]")
            return True

        model = parts[1].strip()
        try:
            data = client.switch_model(model)
            console.print(f"[green]Модель:[/green] {data.get('model')} "
                          f"(провайдер: {data.get('provider')})")
        except AgentClientError as e:
            console.print(f"[red]{e}[/red]")
        return True

    if user_input == "/reset":
        try:
            data = client.reset()
            existed = data.get("existed", False)
            if existed:
                console.print("[green]Сессия сброшена.[/green]")
            else:
                console.print("[dim]Сессия не найдена (уже пустая).[/dim]")
        except AgentClientError as e:
            console.print(f"[red]{e}[/red]")
        return True

    if user_input == "/forget":
        try:
            data = client.forget()
            count = data.get("cleared_sessions", 0)
            console.print(f"[green]Кэш исчерпанных моделей сброшен "
                          f"({count} сессий).[/green]")
        except AgentClientError as e:
            console.print(f"[red]{e}[/red]")
        return True

    return False
