"""Главный REPL-цикл агента."""

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from agent import GeminiAgent
from agent import sessions as sessions_mod
from tools.shell import get_mode, set_confirm_callback
from repl.commands import handle_command, ask_confirmation, looks_like_repl_command

console = Console()


def run_repl(api_key: str):
    agent = GeminiAgent(api_key=api_key)
    set_confirm_callback(ask_confirmation)

    console.print(
        "[bold green]Мини-агент запущен.[/bold green] "
        f"Модель: [cyan]{agent.model_name}[/cyan]. "
        f"Режим: [cyan]{get_mode()}[/cyan]. Введите /help.\n"
    )

    # Если есть последняя сессия — предложить загрузить
    last = sessions_mod.get_last_name()
    if last:
        console.print(f"[dim]💾 Последняя сессия: '{last}'. "
                      f"Загрузить командой /load {last}[/dim]\n")

    try:
        while True:
            try:
                user_input = Prompt.ask("[bold blue]you[/bold blue]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Выход.[/dim]")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                try:
                    handle_command(user_input, agent)
                except SystemExit:
                    break
                continue

            # Защита: если ввод похож на команду REPL без слэша — предупредить
            guess = looks_like_repl_command(user_input)
            if guess:
                console.print()
                console.print(Panel.fit(
                    f"[yellow]Ты написал '[bold]{guess}[/bold]' без слэша.[/yellow]\n\n"
                    f"Команда REPL: [bold]/ {guess}[/bold]\n"
                    f"Отправить как [bold]запрос к модели[/bold] (она может выполнить что-то через shell)?",
                    title="⚠️  Возможно команда",
                    border_style="yellow",
                ))
                ans = Prompt.ask("[bold]Продолжить как запрос к модели?[/bold] "
                                "[dim](y/N)[/dim]", default="n").strip().lower()
                if ans not in ("y", "yes", "д", "да"):
                    console.print("[dim]Отменено. Используй слэш для команды.[/dim]\n")
                    continue
                console.print()

            try:
                import time as _time
                console.print("[bold magenta]agent[/bold magenta]: ", end="")
                _t0 = _time.time()
                agent.ask(user_input)
                _dt = _time.time() - _t0
                from agent import analytics as _a
                _a.get().record_request(agent.model_name, _dt)
                console.print()
                console.print()
            except Exception as e:
                if "rate" not in str(e).lower() and "429" not in str(e):
                    console.print(f"[red]Ошибка:[/red] {type(e).__name__}: {e}")
    finally:
        # Сохраняем кэш исчерпанных моделей
        agent.save_state()
        # Автосохранение активной сессии
        sessions_mod.autosave(agent)



