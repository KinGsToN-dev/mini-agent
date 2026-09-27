"""Инструмент web_search — поиск через Tavily API (с fallback на DuckDuckGo)."""

import os
import re
from urllib.parse import quote_plus
import httpx

MAX_RESULTS = 8
CONTEXT_LIMIT = 6000
TAVILY_URL = "https://api.tavily.com/search"


def _tavily_search(query: str, max_results: int) -> str | None:
    """Поиск через Tavily API. Возвращает строку или None при ошибке."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None

    try:
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",         # или "advanced" (медленнее, дороже)
            "include_answer": True,           # Tavily сам даёт краткий ответ
            "include_raw_content": False,
        }
        with httpx.Client(timeout=15) as client:
            r = client.post(TAVILY_URL, json=payload)
        if r.status_code != 200:
            return None

        data = r.json()

        # Формируем ответ
        lines = [f"🔍 Tavily: {query}"]
        lines.append("=" * 60)

        # Краткий AI-ответ от Tavily
        if data.get("answer"):
            lines.append("\n📌 Краткий ответ:")
            lines.append(data["answer"])
            lines.append("")

        # Список результатов
        results = data.get("results", [])
        if results:
            lines.append(f"\n📄 Источники ({len(results)}):")
            for i, item in enumerate(results, 1):
                title = item.get("title", "?")
                url = item.get("url", "?")
                content = item.get("content", "")
                score = item.get("score", 0)
                lines.append(f"\n{i}. {title}")
                lines.append(f"   URL: {url}")
                if score:
                    lines.append(f"   Релевантность: {score:.2f}")
                if content:
                    if len(content) > 400:
                        content = content[:400] + "..."
                    lines.append(f"   {content}")

        result = "\n".join(lines)
        if len(result) > CONTEXT_LIMIT:
            result = result[:CONTEXT_LIMIT] + "\n...[обрезано]"
        return result

    except Exception:
        return None


def _strip_html(text: str) -> str:
    """Убирает HTML-теги и разэкранирует сущности."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#x27;", "'").replace("&nbsp;", " ")
    return text.strip()


def _ddg_search(query: str, max_results: int) -> str:
    """Fallback — DuckDuckGo Lite."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        with httpx.Client(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        ) as client:
            response = client.get(url)
        if response.status_code != 200:
            return f"[ERROR] DuckDuckGo вернул {response.status_code}"

        html = response.text
        results = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.+?)</a>'
            r'.*?<a[^>]+class="result__snippet"[^>]*>(.+?)</a>',
            re.DOTALL | re.IGNORECASE,
        )
        for match in pattern.finditer(html):
            href, title, snippet = match.groups()
            title_clean = _strip_html(title)
            snippet_clean = _strip_html(snippet)
            if title_clean and len(title_clean) > 3:
                results.append({
                    "title": title_clean[:200],
                    "url": href[:300],
                    "snippet": snippet_clean[:400],
                })
            if len(results) >= max_results:
                break

        if not results:
            return f"[ERROR] DuckDuckGo не вернул результатов для '{query}'"

        lines = [f"🔍 DuckDuckGo: {query} ({len(results)})"]
        for i, r in enumerate(results, 1):
            lines.append(f"\n{i}. {r['title']}")
            lines.append(f"   URL: {r['url']}")
            if r["snippet"]:
                lines.append(f"   {r['snippet']}")
        return "\n".join(lines)
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"


def web_search(query: str, max_results: int = MAX_RESULTS) -> str:
    """
    Поиск в интернете.
    Приоритет: Tavily API → DuckDuckGo Lite (fallback).
    """
    if not query.strip():
        return "[ERROR] Пустой запрос"

    max_results = min(max_results, 15)

    # Tavily (основной)
    tavily_result = _tavily_search(query, max_results)
    if tavily_result:
        return tavily_result

    # Fallback
    return _ddg_search(query, max_results)
