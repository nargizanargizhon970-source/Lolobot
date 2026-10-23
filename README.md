# 📥 Instagram & YouTube Video Downloader Telegram Bot

Ushbu loyiha Python dasturlash tili va **aiogram 3** hamda **yt-dlp** kutubxonalari yordamida yozilgan.
Foydalanuvchi **Instagram** (Reels, Post, IGTV) yoki **YouTube** (Shorts, oddiy videolar) havolasini yuborganida, bot videoni avtomatik tarzda yuklab olib, Telegram orqali video formatida yuboradi.

---

## 📁 Loyiha tarkibi

- `bot.py` — Telegram botining asosiy logikasi va buyruqlar ishlovchisi.
- `downloader.py` — Instagram havolasidan videoni yuklab oluvchi modul (`yt-dlp`).
- `config.py` — Sozlamalar va `.env` faylidan ma'lumotlarni o'quvchi modul.
- `requirements.txt` — Kerakli Python kutubxonalari ro'yxati.
- `.env` — Bot tokeni saqlanadigan fayl.

---

## 🚀 O'rnatish va ishga tushirish bo'yicha qo'llanma

### 1-qadam: Python dasturini o'rnatish
Agar kompyuteringizda Python o'rnatilmagan bo'lsa:
1. [python.org](https://www.python.org/downloads/) rasmiy saytidan Python'ning oxirgi versiyasini yuklab oling.
2. O'rnatish paytida eng pastdagi **"Add python.exe to PATH"** katakchasiga albatta belgi (✅) qo'ying!
3. O'rnatishni yakunlang.

---

### 2-qadam: Kutubxonalarni o'rnatish
Terminal yoki buyruqlar satrini (cmd / PowerShell) ochib, ushbu loyiha papkasida quyidagi buyruqni bajaring:

```bash
pip install -r requirements.txt
```

---

### 3-qadam: Telegram Bot Tokenini olish
1. Telegram'ga kiring va [@BotFather](https://t.me/BotFather) botini oching.
2. `/newbot` buyrug'ini yuboring.
3. Botingizga nom va `@username` bering.
4. `@BotFather` sizga **HTTP API token** beradi (masalan: `1234567890:ABCdef...`).
5. Loyiha ichidagi `.env` faylini ochib, olingan tokenni quyidagicha yozing:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

### 4-qadam: FFmpeg o'rnatish (Tavsiya etiladi)
Videolarni (ayniqsa yuqori sifatli audio va videoni) sifatli birlashtirish uchun tizimda **FFmpeg** bo'lishi tavsiya qilinadi:
- Windows uchun: [ffmpeg.org](https://ffmpeg.org/download.html) yoki terminal orqali `winget install Gyan.FFmpeg` buyrug'i bilan o'rnatish mumkin.

---

### 5-qadam: Botni ishga tushirish
Quyidagi buyruqni bering:

```bash
python bot.py
```

Botingiz muvaffaqiyatli ishga tushadi! Telegram'ga o'tib, botingizga `/start` yuboring va istalgan Instagram video havolasini tashlab ko'ring.

---

## ⚡ Asosiy imkoniyatlari
- **Tezkor va asinxron:** Boshqa foydalanuvchilar kutib qolmasligi uchun yuklash ishlari alohida oqimda (`asyncio.to_thread`) ishlaydi.
- **Xotirani tejash:** Video foydalanuvchiga yuborilgach, server yoki kompyuter xotirasidan avtomatik o'chiriladi.
- **Xatoliklarni boshqarish:** Yopiq (private) profillar, o'chirilgan videolar yoki 50 MB dan katta hajmli fayllar haqida foydalanuvchiga tushunarli xabar beradi.
