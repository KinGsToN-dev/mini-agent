"""
Проверяем vision через старый стабильный API (models.generate_content).
"""

import os
import base64
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SCREENSHOT = "screenshot.png"
if not os.path.exists(SCREENSHOT):
    from PIL import Image
    Image.new("RGB", (100, 100), color=(255, 0, 0)).save(SCREENSHOT, "PNG")
    print(f"Создан тестовый {SCREENSHOT}")

with open(SCREENSHOT, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("ascii")

print(f"Картинка: {SCREENSHOT}, base64 длина: {len(img_b64)}")
print()

# Пробуем через generate_content на разных моделях
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]

for model_name in MODELS:
    print("=" * 60)
    print(f"Модель: {model_name}")
    print("=" * 60)
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": "Опиши одним предложением что на картинке."},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": img_b64,
                            }
                        },
                    ],
                }
            ],
        )
        text = response.text if hasattr(response, "text") else str(response)
        print(f"✅ РАБОТАЕТ!")
        print(f"Ответ: {text[:300]}")
        print()
        print(f"👉 Используй этот метод: client.models.generate_content")
        print(f"   с моделью: {model_name}")
        break
    except Exception as e:
        err = str(e)[:200]
        print(f"❌ {type(e).__name__}: {err}")
        print()
        time.sleep(1)

print("=" * 60)
