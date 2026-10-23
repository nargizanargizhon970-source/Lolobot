import os
import re
import uuid
import asyncio
import subprocess
from yt_dlp import YoutubeDL
from config import COOKIES_FILE

# Вақтинчалик юклаб олинган видеолар сақланадиган папка
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# FFmpeg йўлини аниқлаш (видео ва аудиоларни бирлаштириш учун)
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = None


def clean_url(url: str) -> str:
    """
    Havolani tozalash: ortiqcha tracking parametrlarini olib tashlash va
    Instagram share havolalarini to'g'ri ko'rinishga keltirish.
    """
    url = url.strip()

    # Instagram share havolalarini to'g'rilash
    if "instagram.com" in url:
        url = re.sub(r'instagram\.com/share/reel/', 'instagram.com/reel/', url)
        url = re.sub(r'instagram\.com/share/p/', 'instagram.com/p/', url)
        # Tracking parametrlarini (igsh, utm_source va hk) tozalash
        if "?" in url:
            url = url.split("?")[0]
        if not url.endswith("/"):
            url += "/"

    # YouTube share havolalaridan trackingni tozalash
    elif "youtube.com" in url or "youtu.be" in url:
        # youtu.be/ID?si=xxx -> youtu.be/ID
        if "youtu.be/" in url and "?" in url:
            base, qs = url.split("?", 1)
            url = base
        # youtube.com/shorts/ID?si=xxx -> youtube.com/shorts/ID
        elif "/shorts/" in url and "?" in url:
            base, qs = url.split("?", 1)
            url = base

    return url


def _get_video_meta(path: str) -> dict:
    """
    FFmpeg орқали видеонинг асл ўлчамлари (width, height) ва давомийлигини (duration) аниқлаш.
    Бу Telegram'га видеони айнан Instagram ва YouTube Shorts каби тўғри форматда кўрсатишга ёрдам беради.
    """
    if not FFMPEG_PATH or not os.path.exists(path):
        return {}

    try:
        cmd = [FFMPEG_PATH, '-i', path]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors='ignore')
        out = res.stderr

        width, height, duration = None, None, None
        m = re.search(r'Stream.*Video:.*,\s*(\d{2,5})x(\d{2,5})', out)
        if m:
            width, height = int(m.group(1)), int(m.group(2))

        m_dur = re.search(r'Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)', out)
        if m_dur:
            duration = int(m_dur.group(1)) * 3600 + int(m_dur.group(2)) * 60 + int(float(m_dur.group(3)))

        return {
            'width': width,
            'height': height,
            'duration': duration
        }
    except Exception:
        return {}


def _ensure_faststart_mp4(input_path: str) -> str:
    """
    Видео метамаълумотларини (moov atom) бошланғич қисмга кўчириш (faststart).
    Бу видеони Telegram'да бир зумда стрим бўлиб очилишини таъминлайди.
    """
    if not FFMPEG_PATH or not os.path.exists(input_path):
        return input_path

    temp_out = input_path + ".fast.mp4"
    cmd = [
        FFMPEG_PATH, '-y', '-i', input_path,
        '-c', 'copy',
        '-movflags', '+faststart',
        temp_out
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        if os.path.exists(temp_out) and os.path.getsize(temp_out) > 0:
            os.replace(temp_out, input_path)
    except Exception:
        if os.path.exists(temp_out):
            try:
                os.remove(temp_out)
            except Exception:
                pass
    return input_path


def _download_sync(url: str) -> dict:
    """
    Instagram ва YouTube'дан видеони асл сифат ва форматда юклаб олиш.
    """
    url = clean_url(url)
    unique_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}_%(id)s.%(ext)s")

    ydl_opts = {
        # Telegram 50 MB лимитига мос сифатни танлаш (720p/480p оралиғида)
        'format': (
            'bv*[filesize<45M][ext=mp4]+ba*[filesize<8M][ext=m4a]/'
            'b[filesize<48M][ext=mp4]/'
            'bv*[height<=720][ext=mp4]+ba*[ext=m4a]/'
            'b[height<=720][ext=mp4]/'
            'bv*[height<=720]+ba/'
            'b[height<=720]/'
            'best[ext=mp4]/'
            'best'
        ),
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 30,
        'retries': 3,
        'max_filesize': 50 * 1024 * 1024,  # Telegram бот лимити: 50MB
        'extractor_args': {
            'youtube': {'player_client': ['android', 'web']}
        }
    }

    # Cookies файл мавжудлигини текшириш (Instagram ва YouTube чекловларини ечиш учун)
    cookie_candidate = None
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        cookie_candidate = COOKIES_FILE
    elif os.path.exists("cookies.txt"):
        cookie_candidate = "cookies.txt"

    if cookie_candidate:
        ydl_opts['cookiefile'] = cookie_candidate

    if FFMPEG_PATH:
        ydl_opts['ffmpeg_location'] = FFMPEG_PATH

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        # Агар playlist ёки бир нечта видео бўлса, биринчисини оламиз
        if 'entries' in info and info['entries']:
            info = list(info['entries'])[0]

        filename = ydl.prepare_filename(info)

        base_name, _ = os.path.splitext(filename)
        if not os.path.exists(filename):
            for ext in ['.mp4', '.mkv', '.webm', '.mov']:
                candidate = base_name + ext
                if os.path.exists(candidate):
                    filename = candidate
                    break
        elif os.path.exists(base_name + '.mp4'):
            filename = base_name + '.mp4'

        # Агар файл топилмаса, DOWNLOAD_DIR дан unique_id бўйича қидирамиз
        if not os.path.exists(filename):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(unique_id) and not f.endswith('.fast.mp4'):
                    candidate = os.path.join(DOWNLOAD_DIR, f)
                    if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
                        filename = candidate
                        break

        # Faststart тайёрлаш
        filename = _ensure_faststart_mp4(filename)

        # Видео ўлчамлари (width, height, duration)
        meta = _get_video_meta(filename)
        width = meta.get('width') or info.get('width')
        height = meta.get('height') or info.get('height')
        duration = meta.get('duration') or info.get('duration')

        title = info.get('title') or info.get('description') or "Видео"
        if title and len(title) > 200:
            title = title[:197] + "..."

        return {
            'file_path': filename,
            'title': title,
            'width': width,
            'height': height,
            'duration': duration
        }


async def download_video(url: str) -> dict:
    """
    Асинхрон кўринишда видео юклаб олиш.
    """
    return await asyncio.to_thread(_download_sync, url)


# Эски функция номи билан мувофиқлик учун
download_instagram_video = download_video

