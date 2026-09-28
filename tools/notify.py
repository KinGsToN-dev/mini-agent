"""Инструмент notify — Windows-уведомления."""

import time

# Анти-спам: не чаще 1 уведомления в 2 секунды
_last_notify_time = 0.0
MIN_INTERVAL = 2.0


def notify(title: str = "Мини-агент", message: str = "",
           duration: int = 5) -> str:
    """Показывает Windows-уведомление."""
    global _last_notify_time

    # Анти-спам
    now = time.time()
    if now - _last_notify_time < MIN_INTERVAL:
        return f"[SKIP] Слишком часто (минимум {MIN_INTERVAL}с между уведомлениями)"
    _last_notify_time = now

    if not message:
        return "[ERROR] Пустое сообщение"

    # Обрезаем
    title = title[:64]
    message = message[:200]

    # Пробуем plyer
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="Мини-агент",
            timeout=duration,
        )
        return f"[OK] Уведомление отправлено: {title!r} / {message!r}"
    except ImportError as e:
        from agent.log import log
        log(f"notify: plyer not installed: {e}", level="DEBUG")
    except Exception as e:
        from agent.log import log
        log(f"notify: plyer failed: {type(e).__name__}: {e}", level="DEBUG")

    # Fallback: PowerShell toast (только Windows 10+)
    try:
        import subprocess
        ps_script = (
            f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; '
            f'[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; '
            f'$template = @"'
            f'<toast><visual><binding template="ToastText02">'
            f'<text id="1">{title}</text>'
            f'<text id="2">{message}</text>'
            f'</binding></visual></toast>'
            f'"@; '
            f'$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; '
            f'$xml.LoadXml($template); '
            f'$toast = New-Object Windows.UI.Notifications.ToastNotification $xml; '
            f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Мини-агент").Show($toast)'
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return f"[OK] Уведомление отправлено (fallback): {title!r}"
        return f"[ERROR] PowerShell-fallback вернул код {result.returncode}"
    except Exception as e:
        return f"[ERROR] Не удалось отправить уведомление: {type(e).__name__}: {e}"
