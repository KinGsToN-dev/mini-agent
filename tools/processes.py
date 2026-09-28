"""Инструмент processes — список и kill процессов."""

import time
import psutil

# Процессы, которые убивать ЗАПРЕЩЕНО
PROTECTED_NAMES = {
    "system", "system idle process", "registry", "smss.exe",
    "csrss.exe", "wininit.exe", "winlogon.exe", "services.exe",
    "lsass.exe", "svchost.exe", "dwm.exe", "explorer.exe",
    "audiodg.exe", "fontdrvhost.exe", "ctfmon.exe",
    "searchindexer.exe", "spoolsv.exe", "taskhostw.exe",
    "lsaiso.exe", "memory compression", "msmpeng.exe",
}


def _fmt_mb(bytes_val: int) -> str:
    return f"{bytes_val / (1024 * 1024):.1f}"


def processes(action: str = "list", filter: str = None,
              sort_by: str = "cpu", top: int = 15,
              pid: int = None, name: str = None) -> str:
    """list — список процессов; kill — убить процесс."""
    try:
        if action == "list":
            # Прогрев cpu_percent — первый замер всегда 0.0
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    p.cpu_percent(None)
                except Exception as e:
                    from agent.log import log
                    log(f"processes: warmup failed: {type(e).__name__}: {e}", level="TRACE")
            time.sleep(0.3)

            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                try:
                    info = p.info
                    pname = (info["name"] or "?").lower()
                    # Фильтруем системные по умолчанию (если нет явного filter)
                    if not filter and pname in PROTECTED_NAMES:
                        continue
                    if filter and filter.lower() not in pname:
                        continue
                    cpu = info.get("cpu_percent") or 0.0
                    mem = (info.get("memory_info").rss
                           if info.get("memory_info") else 0)
                    procs.append((info["pid"], info["name"] or "?", cpu, mem))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if sort_by == "memory":
                procs.sort(key=lambda x: x[3], reverse=True)
            elif sort_by == "name":
                procs.sort(key=lambda x: x[1].lower())
            else:
                procs.sort(key=lambda x: x[2], reverse=True)

            procs = procs[:top]
            lines = ["PID     NAME                     CPU%   RAM(MB)"]
            lines.append("-" * 55)
            for p, n, c, m in procs:
                lines.append(f"{p:<7} {n[:24]:<24} {c:>5.1f}  {_fmt_mb(m):>8}")
            return "\n".join(lines)

        elif action == "kill":
            if pid is None and not name:
                return "[ERROR] Для kill нужен параметр pid или name"
            if pid is not None and name:
                return "[ERROR] Укажи только pid ИЛИ name, не оба"

            killed = []
            errors = []
            targets = []

            if pid is not None:
                try:
                    p = psutil.Process(pid)
                    targets.append(p)
                except psutil.NoSuchProcess:
                    return f"[ERROR] Процесс с pid {pid} не найден"
            else:
                name_lower = name.lower()
                for p in psutil.process_iter(["pid", "name"]):
                    try:
                        pname = (p.info["name"] or "").lower()
                        if name_lower in pname:
                            if pname in PROTECTED_NAMES:
                                errors.append(f"{pname} (PID {p.info['pid']}) — защищён")
                                continue
                            targets.append(p)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            if not targets:
                return "Ничего не найдено для kill"

            for p in targets:
                try:
                    pname = p.name()
                    ppid = p.pid
                    p.terminate()
                    killed.append(f"{pname} (PID {ppid})")
                except psutil.AccessDenied:
                    errors.append(f"PID {p.pid} — нет прав")
                except Exception as e:
                    errors.append(f"PID {p.pid} — {e}")

            msg = f"Убито: {len(killed)} процессов"
            if killed:
                msg += "\n  " + "\n  ".join(killed[:20])
                if len(killed) > 20:
                    msg += f"\n  ...[ещё {len(killed) - 20}]"
            if errors:
                msg += "\n\nОшибки:\n  " + "\n  ".join(errors)
            return msg

        else:
            return f"[ERROR] action должен быть 'list' или 'kill', а не '{action}'"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"

