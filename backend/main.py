"""
AI Digital Human - FastAPI Backend Entry Point (V1.2)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
from pathlib import Path

from app.database import init_db
from app.routers import assets, templates, tts, subtitle, render, projects, settings, pipeline

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="AI Digital Human API",
    description="V1.1 - Stability fix: simplified pipeline, timeout, debug logging",
    version="1.1.0"
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    tb = traceback.format_exc()
    print("[EXCEPTION]", type(exc).__name__, str(exc))
    print("[TRACE]", tb[:500])
    return {"error": type(exc).__name__, "detail": str(exc)}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets.router)
app.include_router(templates.router)
app.include_router(tts.router)
app.include_router(subtitle.router)
app.include_router(render.router)
app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(pipeline.router)


def check_ffmpeg() -> dict:
    """Check FFmpeg availability."""
    try:
        candidates = [
            r"C:\Users\Administrator\AppData\Local\Programs\FFmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
            "ffmpeg",
        ]
        for path in candidates:
            if path == "ffmpeg" or os.path.exists(path):
                r = subprocess.run([path, "-version"], capture_output=True, timeout=5)
                if r.returncode == 0:
                    return {"status": "ok", "path": path}
        return {"status": "not_found", "path": ""}
    except Exception as e:
        return {"status": "error", "path": "", "error": str(e)}


def check_edge_tts() -> dict:
    """Check EdgeTTS availability."""
    try:
        import edge_tts
        return {"status": "ok"}
    except ImportError:
        return {"status": "not_installed"}


def check_output_dir() -> dict:
    """Check if output directory is writable."""
    try:
        out_dir = BASE_DIR / "outputs"
        os.makedirs(out_dir, exist_ok=True)
        test_file = out_dir / ".write_test"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return {"status": "ok", "path": str(out_dir)}
    except Exception as e:
        return {"status": "not_writable", "error": str(e)}


@app.on_event("startup")
async def startup_event():
    init_db()
    import os
    # Ensure outputs dir exists (both in dev and packaged paths)
    out_dir = BASE_DIR / "outputs"
    os.makedirs(out_dir, exist_ok=True)
    db_dir = BASE_DIR
    os.makedirs(db_dir, exist_ok=True)
    is_packaged = os.path.exists(os.path.join(os.path.dirname(__file__), "..", "resources"))
    print("[API] AI Digital Human V1.1 started (packaged=" + ("yes" if is_packaged else "no") + ")")
    # Run startup health check
    checks = {
        "python": {"status": "ok"},
        "backend": {"status": "ok"},
        "ffmpeg": check_ffmpeg(),
        "edge_tts": check_edge_tts(),
        "output_dir": check_output_dir(),
    }
    for name, check in checks.items():
        if check.get("status") != "ok":
            print(f"[HEALTH] {name}: {check}")
    print(f"[HEALTH] All core services: {[k for k,v in checks.items() if v.get('status')=='ok']}")


@app.get("/")
async def root():
    return {"service": "AI Digital Human API", "version": "1.1.0"}


@app.get("/ping")
async def ping():
    return {"ok": True, "service": "fastapi-backend"}


@app.get("/health")
async def health_check():
    """
    Comprehensive health check.
    Returns status of: backend, ffmpeg, edge-tts, output_dir.
    """
    checks = {
        "backend": {"status": "ok"},
        "ffmpeg": check_ffmpeg(),
        "edge_tts": check_edge_tts(),
        "output_dir": check_output_dir(),
    }
    all_ok = all(v.get("status") == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": checks
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)