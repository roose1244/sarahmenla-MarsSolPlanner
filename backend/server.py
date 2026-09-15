"""FastAPI backend serving the Mars Sol-Window Planner demo assets.

Endpoints:
  GET  /api/health                     – liveness
  GET  /api/plan                       – returns demo/plan.json
  POST /api/regenerate                 – reruns the planner pipeline
  GET  /api/mars/{file}                – serves demo/{file} (plan_three.html, plan.png, etc)
"""
import os
import sys
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import json

APP_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = APP_DIR / "demo"
SRC_DIR = APP_DIR / "src"

app = FastAPI(title="Sol-Window Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "sol-window-planner"}


@app.get("/api/plan")
def plan():
    p = DEMO_DIR / "plan.json"
    if not p.exists():
        raise HTTPException(404, "plan.json not found — run /api/regenerate")
    return JSONResponse(json.loads(p.read_text()))


@app.post("/api/regenerate")
def regenerate(start: str = "10,10", horizon_sols: int = 20):
    """Re-run the sol_window.demo pipeline."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    try:
        out = subprocess.run(
            [sys.executable, "-m", "sol_window.demo",
             "--start", start, "--horizon-sols", str(horizon_sols),
             "--no-3d"],
            cwd=str(APP_DIR), env=env, capture_output=True, text=True, timeout=90,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Pipeline timed out")
    if out.returncode != 0:
        raise HTTPException(500, out.stderr[-500:] or "Pipeline failed")
    return {"ok": True, "log": out.stdout.splitlines()[-8:]}


@app.get("/api/mars/{name:path}")
def mars_file(name: str):
    """Serve any file from /app/demo/ (plan_three.html, plan.json, plan.png…)"""
    safe = (DEMO_DIR / name).resolve()
    if not str(safe).startswith(str(DEMO_DIR.resolve())):
        raise HTTPException(403, "Forbidden")
    if not safe.exists():
        raise HTTPException(404, f"{name} not found")
    return FileResponse(safe)
