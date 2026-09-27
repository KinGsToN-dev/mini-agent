"""Инструмент новостей — экономический календарь через Biquote."""
from datetime import datetime, timezone

# Уровни важности
IMPORTANCE_LEVELS = {"none": 0, "low": 1, "medium": 2, "high": 3}


def econ_calendar(countries: str = "US,EU,GB,JP",
                   importance: str = "medium",
                   limit: int = 15,
                   only_upcoming: bool = False) -> str:
    """
    Экономический календарь.

    Args:
        countries: список кодов через запятую (US,EU,GB,CN,JP,...)
        importance: минимальный уровень (none/low/medium/high)
        limit: сколько событий показать
        only_upcoming: только будущие события
    """
    try:
        from biquote import Biquote
    except ImportError:
        return "[ERROR] biquote не установлен. pip install biquote"

    try:
        bq = Biquote()
        events = bq.calendar(limit=200)  # Берём с запасом
        if not events:
            return "Нет событий"

        # Фильтр по странам
        country_list = [c.strip().upper() for c in countries.split(",") if c.strip()]
        if country_list and countries != "all":
            events = [e for e in events if e.get("countryCode", "").upper() in country_list]

        # Фильтр по важности
        min_level = IMPORTANCE_LEVELS.get(importance.lower(), 2)
        events = [
            e for e in events
            if IMPORTANCE_LEVELS.get(e.get("importance", "none"), 0) >= min_level
        ]

        # Только будущие
        if only_upcoming:
            now = datetime.now(timezone.utc)
            future = []
            for e in events:
                try:
                    t = datetime.fromisoformat(e["time"].replace("Z", "+00:00"))
                    if t >= now:
                        future.append(e)
                except Exception:
                    future.append(e)
            events = future

        if not events:
            return f"Нет событий (countries={countries}, importance>={importance})"

        # Сортируем по времени
        events.sort(key=lambda e: e.get("time", ""))

        lines = [f"Экономический календарь (топ {min(len(events), limit)} из {len(events)}):",
                 ""]

        for e in events[:limit]:
            # Время
            try:
                dt = datetime.fromisoformat(e["time"].replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                time_str = e.get("time", "?")[:16]

            cur = e.get("currency", "?")
            imp = e.get("importance", "?")
            name = e.get("name", "?")[:60]

            # Значок важности
            icons = {"high": "🔴", "medium": "🟡", "low": "🟢", "none": "⚪"}
            icon = icons.get(imp, "?")

            lines.append(f"{icon} {time_str}  {cur:<4}  {name}")

            # Значения (actual/forecast/previous)
            actual = e.get("actual")
            forecast = e.get("forecast")
            previous = e.get("previous")

            if actual is not None or forecast is not None or previous is not None:
                vals = []
                if actual is not None:
                    vals.append(f"факт: {actual}")
                if forecast is not None:
                    vals.append(f"прогноз: {forecast}")
                if previous is not None:
                    vals.append(f"пред: {previous}")
                lines.append(f"     {' | '.join(vals)}")

        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"