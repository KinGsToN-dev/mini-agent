"""Класс GeminiAgent — обёртка над SDK с fallback и tool-calling."""

import time
from google import genai
from rich.console import Console
from rich.panel import Panel

from config import MODELS, MODEL_CATALOG, DEFAULT_MODEL, SYSTEM_PROMPT, MAX_TOOL_ITERATIONS
from providers.fallback import try_with_fallback
from tools.registry import TOOL_SCHEMAS, execute_tool, set_tool_context, clear_tool_context
from agent.streaming import stream_interaction
from agent.state import load_exhausted, save_exhausted, clear_state
from agent import history as history_mod
from agent.router import classify, pick_model_key
from agent import provider_router
from agent import classifier
from providers.capabilities import pick_provider_for_category
from agent import analytics
from agent.verifier import Verifier

console = Console()


class GeminiAgent:
    def __init__(self, api_key: str, model_key: str = DEFAULT_MODEL):
        self.client = genai.Client(api_key=api_key)
        # Регистрируем клиент для vision-функций (screenshot_analyze)
        try:
            from tools.registry import set_vision_client
            set_vision_client(self.client)
        except Exception as e:
            from agent.log import log
            log(f"core: set_vision_client failed: {type(e).__name__}: {e}", level="WARNING")
        if model_key not in MODELS:
            console.print(f"[yellow]⚠ Модель '{model_key}' не найдена, "
                          f"использую '{MODEL_CATALOG[0][0]}'[/yellow]")
            model_key = MODEL_CATALOG[0][0]
        self.model_key = model_key
        self.model_name = MODELS[model_key]
        self.provider_name = "gemini"
        self.router_enabled = True   # авто-выбор провайдера
        self.last_interaction_id = None
        self.last_user_message = ""
        self.current_session_name = None  # устанавливается при save/load
        # FIX_CHAIN: restart ask after chain reset
        self._chain_reset_retry = False

        # Загружаем кэш исчерпанных моделей
        self.auto_route = True  # авто-выбор модели под задачу
        self.exhausted = load_exhausted()
        if self.exhausted:
            console.print(f"[dim]📦 Загружен кэш: {len(self.exhausted)} "
                          f"недоступных моделей из прошлой сессии[/dim]")
            if self.model_key in self.exhausted:
                for key, _, _ in MODEL_CATALOG:
                    if key not in self.exhausted:
                        self.model_key = key
                        self.model_name = MODELS[key]
                        console.print(f"[dim]↻ Текущая модель была в кэше, "
                                      f"переключаюсь на {self.model_name}[/dim]")
                        break

    def switch_model(self, model_key: str) -> str:
        """Смена модели внутри текущего провайдера."""
        from config import PROVIDER_CATALOG

        if self.provider_name == "gemini":
            if model_key not in MODELS:
                raise ValueError(
                    f"Неизвестная модель Gemini: {model_key}. "
                    f"Доступно: {list(MODELS)}"
                )
            self.model_key = model_key
            self.model_name = MODELS[model_key]
        else:
            catalog = PROVIDER_CATALOG.get(self.provider_name, [])
            found = None
            for k, name, _ in catalog:
                if k == model_key:
                    found = (k, name)
                    break
            if not found:
                valid = [k for k, _, _ in catalog]
                raise ValueError(
                    f"Модель '{model_key}' не найдена в '{self.provider_name}'. "
                    f"Доступно: {valid}"
                )
            self.model_key, self.model_name = found

        self.last_interaction_id = None
        return self.model_name

    def switch_provider(self, provider_name: str) -> tuple:
        """Переключение провайдера. Возвращает (provider, default_model)."""
        from providers import registry as provider_registry
        from config import PROVIDER_CATALOG, PROVIDER_DEFAULT_MODEL

        available = provider_registry.available_providers()
        if provider_name not in available:
            raise ValueError(f"Провайдер '{provider_name}' недоступен. "
                             f"Доступно: {available}")

        # Сбрасываем модель на дефолт ТОЛЬКО если провайдер меняется.
        # Если пользователь уже в этом провайдере и меняет модель через /model —
        # оставляем его выбор.
        provider_changed = (provider_name != self.provider_name)

        if provider_changed:
            default_key = PROVIDER_DEFAULT_MODEL.get(provider_name)
            if provider_name == "gemini":
                self.model_key = default_key or "lite-3.5"
                self.model_name = MODELS.get(self.model_key, "gemini-3.5-flash-lite")
            else:
                catalog = PROVIDER_CATALOG.get(provider_name, [])
                found = False
                for k, name, _ in catalog:
                    if k == default_key:
                        self.model_key = k
                        self.model_name = name
                        found = True
                        break
                if not found and catalog:
                    self.model_key = catalog[0][0]
                    self.model_name = catalog[0][1]

        self.provider_name = provider_name
        self.last_interaction_id = None
        return self.provider_name, self.model_name

    def _ask_openai_compat(self, user_text: str, chat_id=None) -> str:
        """Отправка через Groq/Mistral (OpenAI-совместимый API)."""
        import time as _time
        from config import SYSTEM_PROMPT
        from providers import registry as provider_registry
        from agent import history as history_mod

        provider = provider_registry.get_provider(self.provider_name)
        if provider is None:
            return f"[ERROR] Провайдер {self.provider_name} не настроен"

        # Собираем историю сообщений из локального JSONL
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self.current_session_name:
            for msg in history_mod.load_messages(self.current_session_name):
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["text"]})
        else:
            messages.append({"role": "user", "content": user_text})

        # Схемы инструментов (только если провайдер поддерживает)
        from tools.registry import TOOL_SCHEMAS
        if getattr(provider, "supports_tools", False):
            openai_tools = [
                {"type": "function", "function": s}
                for s in TOOL_SCHEMAS
            ]
        else:
            openai_tools = None

        t0 = _time.time()
        console.print(f"[dim]⏱  запрос к {self.model_name} ({self.provider_name})...[/dim]")

        try:
            answer = provider.ask(
                model_name=self.model_name,
                messages=messages,
                tools=openai_tools,
            )
        except Exception as e:
            # Обрезаем огромные тексты ошибок (иначе rich ломается на Windows)
            err_text = str(e)
            if len(err_text) > 500:
                err_text = err_text[:500] + "...[обрезано]"
            console.print(f"[red]Ошибка {self.provider_name}: {err_text}[/red]")
            raise

        dt = _time.time() - t0
        console.print(f"[dim]⏱  ответ за {dt:.2f}с[/dim]")

        # Печатаем ответ БЕЗ rich-парсинга
        # (иначе [x for x in ...] интерпретируется как тег стиля)
        if answer:
            import sys
            sys.stdout.write(answer)
            sys.stdout.flush()

        # Записываем ответ в локальную историю
        if self.current_session_name and answer:
            history_mod.append_message(self.current_session_name, "agent", answer)

        return answer

    def clear_history(self):
        self.last_interaction_id = None

    def save_state(self):
        """Сохраняет кэш исчерпанных моделей в файл."""
        save_exhausted(self.exhausted)

    def set_auto_route(self, enabled: bool):
        self.auto_route = bool(enabled)

    def _maybe_switch_by_route(self, user_text: str):
        # FIX_EXHAUSTED: router respects exhausted
        """Если auto_route включён — выбирает модель под задачу."""
        if not self.auto_route:
            return
        from config import MODEL_CATALOG
        catalog_keys = [k for k, _, _ in MODEL_CATALOG]
        target_key = pick_model_key(user_text, catalog_keys, self.exhausted)
        # FIX_EXHAUSTED: exhausted-fallback
        if target_key in self.exhausted:
            from config import MODEL_CATALOG
            for k,_,_ in MODEL_CATALOG:
                if k not in self.exhausted:
                    target_key = k
                    break
            else:
                target_key = None
        if target_key and target_key != self.model_key:
            level = classify(user_text)
            self.model_key = target_key
            self.model_name = MODELS[target_key]
            self.last_interaction_id = None  # новая модель — новый контекст
            console.print(f"[dim]🧭 роутер: '{level}' → {self.model_name}[/dim]")

    def forget_exhausted(self):
        """Ручной сброс кэша исчерпанных моделей."""
        self.exhausted.clear()
        clear_state()
        console.print("[green]Кэш исчерпанных моделей сброшен[/green]")

    def ask(self, user_text: str, chat_id: int | None = None) -> str:
        # Установка контекста инструментов (для telegram_send)
        if chat_id is not None:
            set_tool_context(chat_id=chat_id, use_command_bot=True)
        else:
            clear_tool_context()
        
        self.last_user_message = user_text
        # FIX: track if telegram_send was called during this ask
        self._tg_sent_during_ask = False

        # Локальная запись user-сообщения
        try:
            if self.current_session_name:
                history_mod.append_message(self.current_session_name, "user", user_text)
        except Exception as e:
            from agent.log import log
            log(f"core: append user msg failed: {type(e).__name__}: {e}", level="WARNING")

        # === РОУТЕР ПРОВАЙДЕРОВ ===
        if self.router_enabled:
            try:
                from providers import registry as _prov_reg
                available = _prov_reg.available_providers()
                category, confidence, source = classifier.classify(user_text, available)
                # FIX: pick_provider_for_category учитывает supports_tools.
                # Mistral не умеет tools → для 'покажи .py файлы' переключимся
                # на Gemini, а для 'напиши функцию' останемся на Mistral.
                target = pick_provider_for_category(category, user_text, available)
                if target and target != self.provider_name:
                    console.print(
                        f"[dim]🧭 роутер: {category} → {target} "
                        f"(conf={confidence:.2f}, {source})[/dim]"
                    )
                    self.switch_provider(target)
            except Exception as _e:
                from agent.log import log
                log(f"core: router failed: {type(_e).__name__}: {_e}", level="WARNING")

        # Если провайдер НЕ gemini — идём через OpenAI-совместимый путь
        if self.provider_name != "gemini":
            return self._ask_openai_compat(user_text, chat_id=chat_id)

        # Дальше — только для gemini
        self._maybe_switch_by_route(user_text)

        base_kwargs = {
            "input": user_text,
            "tools": TOOL_SCHEMAS,
            "system_instruction": SYSTEM_PROMPT,
            "stream": True,
        }
        if self.last_interaction_id:
            base_kwargs["previous_interaction_id"] = self.last_interaction_id

        t0 = time.time()
        console.print(f"[dim]⏱  запрос к {self.model_name}...[/dim]")
        interaction_id, text, func_calls = self._run_stream(base_kwargs)
        console.print(f"\n[dim]⏱  ответ модели за {time.time()-t0:.2f}с "
                      f"({self.model_name})[/dim]")

        iteration = 0
        all_tool_results = []   # FIX: накапливаем результаты для Verifier
        while func_calls and iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            func_results = self._execute_calls(func_calls, chat_id=chat_id)
            all_tool_results.extend(func_results)

            t2 = time.time()
            console.print(f"[dim]⏱  продолжение с результатами...[/dim]")
            followup = {
                "model": self.model_name,
                "previous_interaction_id": interaction_id,
                "input": func_results,
                "stream": True,
            }
            # FIX_CHAIN: wrap _run_stream to catch invalid_request mid-chain
            try:
                interaction_id, text, func_calls = self._run_stream(followup)
            except Exception as _chain_exc:
                if 'invalid_request' in str(_chain_exc) and not getattr(self, '_chain_reset_retry', False):
                    from agent.log import log
                    log('core: invalid_request mid-loop, restarting ask', level='WARNING')
                    print('\u21bb chain broken \u2014 restarting ask from scratch')
                    self._chain_reset_retry = True
                    self.last_interaction_id = None
                    return self.ask(user_text, chat_id=chat_id)
                raise
            console.print(f"\n[dim]⏱  ответ модели за {time.time()-t2:.2f}с[/dim]")

        self.last_interaction_id = interaction_id

        # FIX: force-send финального текста, если Gemini не вызвал telegram_send
        if chat_id is not None and text:
            import re as _re
            _user_wants = any(_re.search(p, user_text.lower()) for p in [
                r'\bотправь\b', r'\bотправить\b', r'\bскинь\b', r'\bпришли\b',
                r'\bsend\b', r'\btelegram\b', r'\bтелеграм',
            ])
            _tg_sent = getattr(self, '_tg_sent_during_ask', False)
            if _user_wants and not _tg_sent:
                try:
                    from tools.telegram_tools import telegram_send
                    telegram_send(text, title='Анализ', chat_id=chat_id, use_command_bot=True)
                    from agent.log import log
                    log(f'core: force-sent final text to telegram (chat_id={chat_id})', level='INFO')
                except Exception as _e:
                    from agent.log import log
                    log(f'core: force-send failed: {type(_e).__name__}: {_e}', level='ERROR')


        # FIX: Verifier - ВРЕМЕННО ОТКЛЮЧЁН
        # Причина: force-send ломает tool-call цепочку Gemini (invalid_request).
        # Вернём после переделки Verifier.
        # try:
        #     verifier = Verifier(self)
        #     verify_result = verifier.check_and_fix(
        #         user_text=user_text,
        #         tool_results=all_tool_results,
        #         final_text=text,
        #         chat_id=chat_id,
        #     )
        #     text = verify_result.final_text
        #     if verify_result.issues:
        #         from agent.log import log
        #         log(f'verifier: issues={verify_result.issues}, fixed={verify_result.fixed}',
        #             level='INFO')
        # except Exception as _e:
        #     from agent.log import log
        #     log(f'verifier failed: {type(_e).__name__}: {_e}', level='ERROR')

        # Локальная запись ответа агента
        try:
            if self.current_session_name and text:
                history_mod.append_message(self.current_session_name, "agent", text)
        except Exception as e:
            from agent.log import log
            log(f"core: append agent msg failed: {type(e).__name__}: {e}", level="WARNING")
        clear_tool_context()
        return text or "(пустой ответ)"

    def _run_stream(self, kwargs):
        return try_with_fallback(self, kwargs, stream_interaction, console)

    def _execute_calls(self, func_calls, chat_id: int | None = None):
        results = []
        if chat_id is not None:
            set_tool_context(chat_id=chat_id, use_command_bot=True)
        for call in func_calls:
            name, args, call_id = call["name"], call["arguments"], call["id"]
            console.print(Panel.fit(
                f"[bold yellow]{name}[/bold yellow]\n[dim]{args}[/dim]",
                title="tool call", border_style="yellow",
            ))
            t = time.time()
            result = execute_tool(name, args)
            # FIX: mark that telegram_send was called
            if name in ("telegram_send", "send_telegram_message", "send_telegram", "tg_send"):
                self._tg_sent_during_ask = True
            analytics.get().record_tool_call()
            preview = result if len(result) < 500 else result[:500] + "..."
            console.print(Panel.fit(preview, title="tool result", border_style="dim"))
            console.print(f"[dim]⏱  инструмент {name} выполнен за {time.time()-t:.2f}с[/dim]")
            results.append({
                "type": "function_result",
                "name": name,
                "call_id": call_id,
                "result": [{"type": "text", "text": result}],
            })
        return results








