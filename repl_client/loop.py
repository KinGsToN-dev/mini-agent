"""Главный цикл REPL-клиента."""

from rich.console import Console
from rich.prompt import Prompt

from repl_client.client import AgentClient, AgentClientError
from repl_client.commands import handle_command

console = Console()


def run_client_repl(base_url: str = "http://127.0.0.1:8765"):
    """Главный цикл REPL-клиента."""
    client = AgentClient(base_url=base_url)

    # 1. Проверка доступности сервера
    console.print(f"[dim]Проверяю сервер: {base_url}...[/dim]")
    if not client.is_alive():
        console.print()
        console.print("[bold red]❌ Сервер недоступен[/bold red]")
        console.print(f"   URL: {base_url}")
        console.print()
        console.print("[yellow]Запусти сервер в отдельном терминале:[/yellow]")
        console.print(f"   [cyan]python scripts/run_agent_server.py[/cyan]")
        console.print()
        raise SystemExit(1)

    # 2. Получаем статус
    try:
        s = client.status()
    except AgentClientError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1)

    console.print(
        f"[bold green]REPL-клиент подключён[/bold green] к {base_url}\n"
        f"Провайдер: [cyan]{s.get('provider')}[/cyan] | "
        f"Модель: [cyan]{s.get('model')}[/cyan] | "
        f"Режим: [cyan]{s.get('mode')}[/cyan]\n"
        f"Введите [bold]/help[/bold] для списка команд.\n"
    )

    # 3. REPL
    try:
        while True:
            try:
                user_input = Prompt.ask("[bold blue]you[/bold blue]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Выход.[/dim]")
                break

            if not user_input:
                continue

            # Команды
            if user_input.startswith("/"):
                try:
                    handle_command(user_input, client)
                except SystemExit:
                    break
                continue

            # Обычный запрос
            try:
                with console.status("[dim]думаю...[/dim]", spinner="dots"):
                    data = client.ask(user_input)
                answer = data.get("answer", "(пустой ответ)")
                console.print("[bold magenta]agent[/bold magenta]:")
                console.print(answer)
                console.print(
                    f"[dim](провайдер: {data.get('provider')}, "
                    f"модель: {data.get('model')}, "
                    f"{data.get('duration_ms')} мс)[/dim]"
                )
                console.print()
            except AgentClientError as e:
                console.print(f"[red]{e}[/red]")
                console.print()
    finally:
        console.print("[dim]Сессия клиента завершена.[/dim]")
