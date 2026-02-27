import os, shutil, psutil, datetime, uuid, requests, zipfile
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- КОНФИГ ---
ADMIN_USER = "admin"
ADMIN_PASS = "12345"
SESSION_ID = "zenith_secret_777"
MODULES_DIR = "modules"
GALLERY_FILE = "gallery_links.txt"

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)
logging.basicConfig(filename='system.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_ev(txt): logging.info(txt)

async def is_auth(session: str = Cookie(None)):
    if session != SESSION_ID: raise HTTPException(status_code=401)
    return True

# --- API ---
@app.post("/api/login")
async def login(data: dict, response: Response):
    if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASS:
        response.set_cookie(key="session", value=SESSION_ID, httponly=True)
        log_ev("Вход в систему")
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
    if not os.path.exists('system.log'): return []
    with open('system.log', 'r') as f:
        return [{"entry": line.strip()} for line in f.readlines()[-30:]]

# УНИВЕРСАЛЬНАЯ ЗАГРУЗКА ZIP
@app.post("/api/modules/upload")
async def upload_module(file: UploadFile = File(...)):
    path = os.path.join(MODULES_DIR, file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    if file.filename.endswith('.zip'):
        with zipfile.ZipFile(path, 'r') as z:
            z.extractall(MODULES_DIR)
        os.remove(path)
        log_ev(f"Установлен модуль из архива: {file.filename}")
    return {"status": "success"}

# ФОТО-ФУНКЦИЯ (Встроенная)
@app.post("/api/photos/upload")
async def up_photo(file: UploadFile = File(...)):
    try:
        resp = requests.post("https://telegra.ph/upload", files={'file': (file.filename, file.file, file.content_type)})
        url = "https://telegra.ph" + resp.json()[0]['src']
        with open(GALLERY_FILE, "a") as f: f.write(url + "\n")
        log_ev(f"Фото загружено в облако: {url}")
        return {"url": url}
    except: return {"error": "fail"}

@app.get("/api/photos/list")
async def list_ph():
    if not os.path.exists(GALLERY_FILE): return []
    with open(GALLERY_FILE, "r") as f: return [l.strip() for l in f.readlines()]

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    page = "index.html" if session == SESSION_ID else "login.html"
    with open(page, "r", encoding="utf-8") as f: return f.read()
