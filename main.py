import os, shutil, psutil, datetime, json, zipfile, requests
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ADMIN_PASS = "12345"
SESSION_ID = "zenith_777"
MODULES_DIR = "modules"

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)

# --- ЛОГИКА МОДУЛЕЙ ---
@app.get("/api/modules/list")
async def list_modules():
    mods = []
    for d in os.listdir(MODULES_DIR):
        conf_path = os.path.join(MODULES_DIR, d, "config.json")
        if os.path.exists(conf_path):
            with open(conf_path, "r", encoding="utf-8") as f:
                mods.append(json.load(f))
    return mods

@app.post("/api/modules/upload")
async def upload_zip(file: UploadFile = File(...)):
    path = os.path.join(MODULES_DIR, file.filename)
    with open(path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    with zipfile.ZipFile(path, 'r') as z:
        z.extractall(MODULES_DIR)
    os.remove(path)
    return {"status": "ok"}

# --- СИСТЕМНЫЕ ФУНКЦИИ ---
@app.get("/api/stats")
async def get_stats():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "net": f"{psutil.net_io_counters().bytes_sent // 1024} KB/s"
    }

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    page = "index.html" if session == SESSION_ID else "login.html"
    with open(page, "r", encoding="utf-8") as f: return f.read()

# Простая авторизация (API)
@app.post("/api/login")
async def login(data: dict, response: Response):
    if data.get("password") == ADMIN_PASS:
        response.set_cookie(key="session", value=SESSION_ID)
        return {"ok": True}
    return {"ok": False}
