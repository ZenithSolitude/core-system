import os, shutil, psutil, datetime, json, zipfile
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ADMIN_PASS = "12345"
SESSION_ID = "zenith_777"
MODULES_DIR = "modules"
LOG_FILE = "system.log"

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)

def add_log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

# --- СИСТЕМНЫЕ API ---
@app.post("/api/login")
async def login(data: dict, response: Response):
    if data.get("password") == ADMIN_PASS:
        response.set_cookie(key="session", value=SESSION_ID)
        add_log("Успешный вход в админ-панель")
        return {"ok": True}
    return {"ok": False}

@app.get("/api/stats")
async def get_stats():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "net": f"{psutil.net_io_counters().bytes_sent // 1024} KB/s"
    }

@app.get("/api/logs")
async def get_logs():
    if not os.path.exists(LOG_FILE): return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [{"entry": l.strip()} for l in f.readlines()[-20:]]

@app.post("/api/modules/upload")
async def upload_zip(file: UploadFile = File(...)):
    path = os.path.join(MODULES_DIR, file.filename)
    with open(path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    with zipfile.ZipFile(path, 'r') as z:
        z.extractall(MODULES_DIR)
    os.remove(path)
    add_log(f"Установлен новый модуль: {file.filename}")
    return {"status": "ok"}

@app.get("/api/modules/list")
async def list_modules():
    mods = []
    for d in os.listdir(MODULES_DIR):
        p = os.path.join(MODULES_DIR, d, "config.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f: mods.append(json.load(f))
    return mods

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    page = "index.html" if session == SESSION_ID else "login.html"
    with open(page, "r", encoding="utf-8") as f: return f.read()
