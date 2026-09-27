"""
Пробуем разные форматы передачи картинки в Interactions API.
"""

import os
import base64
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SCREENSHOT = "screenshot.png"
if not os.path.exists(SCREENSHOT):
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(SCREENSHOT, "PNG")
        print(f"Создан тестовый {SCREENSHOT}")
    except ImportError:
        print("Нет Pillow и нет screenshot.png — сделай скриншот заранее")
        raise SystemExit(1)

with open(SCREENSHOT, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("ascii")

print(f"Картинка: {SCREENSHOT}, base64 длина: {len(img_b64)}")

VARIANTS = [
    ("A: image + mime_type сверху",
     {"type": "image", "mime_type": "image/png", "data": img_b64}),

    ("B: image.image + mime_type",
     {"type": "image", "image": {"mime_type": "image/png", "data": img_b64}}),

    ("C: image.inline_data",
     {"type": "image", "inline_data": {"mime_type": "image/png", "data": img_b64}}),

    ("D: image + data только",
     {"type": "image", "data": img_b64}),

    ("E: input_image с source",
     {"type": "input_image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}),

    ("F: image без type, как image_data",
     {"image": {"mime_type": "image/png", "data": img_b64}}),
]

for name, fmt in VARIANTS:
    print()
    print("=" * 60)
    print(f"Пробую: {name}")
    print("=" * 60)
    try:
        interaction = client.interactions.create(
            model="gemini-3.5-flash",
            input=[
                {"type": "text", "text": "Опиши одним предложением что на картинке."},
                fmt,
            ],
        )
        text = getattr(interaction, "output_text", "") or "(пусто)"
        print(f"✅ РАБОТАЕТ!")
        print(f"Ответ: {text[:200]}")
        print()
        print(f"👉 Используй этот формат: {name}")
        break
    except Exception as e:
        err = str(e)[:200]
        print(f"❌ {type(e).__name__}: {err}")

print()
print("=" * 60)
print("Готово. Скажи мне, какой формат сработал (если какой-то).")
