from faster_whisper import WhisperModel
from datetime import timedelta
from backend.jobs import update_progress, fail_job
import os

model = None


def load_model():
    global model
    if model is None:
        model = WhisperModel(
            "medium",
            device="cpu",
            compute_type="int8"
        )


def ts(seconds):
    td = timedelta(seconds=seconds)
    s = int(td.total_seconds())
    ms = int((seconds - s) * 1000)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def transcribe_to_srt(video_path, srt_path, job_id):
    # 🔒 Safety checks
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        raise Exception("Invalid or empty video file")

    load_model()
    update_progress(job_id, 15, "Transcribing audio")

    try:
        segments, info = model.transcribe(
            video_path,
            task="translate",   # 🔥 force English
            vad_filter=True
        )

        segments = list(segments)
        total = len(segments)

        if total == 0:
            raise Exception("No speech detected in video")

        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{ts(seg.start)} --> {ts(seg.end)}\n")
                f.write(seg.text.strip() + "\n\n")

                progress = 15 + int((i / total) * 60)
                update_progress(job_id, progress, "Generating subtitles")

        return info.language

    except Exception as e:
        fail_job(job_id, str(e))
        raise
