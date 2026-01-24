import subprocess
import os
from backend.jobs import update_progress
from backend.video_utils import get_video_duration


def extract_audio(video_path, audio_path):
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        raise Exception("Invalid video file")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        audio_path
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        print("FFMPEG STDERR:\n", result.stderr)
        raise Exception("Audio extraction failed")

    
def burn_subtitles(input_video, srt_path, output_video, job_id):
    srt_path = srt_path.replace("\\", "/")

    total_duration = get_video_duration(input_video)
    total_ms = total_duration * 1_000_000

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-vf", f"subtitles={srt_path}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",          # ✅ FIX
        "-b:a", "128k",         # ✅ FIX
        "-progress", "pipe:1",
        "-nostats",
        output_video
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        if line.startswith("out_time="):
             value = line.split("=")[1].strip()
             if value != "N/A":
                h, m, s = value.split(":")
                seconds = int(h)*3600 + int(m)*60 + float(s)
    process.wait()
    update_progress(job_id, 98)
