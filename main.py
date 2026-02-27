import os, shutil, psutil, datetime, json, zipfile, requests
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- ХРАНИЛИЩЕ ---
ADMIN_PASS = "12345"
SESSION_ID = "zenith_777"
MODULES_DIR = "modules"
DATA_FILE = "data.json" # Тут храним пользователей

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)

# Инициализация БД пользователей
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [{"id": "1", "user": "admin", "pass": "12345", "role": "Owner"}]}, f)

def get_db():
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# --- API ПОЛЬЗОВАТЕЛИ ---
@app.get("/api/users")
async def list_users(): return get_db()["users"]

@app.post("/api/users")
async def add_user(u: dict):
    db = get_db()
    u["id"] = str(len(db["users"]) + 1)
    db["users"].append(u)
    save_db(db)
    return u

@app.delete("/api/users/{uid}")
async def del_user(uid: str):
    db = get_db()
    db["users"] = [u for u in db["users"] if u["id"] != uid]
    save_db(db)
    return {"ok": True}

# --- API МОДУЛИ ---
@app.get("/api/modules/list")
async def list_mods():
    mods = []
    if not os.path.exists(MODULES_DIR): return []
    for d in os.listdir(MODULES_DIR):
        p = os.path.join(MODULES_DIR, d, "config.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                m = json.load(f)
                m["folder"] = d # Запоминаем папку для удаления
                mods.append(m)
    return mods

@app.delete("/api/modules/{folder}")
async def delete_mod(folder: str):
    path = os.path.join(MODULES_DIR, folder)
    if os.path.exists(path):
        shutil.rmtree(path)
        return {"ok": True}
    return {"error": "not found"}

@app.post("/api/modules/upload")
async def upload_zip(file: UploadFile = File(...)):
    path = os.path.join(MODULES_DIR, file.filename)
    with open(path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    with zipfile.ZipFile(path, 'r') as z:
        z.extractall(MODULES_DIR)
    os.remove(path)
    return {"ok": True}

# --- СИСТЕМА ---
@app.get("/api/stats")
async def stats():
    return {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}

@app.post("/api/login")
async def login(d: dict, r: Response):
    db = get_db()
    for u in db["users"]:
        if d.get("user") == u["user"] and d.get("pass") == u["pass"]:
            r.set_cookie(key="session", value=SESSION_ID)
            return {"ok": True}
    return {"ok": False}

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    p = "index.html" if session == SESSION_ID else "login.html"
    with open(p, "r", encoding="utf-8") as f: return f.read()
