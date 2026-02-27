import os, shutil, psutil, zipfile, datetime, uuid
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging

app = FastAPI(title="Zenith Core OS")

# Настройка логирования в файл
logging.basicConfig(filename='system.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Имитация БД (в продакшене заменим на SQLite/PostgreSQL)
class User(BaseModel):
    id: str = None
    username: str
    role: str

users_db = [{"id": "1", "username": "admin", "role": "owner"}]
MODULES_DIR = "./modules"
if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)

def log_event(text):
    logging.info(text)

# --- API: МОНИТОРИНГ ---
@app.get("/api/stats")
async def get_stats():
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "net": f"{psutil.net_io_counters().bytes_sent // 1024} KB/s"
    }

# --- API: ПОЛЬЗОВАТЕЛИ ---
@app.get("/api/users")
async def get_users():
    return users_db

@app.post("/api/users")
async def create_user(user: User):
    user.id = str(uuid.uuid4())[:8]
    users_db.append(user.dict())
    log_event(f"Пользователь {user.username} создан")
    return user

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    global users_db
    users_db = [u for u in users_db if u['id'] != user_id]
    log_event(f"Пользователь {user_id} удален")
    return {"status": "deleted"}

# --- API: ЛОГИ ---
@app.get("/api/logs")
async def get_logs():
    if not os.path.exists('system.log'): return []
    with open('system.log', 'r') as f:
        lines = f.readlines()
    return [{"entry": line.strip()} for line in lines[-50:]] # последние 50 записей

# --- API: МОДУЛИ ---
@app.post("/api/modules/upload")
async def upload_module(file: UploadFile = File(...)):
    path = os.path.join(MODULES_DIR, file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    if file.filename.endswith('.zip'):
        with zipfile.ZipFile(path, 'r') as zip_ref:
            module_name = file.filename.replace('.zip', '')
            extract_path = os.path.join(MODULES_DIR, module_name)
            zip_ref.extractall(extract_path)
        os.remove(path)
        log_event(f"Модуль {module_name} установлен из ZIP")
    return {"status": "installed"}

# --- ГЛАВНАЯ СТРАНИЦА ---
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
