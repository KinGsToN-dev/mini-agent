"""/help, /model, /models, /mode, /clear — обработка команд."""

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

from config import MODEL_CATALOG
from tools.shell import set_mode, get_mode
from tools.mt5_trade import (
    get_config_status,
    set_max_lot,
    set_allow_live,
    set_confirm_required,
)
from agent import sessions as sessions_mod
from agent import analytics as analytics_mod
from agent import exporter as exporter_mod
from agent import history as history_mod

console = Console()

# Имена команд REPL — для защиты от ввода без слэша
REPL_COMMAND_NAMES = {
    "help", "tools", "model", "models", "auto", "mode",
    "save", "load", "sessions", "rename", "delete",
    "history", "stats", "export", "find", "forget",
    "clear", "exit", "quit",
}


def looks_like_repl_command(user_input: str) -> str | None:
    """
    Если ввод похож на команду REPL без слэша — возвращает имя команды.
    Иначе None.
    """
    parts = user_input.strip().split(maxsplit=1)
    if not parts:
        return None
    first = parts[0].lower()
    if first in REPL_COMMAND_NAMES:
        return first
    return None


HELP_TEXT = """[bold]Команды:[/bold]
  /help            — справка
  /tools           — список доступных инструментов
  /model <name>    — сменить модель вручную
  /model           — текущая модель
  /models          — список моделей и их статус
  /auto on|off     — авто-выбор модели под задачу (роутер)
  /auto            — состояние роутера
  /mode <m>        — режим безопасности: ask | auto | dry
  /mode            — текущий режим
  /save <имя>      — сохранить текущую сессию
  /load <имя>      — загрузить сессию
  /sessions        — список сохранённых сессий
  /rename <старое> <новое> — переименовать сессию
  /delete <имя>    — удалить сессию
  /history [N]     — последние N сообщений (по умолчанию 10)
  /stats           — статистика текущей сессии
  /export <файл>   — экспорт последней сессии в Markdown (полный)
  /find <текст>    — поиск по всем сообщениям сессий
  /forget          — сбросить кэш исчерпанных моделей
  /clear           — очистить экран
  /trade           — статус торговых настроек MT5
  /confirm on|off  — подтверждение торговых операций
  /limit <value>   — лимит объёма в лотах
  /live on|off     — разрешить торговлю на LIVE-аккаунте
  /exit, /quit     — выход (автосохранение последней сессии)

[bold]Режимы безопасности:[/bold]
  ask  — спрашивать подтверждение для «серых» команд (по умолчанию)
  auto — выполнять всё, кроме чёрного списка
  dry  — ничего не выполнять, только показывать команды

[bold]Роутер моделей:[/bold]
  При включённом /auto on агент сам выбирает модель под задачу:
    simple  → lite-3.5    (большая квота, быстрые ответы)
    medium  → flash-3.5   (код, файлы, генерация)
    complex → pro         (аналитика, сложные рассуждения)

[bold]Кэш моделей:[/bold]
  Агент запоминает модели с исчерпанной квотой (429) и удалённые (404).
  Сбрасывается автоматически в полночь (PT) или вручную через /forget.
"""


def ask_confirmation(command: str, dangerous: bool = False) -> bool:
    """Подтверждение команды. Если dangerous=True — красная панель."""
    console.print()
    if dangerous:
        console.print(Panel.fit(
            f"[bold red]{command}[/bold red]",
            title="🚨 ОПАСНАЯ КОМАНДА",
            border_style="red",
        ))
        console.print("[red]Эта команда может рекурсивно удалить данные.[/red]")
    else:
        console.print(Panel.fit(
            f"[bold yellow]{command}[/bold yellow]",
            title="⚠️  Подтверждение команды",
            border_style="yellow",
        ))
    answer = Prompt.ask("[bold]Выполнить?[/bold] [dim](y/N)[/dim]",
                        default="n").strip().lower()
    return answer in ("y", "yes", "д", "да")


def print_models(agent):
    table = Table(title="Модели", show_lines=False)
    table.add_column("ключ", style="cyan")
    table.add_column("имя", style="white")
    table.add_column("статус", style="white")
    for key, name, _ in MODEL_CATALOG:
        if key == agent.model_key:
            status = "[green]← текущая[/green]"
        elif key in agent.exhausted:
            status = "[red]недоступна[/red]"
        else:
            status = "[dim]не использована[/dim]"
        table.add_row(key, name, status)
    console.print(table)


def print_sessions():
    sessions = sessions_mod.list_sessions()
    if not sessions:
        console.print("[dim]Нет сохранённых сессий.[/dim]")
        return
    table = Table(title="Сессии", show_lines=False)
    table.add_column("имя", style="cyan")
    table.add_column("обновлена", style="white")
    table.add_column("модель", style="white")
    table.add_column("сообщений", style="white", justify="right")
    table.add_column("превью", style="dim")
    for s in sessions:
        preview = (s["preview"] or "")[:40]
        table.add_row(
            s["name"],
            s["updated"],
            s["model"],
            str(s["message_count"]),
            preview,
        )
    console.print(table)


def print_stats():
    s = analytics_mod.get().summary()
    table = Table(title="Статистика сессии", show_lines=False)
    table.add_column("метрика", style="cyan")
    table.add_column("значение", style="white", justify="right")

    mins, secs = divmod(int(s["uptime_sec"]), 60)
    table.add_row("время работы", f"{mins}м {secs}с")
    table.add_row("запросов", str(s["requests"]))
    table.add_row("tool-calls", str(s["tool_calls"]))
    table.add_row("fallback-переключений", str(s["fallbacks"]))
    table.add_row("среднее время ответа", f"{s['avg_time']:.2f}с")
    table.add_row("быстрейший ответ", f"{s['fastest']:.2f}с")
    table.add_row("медленнейший ответ", f"{s['slowest']:.2f}с")

    console.print(table)
    if s["models"]:
        console.print()
        mt = Table(title="Использование моделей", show_lines=False)
        mt.add_column("модель", style="cyan")
        mt.add_column("запросов", style="white", justify="right")
        for name, count in sorted(s["models"].items(), key=lambda x: -x[1]):
            mt.add_row(name, str(count))
        console.print(mt)


def find_in_sessions(query: str) -> int:
    """Ищет query во всех сообщениях сохранённых сессий."""
    hits = history_mod.find_in_messages(query)
    for h in hits[:20]:
        role_icon = "👤" if h["role"] == "user" else "🤖"
        text = h["text"].replace("\n", " ")[:120]
        console.print(
            f"  {role_icon} [cyan]{h['session']}[/cyan] "
            f"[dim]{h['ts']}[/dim]: {text}"
        )
    if len(hits) > 20:
        console.print(f"  [dim]...[ещё {len(hits) - 20}][/dim]")
    return len(hits)


def print_tools():
    """Показывает список инструментов и их назначение."""
    from tools.registry import TOOL_FUNCTIONS
    from tools.registry import TOOL_SCHEMAS

    # Описания из схем
    desc_map = {}
    for schema in TOOL_SCHEMAS:
        name = schema.get("name")
        desc = schema.get("description", "")
        if name:
            desc_map[name] = desc

    table = Table(title="Доступные инструменты", show_lines=True)
    table.add_column("инструмент", style="cyan", no_wrap=True)
    table.add_column("назначение", style="white")

    for name in sorted(TOOL_FUNCTIONS.keys()):
        desc = desc_map.get(name, "—")
        # Обрезаем длинные описания
        if len(desc) > 120:
            desc = desc[:117] + "..."
        table.add_row(name, desc)

    console.print(table)
    console.print(f"\n[dim]Всего инструментов: {len(TOOL_FUNCTIONS)}[/dim]")


def print_history(agent, count: int = 10):
    """Показывает последние N сообщений текущей сессии."""
    name = agent.current_session_name or sessions_mod.get_last_name()
    if not name:
        console.print("[yellow]Нет активной сессии[/yellow]")
        return
    messages = history_mod.load_messages(name)
    if not messages:
        console.print(f"[dim]Сессия '{name}' пуста[/dim]")
        return

    tail = messages[-count:]
    console.print(f"[dim]Последние {len(tail)} из {len(messages)} сообщений "
                  f"сессии '{name}':[/dim]\n")
    for msg in tail:
        role = msg.get("role")
        ts = msg.get("ts", "")[11:]  # только время
        text = msg.get("text", "").replace("\n", " ")
        if len(text) > 300:
            text = text[:300] + "..."
        if role == "user":
            console.print(f"[bold blue]👤 you[/bold blue] [dim]{ts}[/dim]")
        else:
            console.print(f"[bold magenta]🤖 agent[/bold magenta] [dim]{ts}[/dim]")
        console.print(f"  {text}\n")


def handle_command(user_input: str, agent) -> bool:
    if user_input in ("/exit", "/quit"):
        console.print("[dim]Выход.[/dim]")
        raise SystemExit(0)

    if user_input == "/help":
        console.print(HELP_TEXT)
        return True

    if user_input == "/clear":
        # Просто очищаем экран — контекст сессии сохраняется
        import os as _os
        _os.system("cls" if _os.name == "nt" else "clear")
        console.print("[dim]Экран очищен (контекст диалога сохранён).[/dim]")
        return True

    if user_input == "/tools":
        print_tools()
        return True

    if user_input.startswith("/delete"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            console.print("[yellow]Использование: /delete <имя>[/yellow]")
            return True
        name = parts[1].strip()
        # Подтверждение
        ans = Prompt.ask(f"[bold red]Удалить сессию '{name}'?[/bold red] "
                        f"[dim](y/N)[/dim]", default="n").strip().lower()
        if ans not in ("y", "yes", "д", "да"):
            console.print("[dim]Отменено.[/dim]")
            return True
        try:
            sessions_mod.delete_session(name)
            console.print(f"[green]Сессия удалена:[/green] {name}")
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Ошибка:[/red] {e}")
        return True

    if user_input.startswith("/rename"):
        parts = user_input.split(maxsplit=2)
        if len(parts) < 3:
            console.print("[yellow]Использование: /rename <старое> <новое>[/yellow]")
            return True
        old_name, new_name = parts[1].strip(), parts[2].strip()
        try:
            result = sessions_mod.rename_session(old_name, new_name)
            console.print(f"[green]Переименовано:[/green] {old_name} → {result}")
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
        except FileExistsError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Ошибка:[/red] {e}")
        return True

    if user_input == "/forget":
        agent.forget_exhausted()
        return True

    if user_input == "/trade":
        console.print("[bold]Торговые настройки MT5:[/bold]")
        console.print(get_config_status())
        console.print()
        console.print("[dim]Пример: 'купи 0.01 BTCUSD с SL 84000 и TP 86000'[/dim]")
        return True

    if user_input.startswith("/confirm"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            lines = get_config_status().split("\n")
            console.print(f"[cyan]{lines[2] if len(lines) > 2 else '?'}[/cyan]")
        else:
            arg = parts[1].strip().lower()
            if arg in ("on", "yes", "true", "вкл", "включить"):
                set_confirm_required(True)
                console.print("[green]Подтверждение: ВКЛ[/green]")
            elif arg in ("off", "no", "false", "выкл", "выключить"):
                set_confirm_required(False)
                console.print("[yellow]Подтверждение: ВЫКЛ (ордера сразу!)[/yellow]")
            else:
                console.print("[red]Использование: /confirm on | /confirm off[/red]")
        return True

    if user_input.startswith("/limit"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            lines = get_config_status().split("\n")
            console.print(f"[cyan]{lines[0] if len(lines) > 0 else '?'}[/cyan]")
        else:
            try:
                value = float(parts[1].strip())
                if value <= 0:
                    console.print("[red]Лимит должен быть > 0[/red]")
                else:
                    set_max_lot(value)
                    console.print(f"[green]MAX_LOT: {value}[/green]")
            except ValueError:
                console.print("[red]Использование: /limit <число>[/red]")
        return True

    if user_input.startswith("/live"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            lines = get_config_status().split("\n")
            console.print(f"[cyan]{lines[1] if len(lines) > 1 else '?'}[/cyan]")
        else:
            arg = parts[1].strip().lower()
            if arg in ("on", "yes", "true", "вкл", "включить"):
                set_allow_live(True)
                console.print("[red]LIVE-торговля РАЗРЕШЕНА![/red]")
            elif arg in ("off", "no", "false", "выкл", "выключить"):
                set_allow_live(False)
                console.print("[green]LIVE-торговля заблокирована[/green]")
            else:
                console.print("[red]Использование: /live on | /live off[/red]")
        return True

    if user_input.startswith("/history"):
        parts = user_input.split(maxsplit=1)
        n = 10
        if len(parts) > 1:
            try:
                n = int(parts[1].strip())
            except ValueError:
                console.print("[red]Использование: /history [N][/red]")
                return True
        print_history(agent, n)
        return True

    if user_input.startswith("/auto"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            state = "[green]включён[/green]" if agent.auto_route else "[yellow]выключен[/yellow]"
            console.print(f"Роутер моделей: {state}")
        else:
            arg = parts[1].strip().lower()
            if arg in ("on", "вкл", "включить", "yes", "true"):
                agent.set_auto_route(True)
                console.print("[green]Роутер включён[/green]")
            elif arg in ("off", "выкл", "выключить", "no", "false"):
                agent.set_auto_route(False)
                console.print("[yellow]Роутер выключен[/yellow]")
            else:
                console.print("[red]Использование: /auto on | /auto off[/red]")
        return True

    if user_input.startswith("/save"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            console.print("[yellow]Использование: /save <имя>[/yellow]")
            return True
        name = parts[1].strip()
        try:
            path = sessions_mod.save_session(name, agent)
            console.print(f"[green]Сессия сохранена:[/green] {name} → {path}")
        except Exception as e:
            console.print(f"[red]Ошибка сохранения:[/red] {e}")
        return True

    if user_input.startswith("/load"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            console.print("[yellow]Использование: /load <имя>[/yellow]")
            return True
        name = parts[1].strip()
        try:
            data = sessions_mod.load_session(name, agent)
            console.print(f"[green]Сессия загружена:[/green] {name} "
                          f"(модель: {data.get('model')}, "
                          f"сообщений: {data.get('message_count')})")
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Ошибка загрузки:[/red] {e}")
        return True

    if user_input == "/sessions":
        print_sessions()
        return True

    if user_input == "/stats":
        print_stats()
        return True

    if user_input.startswith("/export"):
        parts = user_input.split(maxsplit=1)
        out = parts[1].strip() if len(parts) > 1 else "export.md"
        # Берём последнюю активную сессию
        last_name = sessions_mod.get_last_name()
        if not last_name:
            console.print("[yellow]Нет активной сессии для экспорта[/yellow]")
            return True
        try:
            path = exporter_mod.export_session(last_name, out)
            console.print(f"[green]Экспортировано:[/green] {path}")
        except Exception as e:
            console.print(f"[red]Ошибка экспорта:[/red] {e}")
        return True

    if user_input.startswith("/find"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            console.print("[yellow]Использование: /find <текст>[/yellow]")
            return True
        query = parts[1].strip()
        console.print(f"[dim]Поиск '{query}' в сессиях:[/dim]")
        hits = find_in_sessions(query)
        console.print(f"[dim]Найдено: {hits}[/dim]")
        return True

    if user_input == "/models":
        print_models(agent)
        return True

    if user_input.startswith("/router"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            state = "[green]включён[/green]" if agent.router_enabled else "[yellow]выключен[/yellow]"
            console.print(f"Роутер провайдеров: {state}")
            console.print("[dim]on — авто-выбор | off — только вручную через /provider[/dim]")
        else:
            arg = parts[1].strip().lower()
            if arg in ("on", "вкл", "включить", "yes", "true"):
                agent.router_enabled = True
                console.print("[green]Роутер включён[/green]")
            elif arg in ("off", "выкл", "выключить", "no", "false"):
                agent.router_enabled = False
                console.print("[yellow]Роутер выключен[/yellow]")
            else:
                console.print("[red]Использование: /router on | /router off[/red]")
        return True

    if user_input.startswith("/provider"):
        from providers import registry as provider_registry
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            console.print(f"Текущий провайдер: [cyan]{agent.provider_name}[/cyan]")
            console.print(f"[dim]Доступные: {', '.join(provider_registry.available_providers())}[/dim]")
        else:
            new_provider = parts[1].strip().lower()
            try:
                name, model = agent.switch_provider(new_provider)
                console.print(f"[green]Провайдер:[/green] {name}, "
                              f"модель по умолчанию: {model}")
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
        return True

    if user_input.startswith("/model"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            console.print(f"Текущая модель: [cyan]{agent.model_name}[/cyan] "
                          f"(ключ: {agent.model_key})")
        else:
            try:
                new_name = agent.switch_model(parts[1].strip())
                console.print(f"[green]Модель переключена:[/green] {new_name}")
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
        return True

    if user_input.startswith("/mode"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1:
            console.print(f"Текущий режим: [cyan]{get_mode()}[/cyan]")
        else:
            try:
                set_mode(parts[1].strip().lower())
                console.print(f"[green]Режим:[/green] {get_mode()}")
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
        return True

    return False








