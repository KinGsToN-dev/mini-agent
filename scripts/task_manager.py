"""
Управление задачами Windows Task Scheduler.

Поддерживает несколько задач:
    briefing — утренний брифинг (04:00)
    monitor  — мониторинг позиций (каждый час)

Использование:
    python scripts/task_manager.py create --task-name briefing --time 04:00
    python scripts/task_manager.py create --task-name monitor --interval hourly
    python scripts/task_manager.py delete --task-name briefing
    python scripts/task_manager.py enable --task-name monitor
    python scripts/task_manager.py disable --task-name monitor
    python scripts/task_manager.py status --task-name briefing
    python scripts/task_manager.py run-now --task-name monitor
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()
PYTHON_EXE = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"


# ============================================================
# Реестр задач
# ============================================================
TASKS = {
    "briefing": {
        "name": "Mini-Agent Morning Briefing",
        "script": "daily_briefing.py",
        "default_time": "04:00",
        "default_interval": "daily",
        "description": "Утренний брифинг",
    },
    "monitor": {
        "name": "Mini-Agent Position Monitor",
        "script": "position_monitor.py",
        "default_time": "00:00",
        "default_interval": "hourly",
        "description": "Мониторинг позиций MT5",
    },
}


def get_task(task_key: str) -> dict:
    if task_key not in TASKS:
        print(f"[ERROR] Неизвестная задача: {task_key}")
        print(f"        Доступные: {list(TASKS.keys())}")
        sys.exit(1)
    return TASKS[task_key]


# ============================================================
# Хелперы
# ============================================================
def _run_schtasks(args: list, check: bool = True) -> tuple:
    cmd = ["schtasks"] + args
    result = subprocess.run(cmd, capture_output=True, text=False)
    if check and result.returncode != 0:
        print(f"[ERROR] schtasks вернул код {result.returncode}")
    return result.returncode, result.stdout, result.stderr


def _task_exists(task_name: str) -> bool:
    code, _, _ = _run_schtasks(["/Query", "/TN", task_name], check=False)
    return code == 0


def _check_paths(script_path: Path):
    errors = []
    if not PYTHON_EXE.exists():
        errors.append(f"Python не найден: {PYTHON_EXE}")
    if not script_path.exists():
        errors.append(f"Скрипт не найден: {script_path}")
    if errors:
        for e in errors:
            print(f"[ERROR] {e}")
        sys.exit(1)


def _read_task_xml(task_name: str):
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", task_name, "/XML"],
        capture_output=True, text=False,
    )
    if result.returncode != 0:
        return None
    raw = result.stdout
    if raw.startswith(b"\xff\xfe"):
        xml = raw[2:].decode("utf-16-le")
    elif raw.startswith(b"\xfe\xff"):
        xml = raw[2:].decode("utf-16-be")
    else:
        try:
            xml = raw.decode("utf-8")
        except UnicodeDecodeError:
            xml = raw.decode("cp866", errors="replace")
    return xml.lstrip("\ufeff")


def _patch_task_xml(task_name: str, wake: bool):
    """Патчит XML: WakeToRun + WorkingDirectory."""
    xml = _read_task_xml(task_name)
    if not xml:
        print("[patch] Не удалось прочитать XML")
        return

    changes = []
    NL = chr(10)

    if wake and "<WakeToRun>true</WakeToRun>" not in xml:
        xml = xml.replace(
            "<Settings>",
            "<Settings>" + NL + "    <WakeToRun>true</WakeToRun>",
            1,
        )
        changes.append("WakeToRun")

    if "<WorkingDirectory>" not in xml:
        work_dir = str(PROJECT_DIR)
        insert = "</Command>" + NL + "      <WorkingDirectory>" + work_dir + "</WorkingDirectory>"
        xml = xml.replace("</Command>", insert, 1)
        changes.append("WorkingDirectory")

    if not changes:
        print("[patch] Задача уже настроена")
        return

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-16"
    )
    tmp.write(xml)
    tmp.close()

    code, _, _ = _run_schtasks(["/Create", "/TN", task_name, "/XML", tmp.name, "/F"])
    try:
        os.unlink(tmp.name)
    except Exception:
        pass

    if code == 0:
        print(f"[patch] Обновлено: {', '.join(changes)}")
    else:
        print("[patch] Не удалось обновить")


# ============================================================
# Команды
# ============================================================
def cmd_create(args):
    task = get_task(args.task_name)
    task_name = task["name"]
    script_path = PROJECT_DIR / "scripts" / task["script"]

    _check_paths(script_path)

    time_val = args.time or task["default_time"]
    interval = args.interval or task["default_interval"]

    print(f"[create] Создание задачи '{task_name}'")
    print(f"         Описание: {task['description']}")
    print(f"         Скрипт: {task['script']}")
    print(f"         Расписание: {interval}")
    if interval == "daily":
        print(f"         Время: {time_val}")

    # Удаляем старую если есть
    if _task_exists(task_name):
        print("[create] Задача существует, удаляю...")
        _run_schtasks(["/Delete", "/TN", task_name, "/F"])

    tr = f'"{PYTHON_EXE}" "{script_path}"'

    if interval == "hourly":
        schtasks_args = [
            "/Create", "/TN", task_name, "/TR", tr,
            "/SC", "HOURLY", "/MO", "1", "/RL", "HIGHEST", "/F",
        ]
    else:  # daily
        schtasks_args = [
            "/Create", "/TN", task_name, "/TR", tr,
            "/SC", "DAILY", "/ST", time_val, "/RL", "HIGHEST", "/F",
        ]
        if args.days == "WEEKDAYS":
            schtasks_args.extend(["/D", "MON,TUE,WED,THU,FRI"])

    code, _, _ = _run_schtasks(schtasks_args)
    if code != 0:
        print("[create] Не удалось создать задачу")
        return

    print("[create] Базовая задача создана")
    _patch_task_xml(task_name, wake=args.wake)


def cmd_delete(args):
    task = get_task(args.task_name)
    task_name = task["name"]

    if not _task_exists(task_name):
        print(f"[delete] Задача '{task_name}' не существует")
        return
    code, _, _ = _run_schtasks(["/Delete", "/TN", task_name, "/F"])
    if code == 0:
        print(f"[delete] Задача '{task_name}' удалена")


def cmd_enable(args):
    task = get_task(args.task_name)
    task_name = task["name"]
    if not _task_exists(task_name):
        print(f"[enable] Задача '{task_name}' не существует")
        return
    code, _, _ = _run_schtasks(["/Change", "/TN", task_name, "/ENABLE"])
    if code == 0:
        print(f"[enable] Задача '{task_name}' включена")


def cmd_disable(args):
    task = get_task(args.task_name)
    task_name = task["name"]
    if not _task_exists(task_name):
        print(f"[disable] Задача '{task_name}' не существует")
        return
    code, _, _ = _run_schtasks(["/Change", "/TN", task_name, "/DISABLE"])
    if code == 0:
        print(f"[disable] Задача '{task_name}' отключена")


def cmd_status(args):
    task = get_task(args.task_name)
    task_name = task["name"]

    if not _task_exists(task_name):
        print(f"[status] Задача '{task_name}' не создана")
        return

    print(f"[status] Задача '{task_name}':")
    print()

    result = subprocess.run(
        ["schtasks", "/Query", "/TN", task_name, "/V", "/FO", "LIST"],
        capture_output=True, text=False,
    )
    output = result.stdout.decode("cp866", errors="replace")
    for line in output.splitlines():
        line = line.strip()
        if line:
            print(f"  {line}")


def cmd_change_time(args):
    task = get_task(args.task_name)
    task_name = task["name"]

    if not _task_exists(task_name):
        print(f"[change-time] Задача '{task_name}' не существует")
        return

    print(f"[change-time] Меняю время на {args.time}")

    # Пересоздаём
    _run_schtasks(["/Delete", "/TN", task_name, "/F"])
    create_args = argparse.Namespace(
        task_name=args.task_name,
        time=args.time,
        wake=True,
        days=args.days or "DAILY",
        interval=task["default_interval"],
    )
    cmd_create(create_args)


def cmd_run_now(args):
    task = get_task(args.task_name)
    task_name = task["name"]

    if not _task_exists(task_name):
        print(f"[run-now] Задача '{task_name}' не существует")
        return
    code, _, _ = _run_schtasks(["/Run", "/TN", task_name])
    if code == 0:
        print(f"[run-now] Задача '{task_name}' запущена")


def cmd_list(args):
    """Список всех задач из реестра с их статусом."""
    print("Доступные задачи:")
    print()
    for key, task in TASKS.items():
        exists = _task_exists(task["name"])
        status = "создана" if exists else "не создана"
        print(f"  {key}: {task['name']}")
        print(f"      Описание: {task['description']}")
        print(f"      Скрипт: {task['script']}")
        print(f"      Интервал: {task['default_interval']}")
        print(f"      Статус: {status}")
        print()


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Управление задачами Task Scheduler")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create")
    p_create.add_argument("--task-name", default="briefing", choices=list(TASKS.keys()))
    p_create.add_argument("--time", default=None)
    p_create.add_argument("--wake", action="store_true", default=True)
    p_create.add_argument("--no-wake", dest="wake", action="store_false")
    p_create.add_argument("--days", default="DAILY", choices=["DAILY", "WEEKDAYS"])
    p_create.add_argument("--interval", default=None, choices=["daily", "hourly"])
    p_create.set_defaults(func=cmd_create)

    # delete
    p_del = sub.add_parser("delete")
    p_del.add_argument("--task-name", default="briefing", choices=list(TASKS.keys()))
    p_del.set_defaults(func=cmd_delete)

    # enable
    p_en = sub.add_parser("enable")
    p_en.add_argument("--task-name", default="briefing", choices=list(TASKS.keys()))
    p_en.set_defaults(func=cmd_enable)

    # disable
    p_dis = sub.add_parser("disable")
    p_dis.add_argument("--task-name", default="briefing", choices=list(TASKS.keys()))
    p_dis.set_defaults(func=cmd_disable)

    # status
    p_st = sub.add_parser("status")
    p_st.add_argument("--task-name", default="briefing", choices=list(TASKS.keys()))
    p_st.set_defaults(func=cmd_status)

    # change-time
    p_change = sub.add_parser("change-time")
    p_change.add_argument("time")
    p_change.add_argument("--task-name", default="briefing", choices=list(TASKS.keys()))
    p_change.add_argument("--days", default="DAILY", choices=["DAILY", "WEEKDAYS"])
    p_change.set_defaults(func=cmd_change_time)

    # run-now
    p_run = sub.add_parser("run-now")
    p_run.add_argument("--task-name", default="briefing", choices=list(TASKS.keys()))
    p_run.set_defaults(func=cmd_run_now)

    # list
    sub.add_parser("list").set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()