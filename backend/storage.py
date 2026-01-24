import os

def file_size_mb(path: str) -> float:
    return round(os.path.getsize(path) / (1024 * 1024), 2)
