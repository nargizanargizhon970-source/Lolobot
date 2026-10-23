import logging
import aiohttp
from g4f.client import AsyncClient
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Siz Telegram bot ichidagi do'stona, bilimdon va foydali sun'iy intellekt (AI) yordamchisisiz. "
    "Foydalanuvchining savoliga qisqa, aniq, tushunarli va chiroyli formatda javob bering. "
    "Foydalanuvchi qaysi tilda yozsa, shu tilda javob bering (asosan o'zbek tilida)."
)


async def _ask_gemini(prompt: str) -> str:
    """
    Google Gemini rasmiy API orqali javob olish.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY mavjud emas")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\nFoydalanuvchi savoli: {prompt}"}
                ]
            }
        ]
    }

    timeout = aiohttp.ClientTimeout(total=6)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
            else:
                body = await resp.text()
                raise RuntimeError(f"Gemini API xatoligi {resp.status}: {body[:100]}")


async def _ask_g4f(prompt: str) -> str:
    """
    Zaxira AI (GPT-4o-mini) orqali javob olish.
    """
    client = AsyncClient()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message.content
    if answer:
        return answer.strip()
    raise RuntimeError("Bo'sh javob qaytdi")


async def ask_ai(prompt: str) -> str:
    """
    Foydalanuvchi savoliga AI orqali javob berish (Gemini -> Zaxira GPT).
    """
    # 1. Avval rasmiy Google Gemini API'ni tekshiramiz
    if GEMINI_API_KEY:
        try:
            return await _ask_gemini(prompt)
        except Exception as e:
            logger.warning(f"Gemini API javob bermadi ({type(e).__name__}), zaxira modelga o'tilmoqda...")

    # 2. Zaxira AI modeli (GPT-4o-mini)
    try:
        return await _ask_g4f(prompt)
    except Exception as e:
        logger.error(f"Zaxira AI xatoligi: {e}", exc_info=True)
        return "Hozirda AI xizmatiga ulanishda vaqtinchalik muammo bo'ldi. Iltimos, birozdan so'ng qayta urinib ko'ring."
