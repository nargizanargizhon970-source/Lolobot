import os
import re
import sys
import logging
import asyncio

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN
from downloader import download_video
from ai_helper import ask_ai

# Журнални (logging) созлаш
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ҳаволаларни аниқлаш
INSTAGRAM_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:reel|reels|p|tv|share)/([a-zA-Z0-9_\-\./\?=&]+)'
)
YOUTUBE_URL_PATTERN = re.compile(
    r'https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?[^\s]+|shorts/[a-zA-Z0-9_\-]+[^\s]*|embed/[a-zA-Z0-9_\-]+[^\s]*|live/[a-zA-Z0-9_\-]+[^\s]*)|youtu\.be/[a-zA-Z0-9_\-]+[^\s]*)'
)


# FSM ҳолатлари
class BotStates(StatesGroup):
    ai_chat = State()


# Клавиатуралар
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Video Yuklash"), KeyboardButton(text="🤖 AI Chat")],
        [KeyboardButton(text="ℹ️ Yordam")]
    ],
    resize_keyboard=True
)

ai_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ AI Chatdan chiqish")]
    ],
    resize_keyboard=True
)

dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext):
    """
    /start буйруғи
    """
    await state.clear()
    first_name = message.from_user.first_name if message.from_user else "do'stim"
    text = (
        f"Assalomu alaykum, {first_name}! 👋\n\n"
        "🎬 **Men universal video yuklovchi va AI yordamchi botman!**\n\n"
        "Quyidagi imkoniyatlardan foydalanishingiz mumkin:\n"
        "• 📥 **Video Yuklash** — Instagram (Reels, Post) va YouTube (Shorts, Video) havolalarini yuboring.\n"
        "• 🤖 **AI Chat** — Istalgan savolingizni bering va sun'iy intellektdan tezkor javob oling!\n\n"
        "Kerakli bo'limni tanlang yoki to'g'ridan-to'g'ri havola yuboring 👇"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_kb)


@dp.message(F.text == "ℹ️ Yordam")
async def handle_help(message: types.Message):
    """
    Yordam bo'limi
    """
    text = (
        "📖 **Botdan foydalanish bo'yicha qo'llanma:**\n\n"
        "1️⃣ **Video yuklash:**\n"
        "Instagram yoki YouTube'dagi videoning havolasini botga yuboring. Bot uni original sifatda yuklab beradi.\n\n"
        "2️⃣ **AI Chat bo'limi:**\n"
        "«🤖 AI Chat» tugmasini bosing va istalgan mavzudagi savolingizni yozing. Chiqish uchun «❌ AI Chatdan chiqish» tugmasini bosing.\n\n"
        "3️⃣ **Tezkor AI so'rovi:**\n"
        "`/ai <savolingiz>` buyrug'i orqali ham to'g'ridan-to'g'ri AI'dan javob olishingiz mumkin."
    )
    await message.answer(text, parse_mode="Markdown")


@dp.message(F.text == "🤖 AI Chat")
async def enter_ai_chat(message: types.Message, state: FSMContext):
    """
    AI Chat rejimiga o'tish
    """
    await state.set_state(BotStates.ai_chat)
    text = (
        "🤖 **AI Chat bo'limiga xush kelibsiz!**\n\n"
        "Menga istalgan savolingizni bering:\n"
        "• Dasturlash va texnologiya\n"
        "• Matnlarni tahrirlash va tarjima\n"
        "• Maslahat, g'oyalar va hisob-kitoblar\n"
        "• Istalgan mavzuda erkin suhbat!\n\n"
        "✍️ *Savolingizni yozing (Chiqish uchun pastdagi tugmani bosing):*"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=ai_kb)


@dp.message(F.text.in_(["❌ AI Chatdan chiqish", "📥 Video Yuklash"]))
async def exit_ai_chat(message: types.Message, state: FSMContext):
    """
    AI Chat rejimini tugatish va video yuklash rejimiga qaytish
    """
    await state.clear()
    await message.answer(
        "📥 **Video yuklash rejimiga qaytdingiz.**\n"
        "Instagram yoki YouTube video havolasini yuborishingiz mumkin!",
        parse_mode="Markdown",
        reply_markup=main_kb
    )


@dp.message(Command("ai"))
async def handle_quick_ai(message: types.Message, bot: Bot):
    """
    /ai <savol> tezkor buyrug'i
    """
    query = message.text.replace("/ai", "", 1).strip()
    if not query:
        await message.reply("Iltimos, savolingizni ham yozing.\nMisol: `/ai Dunyoning eng baland tog'i qaysi?`", parse_mode="Markdown")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    answer = await ask_ai(query)
    if len(answer) > 4000:
        for i in range(0, len(answer), 4000):
            await message.reply(answer[i:i+4000])
    else:
        await message.reply(answer)


async def process_video_download(message: types.Message, bot: Bot, url: str, source_name: str):
    """
    Instagram yoki YouTube videosini yuklab yuborish
    """
    status_msg = await message.reply(f"⏳ {source_name} videosi yuklab olinmoqda, iltimos kuting...")
    await bot.send_chat_action(chat_id=message.chat.id, action="upload_video")

    file_path = None
    try:
        data = await download_video(url)
        file_path = data.get("file_path")
        title = data.get("title", f"{source_name} videosi")

        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text("❌ Videoni yuklab olishda xatolik yuz berdi.")
            return

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50:
            await status_msg.edit_text(
                f"⚠️ Video hajmi juda katta ({file_size_mb:.1f} MB).\n"
                "Telegram bot faqat 50 MB gacha bo'lgan videolarni yubora oladi."
            )
            return

        video_file = FSInputFile(file_path)
        bot_user = await bot.get_me()
        caption = f"🎬 {title}\n\n📥 {source_name} • 🤖 @{bot_user.username}"

        width = data.get("width")
        height = data.get("height")
        duration = int(data.get("duration")) if data.get("duration") else None

        await message.reply_video(
            video=video_file,
            caption=caption,
            width=width,
            height=height,
            duration=duration,
            supports_streaming=True
        )

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Xatolik ({source_name}): {e}", exc_info=True)
        error_str = str(e).lower()

        if any(k in error_str for k in [
            "empty media response", "login", "logged-in", "checkpoint", 
            "rate-limit", "rate limit", "restricted", "requires authentication"
        ]):
            if source_name == "Instagram":
                await status_msg.edit_text(
                    "🔒 **Instagram videoni yuklab bo'lmadi!**\n\n"
                    "Sabablari:\n"
                    "• Video yopiq (private) akkauntga tegishli bo'lishi mumkin.\n"
                    "• Instagram serveri avtorizatsiya talab qilmoqda.\n\n"
                    "💡 *Tavsiya:* Ommaviy videolarni ham yuklash uchun botga `cookies.txt` faylini biriktirish tavsiya etiladi."
                )
            else:
                await status_msg.edit_text("🔒 Bu video yopiq (private) profilga tegishli, uni yuklab bo'lmaydi.")

        elif any(k in error_str for k in ["not found", "404", "unavailable", "removed", "deleted"]):
            await status_msg.edit_text("❌ Video topilmadi, o'chirib tashlangan yoki havola noto'g'ri.")

        elif "live" in error_str:
            await status_msg.edit_text("⚠️ Jonli efir (live stream) videolarini yuklab bo'lmaydi.")

        elif any(k in error_str for k in ["too large", "max_filesize", "max-filesize", "larger than", "filesize"]):
            await status_msg.edit_text(
                "⚠️ Video hajmi juda katta (50 MB dan ortiq).\n"
                "Telegram bot faqat 50 MB gacha bo'lgan videolarni yubora oladi."
            )

        elif any(k in error_str for k in ["bot", "sign in", "confirm you're not a bot"]):
            await status_msg.edit_text(
                "⚠️ Platforma bot tekshiruvini talab qildi. Iltimos, birozdan so'ng qayta urinib ko'ring."
            )

        elif any(k in error_str for k in ["timed out", "timeout", "connection", "temporary"]):
            await status_msg.edit_text("⏱ Ulanish vaqti tugadi yoki internet sekin. Qayta urinib ko'ring.")

        else:
            await status_msg.edit_text(
                "❌ **Videoni yuklab olishda xatolik yuz berdi.**\n\n"
                f"Tafsilot: `{str(e)[:120]}`\n\n"
                "Iltimos, havolani tekshirib qayta urinib ko'ring."
            )

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as clean_err:
                logger.error(f"Faylni o'chirishda xatolik: {clean_err}")


@dp.message(BotStates.ai_chat, F.text)
async def handle_ai_chat_message(message: types.Message, bot: Bot):
    """
    AI Chat rejimida foydalanuvchi savollariga javob berish
    """
    text = message.text.strip()

    # Agar foydalanuvchi adashib video havola tashlasa, baribir yuklab beramiz
    match_insta = INSTAGRAM_URL_PATTERN.search(text)
    match_yt = YOUTUBE_URL_PATTERN.search(text)
    if match_insta:
        await process_video_download(message, bot, match_insta.group(0), "Instagram")
        return
    elif match_yt:
        await process_video_download(message, bot, match_yt.group(0), "YouTube")
        return

    # AI javob berishi uchun typing holatini yoqamiz
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    ai_response = await ask_ai(text)

    # Telegram xabar limiti (4096 belgi) dan oshmasligi uchun
    if len(ai_response) > 4000:
        for i in range(0, len(ai_response), 4000):
            await message.reply(ai_response[i:i+4000])
    else:
        await message.reply(ai_response)


@dp.message(F.text)
async def handle_general_message(message: types.Message, bot: Bot):
    """
    Asosiy rejimda video havolalarini qabul qilish
    """
    text = message.text.strip()

    match_insta = INSTAGRAM_URL_PATTERN.search(text)
    match_yt = YOUTUBE_URL_PATTERN.search(text)

    if match_insta:
        await process_video_download(message, bot, match_insta.group(0), "Instagram")
    elif match_yt:
        await process_video_download(message, bot, match_yt.group(0), "YouTube")
    else:
        await message.reply(
            "⚠️ Iltimos, **Instagram** yoki **YouTube** video havolasini yuboring!\n\n"
            "💬 Agar sun'iy intellektga savol bermoqchi bo'lsangiz, pastdagi **«🤖 AI Chat»** tugmasini bosing.",
            parse_mode="Markdown",
            reply_markup=main_kb
        )


from aiohttp import web


async def start_health_server():
    """
    Render Web Service uchun portni ochiq tutuvchi server.
    Render bepul tarifida Web Service ochilganda port talab qiladi.
    """
    port_str = os.getenv("PORT")
    if not port_str:
        return

    try:
        port = int(port_str)
        app = web.Application()

        async def handle_ping(request):
            return web.Response(text="Bot is alive and running!")

        app.router.add_get("/", handle_ping)
        app.router.add_get("/health", handle_ping)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Render health check serveri ochildi (port: {port})")
    except Exception as e:
        logger.error(f"Render portini ochishda xatolik: {e}")


async def main():
    if not BOT_TOKEN:
        print("[XATOLIK] BOT_TOKEN topilmadi! .env fayliga tokenni yozing.")
        return

    # Render Web Service portini ochish
    await start_health_server()

    bot = Bot(token=BOT_TOKEN)
    print("🚀 Bot ishga tushdi (Instagram + YouTube + AI Chat)! To'xtatish uchun Ctrl+C bosing.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot to'xtatildi.")
