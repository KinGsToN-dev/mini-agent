"""Long polling Telegram-бот."""

import logging
import time

import httpx

from telegram_bot import config
from telegram_bot.handler import handle_message, split_message


logger = logging.getLogger(__name__)


class TelegramBot:

    def __init__(self, token: str, allowed_chat_ids: set):
        self.token = token
        self.allowed = allowed_chat_ids
        self.api = f"{config.TELEGRAM_API_BASE}/bot{token}"
        self.offset = 0

    def _get_updates(self, timeout: int = config.POLL_TIMEOUT) -> list:
        try:
            with httpx.Client(timeout=timeout + 10) as client:
                r = client.get(
                    f"{self.api}/getUpdates",
                    params={"offset": self.offset, "timeout": timeout},
                )
            if r.status_code != 200:
                logger.error("getUpdates status=%s body=%s", r.status_code, r.text[:200])
                return []
            data = r.json()
            return data.get("result", []) or []
        except httpx.HTTPError as e:
            logger.error("getUpdates error: %s", e)
            return []

    def _send_message(self, chat_id: int, text: str):
        try:
            with httpx.Client(timeout=30) as client:
                client.post(
                    f"{self.api}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                )
        except httpx.HTTPError as e:
            logger.error("sendMessage error: %s", e)

    def _process_update(self, update: dict):
        msg = update.get("message") or {}
        if not msg:
            return

        sender = msg.get("from") or {}
        if sender.get("is_bot"):
            return

        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return

        if chat_id not in self.allowed:
            logger.warning("Ignored unauthorized chat_id=%s", chat_id)
            return

        text = msg.get("text") or ""
        if not text:
            return

        username = sender.get("username") or sender.get("first_name") or "?"

        try:
            answer = handle_message(chat_id, text, username)
        except Exception as e:
            logger.exception("handle_message failed")
            answer = f"Ошибка: {type(e).__name__}: {e}"

        parts = split_message(answer)
        for part in parts:
            self._send_message(chat_id, part)

    def run(self):
        logger.info("Bot started. Allowed chat_ids: %s", self.allowed)
        while True:
            try:
                updates = self._get_updates()
                for u in updates:
                    self.offset = max(self.offset, u.get("update_id", 0) + 1)
                    try:
                        self._process_update(u)
                    except Exception:
                        logger.exception("process_update failed")
            except KeyboardInterrupt:
                logger.info("Stopped by user")
                raise
            except Exception:
                logger.exception("Loop error, sleeping 5s")
                time.sleep(5)


def run_bot():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    token = config.get_token()
    allowed = config.get_allowed_chat_ids()
    bot = TelegramBot(token=token, allowed_chat_ids=allowed)
    bot.run()
