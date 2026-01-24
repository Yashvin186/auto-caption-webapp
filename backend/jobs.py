jobs = {}

def create_job(job_id):
    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Queued",
        "srt_path": None,
        "video_path": None,
        "error": None
    }


def update_progress(job_id, value, message=None):
    if job_id not in jobs:
        return

    jobs[job_id]["progress"] = max(
        jobs[job_id]["progress"], int(value)
    )

    if message:
        jobs[job_id]["message"] = message


def complete_job(job_id, srt_path, video_path,lang):
    if job_id not in jobs:
        return

    jobs[job_id].update({
        "status": "completed",
        "language":lang,
        "progress": 100,
        "message": "Completed",
        "srt_path": srt_path,
        "video_path": video_path
    })


def fail_job(job_id, error):
    if job_id not in jobs:
        return

    jobs[job_id].update({
        "status": "failed",
        "progress": jobs[job_id].get("progress", 0),
        "message": "Failed",
        "error": str(error)
    })
