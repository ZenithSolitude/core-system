import os, shutil, psutil, datetime, uuid, requests
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI()

# Разрешаем сайту работать в браузере
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- НАСТРОЙКИ ---
ADMIN_USER = "admin"
ADMIN_PASS = "12345" # ОБЯЗАТЕЛЬНО ЗАПОМНИ: логин admin, пароль 12345
SESSION_ID = "zenith_secret_token_777"
GALLERY_FILE = "gallery_links.txt"

logging.basicConfig(filename='system.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Проверка: залогинен ли пользователь?
async def is_logged_in(session: str = Cookie(None)):
    return session == SESSION_ID

# --- АВТОРИЗАЦИЯ ---
@app.post("/api/login")
async def login(data: dict, response: Response):
    if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASS:
        response.set_cookie(key="session", value=SESSION_ID, httponly=True)
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Неверный пароль")

@app.get("/api/logout")
async def logout(response: Response):
    response.delete_cookie("session")
    return RedirectResponse(url="/")

# --- СТАТИСТИКА И ЛОГИ ---
@app.get("/api/stats")
async def get_stats():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "net": "Active"
    }

@app.get("/api/logs")
async def get_logs():
    if not os.path.exists('system.log'): return []
    with open('system.log', 'r') as f:
        return [{"entry": line.strip()} for line in f.readlines()[-20:]]

# --- МОДУЛЬ: ФОТООБМЕННИК ---
@app.post("/api/photos/upload")
async def upload_photo(file: UploadFile = File(...)):
    # Отправляем файл на анонимный хостинг (Telegra.ph)
    files = {'file': (file.filename, file.file, file.content_type)}
    try:
        resp = requests.post("https://telegra.ph/upload", files=files)
        img_url = "https://telegra.ph" + resp.json()[0]['src']
        # Сохраняем ссылку в файл на сервере
        with open(GALLERY_FILE, "a") as f:
            f.write(img_url + "\n")
        logging.info(f"Фото загружено: {img_url}")
        return {"url": img_url}
    except:
        return {"error": "Ошибка загрузки"}

@app.get("/api/photos/list")
async def list_photos():
    if not os.path.exists(GALLERY_FILE): return []
    with open(GALLERY_FILE, "r") as f:
        return [line.strip() for line in f.readlines()]

# --- СТРАНИЦЫ (ИНТЕРФЕЙС) ---
@app.get("/", response_class=HTMLResponse)
async def index_page(logged_in: bool = Depends(is_logged_in)):
    file_to_open = "index.html" if logged_in else "login.html"
    with open(file_to_open, "r", encoding="utf-8") as f:
        return f.read()
