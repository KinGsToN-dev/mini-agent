"""Verifier — проверка результата ask() и автоматическое исправление.

Проверки:
  1. Tool-calls с [ERROR] -> retry 1 раз через 5 секунд.
  2. telegram_send не вызван, но запрос просит отправить -> force-send.
  3. Пустой ответ -> retry ask 1 раз.
  4. Ответ "отправлено", но telegram_send не вызывался -> force-send.

Verifier НЕ делает LLM-проверок. Только детерминистичные.
"""

import re
import time
from dataclasses import dataclass, field

from agent.log import log


# Паттерны, определяющие, что пользователь просит отправить в Telegram
TELEGRAM_REQUEST_PATTERNS = [
    r"\bотправь\b",
    r"\bотправить\b",
    r"\bскинь\b",
    r"\bпришли\b",
    r"\bотправь\s+в\s+телеграм",
    r"\bотправь\s+в\s+tg\b",
    r"\bв\s+телеграм\b",
    r"\bв\s+тг\b",
    r"\bsend\s+to\s+telegram\b",
]

# Паттерны, определяющие, что модель утверждает, что отправила
SENT_CLAIM_PATTERNS = [
    r"\bотправлено\b",
    r"\bотправил\b",
    r"\bуспешно\s+отправлено\b",
    r"\bsent\b",
]


@dataclass
class VerifyResult:
    """Результат проверки."""
    final_text: str
    issues: list = field(default_factory=list)
    fixed: bool = False


class Verifier:
    """Проверяет результат ask() и исправляет проблемы."""

    MAX_RETRIES = 1
    RETRY_DELAY_SEC = 5.0

    def __init__(self, agent):
        """agent — экземпляр GeminiAgent (для доступа к _tg_sent_during_ask)."""
        self.agent = agent

    # ------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------

    def check_and_fix(
        self,
        user_text: str,
        tool_results: list,
        final_text: str,
        chat_id: int | None,
        retry_ask_fn=None,
    ) -> VerifyResult:
        """
        Проверяет результат. Возвращает VerifyResult.

        Args:
            user_text: исходный запрос пользователя.
            tool_results: список результатов tool-calls (list of dict).
            final_text: финальный текст ответа.
            chat_id: Telegram chat_id, если запрос из бота.
            retry_ask_fn: функция для повторного ask (callable(text) -> str).
        """
        result = VerifyResult(final_text=final_text)

        # 1. Проверка на [ERROR] в tool_results
        errors = self._collect_errors(tool_results)
        if errors:
            for err in errors:
                result.issues.append(f"tool_error: {err[:80]}")

            # Retry: если есть retry_ask_fn и это первая попытка
            if retry_ask_fn is not None and self.MAX_RETRIES > 0:
                log(f"verifier: found {len(errors)} tool errors, retrying ask...", level="WARNING")
                time.sleep(self.RETRY_DELAY_SEC)
                try:
                    new_text = retry_ask_fn(user_text)
                    if new_text and new_text != "(пустой ответ)":
                        result.final_text = new_text
                        result.fixed = True
                        result.issues.append("retried_after_tool_error")
                        log("verifier: retry succeeded", level="INFO")
                except Exception as e:
                    log(f"verifier: retry failed: {type(e).__name__}: {e}", level="ERROR")

        # 2. Проверка на пустой ответ
        if not result.final_text or result.final_text == "(пустой ответ)":
            result.issues.append("empty_response")
            if retry_ask_fn is not None:
                log("verifier: empty response, retrying ask...", level="WARNING")
                time.sleep(self.RETRY_DELAY_SEC)
                try:
                    new_text = retry_ask_fn(user_text)
                    if new_text and new_text != "(пустой ответ)":
                        result.final_text = new_text
                        result.fixed = True
                        result.issues.append("retried_after_empty")
                        log("verifier: retry succeeded", level="INFO")
                except Exception as e:
                    log(f"verifier: retry failed: {type(e).__name__}: {e}", level="ERROR")

        # 3. Проверка: telegram_send должен быть вызван, но не был
        if chat_id is not None and self._user_wants_telegram(user_text):
            if not self._was_called("telegram_send", tool_results):
                # Если ответ пустой или утверждает, что "отправлено" — force-send
                if not result.final_text or self._claims_sent(result.final_text):
                    result.issues.append("missing_telegram_send")
                    if self._force_telegram_send(result.final_text, chat_id):
                        result.fixed = True
                        result.issues.append("forced_telegram_send")
                        # Переписываем ответ, чтобы не было галлюцинации
                        result.final_text = "Отправлено в Telegram."

        return result

    # ------------------------------------------------------------
    # Внутренние проверки
    # ------------------------------------------------------------

    def _collect_errors(self, tool_results: list) -> list:
        """Собирает все [ERROR] из tool_results."""
        errors = []
        for r in tool_results or []:
            text = self._extract_text(r)
            if text and "[ERROR]" in text:
                errors.append(text.strip())
        return errors

    @staticmethod
    def _extract_text(item) -> str:
        """Извлекает текст из tool_result (dict или строка)."""
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            if "result" in item:
                res = item["result"]
                if isinstance(res, list) and res and isinstance(res[0], dict):
                    return res[0].get("text", "")
                if isinstance(res, str):
                    return res
            return item.get("text", "")
        return str(item) if item else ""

    def _user_wants_telegram(self, user_text: str) -> bool:
        t = (user_text or "").lower()
        for pat in TELEGRAM_REQUEST_PATTERNS:
            if re.search(pat, t):
                return True
        return False

    def _claims_sent(self, text: str) -> bool:
        t = (text or "").lower()
        for pat in SENT_CLAIM_PATTERNS:
            if re.search(pat, t):
                return True
        return False

    def _was_called(self, tool_name: str, tool_results: list) -> bool:
        """Проверяет, был ли вызван tool с заданным именем."""
        # Основной сигнал — флаг на агенте (устанавливается в _execute_calls)
        if getattr(self.agent, "_tg_sent_during_ask", False):
            if tool_name in ("telegram_send", "send_telegram_message",
                             "send_telegram", "tg_send"):
                return True

        # Резервная проверка — по tool_results
        for r in tool_results or []:
            if isinstance(r, dict):
                name = r.get("name", "")
                if name == tool_name:
                    text = self._extract_text(r)
                    if "[OK]" in text:
                        return True
        return False

    def _force_telegram_send(self, text: str, chat_id: int) -> bool:
        """Принудительно вызывает telegram_send."""
        try:
            from tools.telegram_tools import telegram_send
            msg = (text or "").strip() or "(пустой ответ)"
            res = telegram_send(msg, title="Mini-Agent", chat_id=chat_id, use_command_bot=True)
            log(f"verifier: forced telegram_send -> {res[:80]}", level="INFO")
            return True
        except Exception as e:
            log(f"verifier: force telegram_send failed: {type(e).__name__}: {e}", level="ERROR")
            return False
