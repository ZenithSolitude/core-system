import os
import shutil
import psutil
import zipfile
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from git import Repo

app = FastAPI(title="Modular Core System")

# Разрешаем CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODULES_DIR = "./modules"

@app.get("/api/stats")
async def get_stats():
    """А: Дашборд - Нагрузка системы"""
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "net": psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    }

@app.get("/api/modules")
async def list_modules():
    """Список установленных модулей"""
    if not os.path.exists(MODULES_DIR):
        return []
    return [d for d in os.listdir(MODULES_DIR) if os.path.isdir(os.path.join(MODULES_DIR, d))]

@app.post("/api/modules/upload-zip")
async def upload_module_zip(file: UploadFile = File(...)):
    """Загрузка модуля через ZIP"""
    file_path = f"{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(MODULES_DIR)
    
    os.remove(file_path)
    return {"status": "success", "message": "Module installed from ZIP"}

@app.post("/api/modules/install-github")
async def install_from_github(repo_url: str):
    """Загрузка модуля через GitHub ссылку"""
    module_name = repo_url.split("/")[-1].replace(".git", "")
    target_path = os.path.join(MODULES_DIR, module_name)
    
    if os.path.exists(target_path):
        return {"status": "error", "message": "Module already exists"}
    
    Repo.clone_from(repo_url, target_path)
    return {"status": "success", "message": f"Module {module_name} installed"}

@app.get("/")
async def root():
    return {"message": "Core System is Running", "docs": "/docs"}
