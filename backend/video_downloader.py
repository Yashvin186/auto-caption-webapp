from backend.jobs import jobs
import yt_dlp
import os

def progress_hook(d, job_id):
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)

        if total:
            percent = int(downloaded / total * 100)
            jobs[job_id]["progress"] = percent
            jobs[job_id]["message"] = "Downloading video"


def download_video_from_url(url, output_path, job_id):
    ydl_opts = {
        "outtmpl": output_path,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "js_runtimes": {"node": {}},   # ✅ FIXED
        "hls_prefer_native": False,
        "progress_hooks": [lambda d: progress_hook(d, job_id)],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise Exception("Downloaded video is empty")
