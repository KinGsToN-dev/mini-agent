"""Простая аналитика запросов в текущей сессии."""

from collections import Counter, defaultdict
from datetime import datetime


class Analytics:
    def __init__(self):
        self.reset()

    def reset(self):
        self.started = datetime.now()
        self.requests = 0
        self.tool_calls = 0
        self.fallbacks = 0
        self.errors = 0
        self.models_used = Counter()
        self.total_time = 0.0
        self.slowest = 0.0
        self.fastest = None

    def record_request(self, model_name: str, duration: float):
        self.requests += 1
        self.models_used[model_name] += 1
        self.total_time += duration
        if duration > self.slowest:
            self.slowest = duration
        if self.fastest is None or duration < self.fastest:
            self.fastest = duration

    def record_tool_call(self):
        self.tool_calls += 1

    def record_fallback(self):
        self.fallbacks += 1

    def record_error(self):
        self.errors += 1

    def summary(self) -> dict:
        avg = (self.total_time / self.requests) if self.requests else 0.0
        uptime = (datetime.now() - self.started).total_seconds()
        return {
            "uptime_sec": uptime,
            "requests": self.requests,
            "tool_calls": self.tool_calls,
            "fallbacks": self.fallbacks,
            "errors": self.errors,
            "avg_time": avg,
            "fastest": self.fastest or 0.0,
            "slowest": self.slowest,
            "models": dict(self.models_used),
        }


# Глобальный экземпляр
_instance = Analytics()


def get() -> Analytics:
    return _instance
