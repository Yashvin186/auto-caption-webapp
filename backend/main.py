import uuid, os ,time
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi import Form
from backend.video_downloader import download_video_from_url
from backend.whisper_engine import transcribe_to_srt
from backend.ffmpeg_utils import burn_subtitles, extract_audio
from backend.jobs import jobs, create_job, update_progress, complete_job, fail_job
import traceback
from fastapi.staticfiles import StaticFiles


UPLOADS = "uploads"
OUTPUTS = "outputs"
current_stage = "Transcribing audio…"


os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

app = FastAPI()

app.mount("/outputs", StaticFiles(directory=OUTPUTS), name="outputs")

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

@app.get("/test")
def test():
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "Server is running"}
    
@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# 🔹 BACKGROUND PIPELINE
def process_video(job_id, video_path, background_tasks):
    try:
        update_progress(job_id, 5, "Loading Whisper model")

        srt_path = f"{OUTPUTS}/{job_id}.srt"
        out_video = f"{OUTPUTS}/{job_id}_cc.mp4"

        update_progress(job_id, 10, "Transcribing audio")
        audio_path = f"{UPLOADS}/{job_id}.wav"

        extract_audio(video_path, audio_path)
        lang = transcribe_to_srt(audio_path, srt_path, job_id)


        update_progress(job_id, 70, "Burning subtitles")
        burn_subtitles(video_path, srt_path, out_video, job_id)

        complete_job(job_id, srt_path, out_video, lang)

        background_tasks.add_task(
        cleanup_files,
        [video_path, audio_path, srt_path, out_video],
        2400
    )

    except Exception as e:
        print("❌ BACKGROUND ERROR:")
        traceback.print_exc()
        fail_job(job_id, str(e))
        return


# 🔹 UPLOAD
@app.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    video_url: str = Form(None)
):
    job_id = str(uuid.uuid4())
    create_job(job_id)

    video_path = f"{UPLOADS}/{job_id}.mp4"

    # 🔹 CASE 1: Local file upload
    if file:
        with open(video_path, "wb") as f:
            f.write(await file.read())
        update_progress(job_id, 5)

    # 🔹 CASE 2: Video URL
    elif video_url:
        download_video_from_url(video_url, video_path, job_id)

    else:
        return {"error": "No video provided"}

    background_tasks.add_task(
        process_video,
        job_id,
        video_path,
        background_tasks  # 👈 pass it
    )
    return {"job_id": job_id}


# 🔹 STATUS
@app.get("/status/{job_id}")
def job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return {"status": "invalid"}

    return {
        "status": job["status"],
        "message": job.get("message", ""),
        "progress": job["progress"],
        "video_url": f"/outputs/{job_id}_cc.mp4" if job["video_path"] else None,
        "srt_url": f"/outputs/{job_id}.srt" if job["srt_path"] else None,
    }





# 🔹 DOWNLOADS
@app.get("/download/srt/{job_id}")
def download_srt(job_id: str):
    job = jobs[job_id]
    return FileResponse(
        job["srt_path"],
        media_type="application/x-subrip",
        filename=f"{job_id}.srt"
    )


@app.get("/download/video/{job_id}")
def download_video(job_id: str):
    job = jobs[job_id]
    return FileResponse(
        job["video_path"],
        media_type="video/mp4",
        filename=f"{job_id}_cc.mp4"
    )

def cleanup_files(paths, delay=2400):  # 10 minutes
    time.sleep(delay)
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except:

            pass

