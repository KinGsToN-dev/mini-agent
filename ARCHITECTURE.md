# РђСЂС…РёС‚РµРєС‚СѓСЂР° Mini-Agent

## РћР±С‰Р°СЏ СЃС…РµРјР°

РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ -> repl/loop -> repl/commands -> agent/core.GeminiAgent
                                                    |
                                                    +-> agent/provider_router
                                                    +-> agent/router
                                                    +-> providers/registry
                                                    |     +-> Gemini
                                                    |     +-> Groq
                                                    |     +-> Mistral
                                                    +-> tools/registry.execute_tool
                                                          +-> 13 РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ

## РџРѕС‚РѕРє Р·Р°РїСЂРѕСЃР° (СЂРѕСѓС‚РµСЂ)

1. РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РїРёС€РµС‚: РЅР°РїРёС€Рё С„СѓРЅРєС†РёСЋ quicksort
2. repl/loop РІС‹Р·С‹РІР°РµС‚ agent.ask(text)
3. provider_router.pick_provider() РІРёРґРёС‚ СЃР»РѕРІРѕ РЅР°РїРёС€Рё -> Mistral
4. agent.switch_provider("mistral")
5. РџСЂРѕРІР°Р№РґРµСЂ РЅРµ Gemini -> _ask_openai_compat()
6. history.load_messages() СЃРѕР±РёСЂР°РµС‚ РёСЃС‚РѕСЂРёСЋ РёР· JSONL (РїРѕСЃР»РµРґРЅРёРµ 20)
7. provider.ask() РѕС‚РїСЂР°РІР»СЏРµС‚ РІ Mistral API
8. РћС‚РІРµС‚ -> sys.stdout.write() -> РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ
9. history.append_message() СЃРѕС…СЂР°РЅСЏРµС‚ РІ JSONL

## РџРѕС‚РѕРє Р·Р°РїСЂРѕСЃР° (Gemini + tools)

1. РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РїРёС€РµС‚: С‡С‚Рѕ РІ РїР°РїРєРµ?
2. provider_router -> Gemini
3. agent.ask() -> _run_stream() -> SSE
4. РџРѕР»СѓС‡РёР»Рё function_call -> execute_tool("list_dir", {})
5. РћС‚РїСЂР°РІР»СЏРµРј function_result РѕР±СЂР°С‚РЅРѕ
6. Р¤РёРЅР°Р»СЊРЅС‹Р№ С‚РµРєСЃС‚

## РљР»СЋС‡РµРІС‹Рµ РјРѕРґСѓР»Рё

### agent/core.py вЂ” GeminiAgent

РЈРїСЂР°РІР»СЏРµС‚:
- С‚РµРєСѓС‰РёРј РїСЂРѕРІР°Р№РґРµСЂРѕРј Рё РјРѕРґРµР»СЊСЋ
- РёСЃС‚РѕСЂРёРµР№
- tool-calling С†РёРєР»РѕРј
- fallback РїСЂРё 429/404
- СЂРѕСѓС‚РµСЂРѕРј

РњРµС‚РѕРґС‹:
- ask(text) вЂ” РІС…РѕРґ, РІС‹Р·С‹РІР°РµС‚ СЂРѕСѓС‚РµСЂ
- _ask_openai_compat(text) вЂ” Groq/Mistral
- switch_provider(name) вЂ” СЃРјРµРЅР° РїСЂРѕРІР°Р№РґРµСЂР° Рё СЃР±СЂРѕСЃ РјРѕРґРµР»Рё
- switch_model(key) вЂ” СЃРјРµРЅР° РјРѕРґРµР»Рё РІРЅСѓС‚СЂРё РїСЂРѕРІР°Р№РґРµСЂР°

### agent/provider_router.py

РљР»Р°СЃСЃРёС„РёРєР°С‚РѕСЂ Р·Р°РґР°С‡:
- WEB_SEARCH_PATTERNS -> Gemini (Tavily)
- VISION_PATTERNS -> Gemini
- CODE_PATTERNS -> Mistral
- ANALYSIS_PATTERNS -> Gemini
- РѕСЃС‚Р°Р»СЊРЅРѕРµ -> Groq

### providers/openai_compat.py

РћР±С‰Р°СЏ РѕР±С‘СЂС‚РєР° Groq/Mistral:
- supports_tools=False РґР»СЏ Mistral
- max_tokens=4000
- РџРµС‡Р°С‚Р°РµС‚ tool-calls

### tools/registry.py

Р¦РµРЅС‚СЂР°Р»СЊРЅС‹Р№ СЂРµРµСЃС‚СЂ:
- TOOL_SCHEMAS вЂ” СЃС…РµРјС‹ РґР»СЏ LLM
- TOOL_FUNCTIONS вЂ” СЂРµР°Р»СЊРЅС‹Рµ С„СѓРЅРєС†РёРё
- execute_tool(name, args)
- set_vision_client(client)

### agent/history.py

JSONL-С…СЂР°РЅРёР»РёС‰Рµ sessions/РёРјСЏ.jsonl:
- РѕРґРЅР° СЃС‚СЂРѕРєР° = РѕРґРЅРѕ СЃРѕРѕР±С‰РµРЅРёРµ
- append_message, load_messages, find_in_messages

## РљР°Рє РґРѕР±Р°РІРёС‚СЊ РЅРѕРІС‹Р№ РёРЅСЃС‚СЂСѓРјРµРЅС‚

РЁР°Рі 1 вЂ” СЃРѕР·РґР°С‚СЊ tools/my_tool.py:

def my_tool(param):
    return "result: " + str(param)

РЁР°Рі 2 вЂ” РІ tools/registry.py:

from .my_tool import my_tool
TOOL_SCHEMAS.append({...})
TOOL_FUNCTIONS["my_tool"] = my_tool

РЁР°Рі 3 вЂ” РіРѕС‚РѕРІРѕ, РјРѕРґРµР»СЊ СѓРІРёРґРёС‚.

## РР·РІРµСЃС‚РЅС‹Рµ РѕРіСЂР°РЅРёС‡РµРЅРёСЏ

- Mistral РЅРµ РїРѕРґРґРµСЂР¶РёРІР°РµС‚ tool-calling
- Groq gpt-oss-120b РїСѓС‚Р°РµС‚ tools СЃ РІСЃС‚СЂРѕРµРЅРЅС‹Рј python
- Groq qwen-27b вЂ” Р»РёРјРёС‚ 7000 ITPM
- Gemini flash-3.5 вЂ” 20/РґРµРЅСЊ
- Tavily вЂ” 1000/РјРµСЃ