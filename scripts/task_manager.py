"""
Управление задачей Windows Task Scheduler для утреннего брифинга.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_NAME = "Mini-Agent Morning Briefing"
PROJECT_DIR = Path(__file__).parent.parent.resolve()
PYTHON_EXE = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
SCRIPT = PROJECT_DIR / "scripts" / "daily_briefing.py"


def _run_schtasks(args, check=True):
    cmd = ["schtasks"] + args
    result = subprocess.run(cmd, capture_output=True, text=False)
    if check and result.returncode != 0:
        print(f"[ERROR] schtasks вернул код {result.returncode}")
    return result.returncode, result.stdout, result.stderr


def _task_exists():
    code, _, _ = _run_schtasks(["/Query", "/TN", TASK_NAME], check=False)
    return code == 0


def _check_paths():
    errors = []
    if not PYTHON_EXE.exists():
        errors.append(f"Python не найден: {PYTHON_EXE}")
    if not SCRIPT.exists():
        errors.append(f"Скрипт не найден: {SCRIPT}")
    if errors:
        for e in errors:
            print(f"[ERROR] {e}")
        sys.exit(1)


def _read_task_xml():
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/XML"],
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


def _patch_task_xml(wake):
    xml = _read_task_xml()
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

    code, _, _ = _run_schtasks(["/Create", "/TN", TASK_NAME, "/XML", tmp.name, "/F"])
    try:
        os.unlink(tmp.name)
    except Exception:
        pass

    if code == 0:
        print(f"[patch] Обновлено: {', '.join(changes)}")
    else:
        print("[patch] Не удалось обновить")


def cmd_create(args):
    _check_paths()
    print(f"[create] Создание задачи '{TASK_NAME}'")
    print(f"         Время: {args.time}")
    print(f"         Wake: {'да' if args.wake else 'нет'}")

    if _task_exists():
        cmd_delete(args)

    tr = f'"{PYTHON_EXE}" "{SCRIPT}"'
    schtasks_args = [
        "/Create", "/TN", TASK_NAME, "/TR", tr,
        "/SC", "DAILY", "/ST", args.time, "/RL", "HIGHEST", "/F",
    ]
    if args.days == "WEEKDAYS":
        schtasks_args.extend(["/D", "MON,TUE,WED,THU,FRI"])

    code, _, _ = _run_schtasks(schtasks_args)
    if code != 0:
        print("[create] Не удалось создать задачу")
        return
    print("[create] Базовая задача создана")
    _patch_task_xml(wake=args.wake)


def cmd_delete(args):
    if not _task_exists():
        print(f"[delete] Задача '{TASK_NAME}' не существует")
        return
    code, _, _ = _run_schtasks(["/Delete", "/TN", TASK_NAME, "/F"])
    if code == 0:
        print(f"[delete] Задача '{TASK_NAME}' удалена")


def cmd_enable(args):
    code, _, _ = _run_schtasks(["/Change", "/TN", TASK_NAME, "/ENABLE"])
    if code == 0:
        print(f"[enable] Задача '{TASK_NAME}' включена")


def cmd_disable(args):
    code, _, _ = _run_schtasks(["/Change", "/TN", TASK_NAME, "/DISABLE"])
    if code == 0:
        print(f"[disable] Задача '{TASK_NAME}' отключена")


def cmd_status(args):
    if not _task_exists():
        print(f"[status] Задача '{TASK_NAME}' не создана")
        return
    print(f"[status] Задача '{TASK_NAME}':")
    print()
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"],
        capture_output=True, text=False,
    )
    output = result.stdout.decode("cp866", errors="replace")
    for line in output.splitlines():
        line = line.strip()
        if line:
            print(f"  {line}")


def cmd_change_time(args):
    if not _task_exists():
        print(f"[change-time] Задача не существует")
        return
    print(f"[change-time] Меняю время на {args.time}")
    cmd_delete(args)
    create_args = argparse.Namespace(
        time=args.time, wake=True, days=args.days or "DAILY",
    )
    cmd_create(create_args)


def cmd_run_now(args):
    if not _task_exists():
        print(f"[run-now] Задача не существует")
        return
    code, _, _ = _run_schtasks(["/Run", "/TN", TASK_NAME])
    if code == 0:
        print(f"[run-now] Задача '{TASK_NAME}' запущена")


def main():
    parser = argparse.ArgumentParser(description="Управление задачей брифинга")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create")
    p_create.add_argument("--time", default="04:00")
    p_create.add_argument("--wake", action="store_true", default=True)
    p_create.add_argument("--no-wake", dest="wake", action="store_false")
    p_create.add_argument("--days", default="DAILY", choices=["DAILY", "WEEKDAYS"])
    p_create.set_defaults(func=cmd_create)

    sub.add_parser("delete").set_defaults(func=cmd_delete)
    sub.add_parser("enable").set_defaults(func=cmd_enable)
    sub.add_parser("disable").set_defaults(func=cmd_disable)
    sub.add_parser("status").set_defaults(func=cmd_status)

    p_change = sub.add_parser("change-time")
    p_change.add_argument("time")
    p_change.add_argument("--days", default="DAILY", choices=["DAILY", "WEEKDAYS"])
    p_change.set_defaults(func=cmd_change_time)

    sub.add_parser("run-now").set_defaults(func=cmd_run_now)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()