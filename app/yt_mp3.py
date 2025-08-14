import os
from yt_dlp import YoutubeDL


def download_mp3_from_youtube(
    url,
    max_duration=1200,
):
    downloaded_files = []

    def my_hook(d):
        if d['status'] == 'finished':
            downloaded_files.append(f"{d['filename']}.mp3")

    # Фильтр: пропускать видео длиннее max_duration
    def duration_filter(info, *, incomplete):
        duration = info.get('duration')
        # if info.get("playlist_count") > 20:
        #     return "плейлист слишком большой"
        if duration and duration > max_duration:
            return f"Video too long ({duration} sec)"
        return None  # None = оставить видео

    # Опции скачивания
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'nocheckcertificate': True,
        "ignoreerrors": True,
        'playlist_items': '1:20',
        'max_filesize': 40 * 1024 * 1024,  # 40 MB в байтах
        'progress_hooks': [my_hook],
        'match_filter': duration_filter,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s',
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return downloaded_files


def remove_file(path):
    for p in path:
        os.remove(p)
