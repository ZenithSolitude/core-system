import os
import zipfile
import subprocess
import importlib.util

def install_module_from_github(repo_url):
    module_name = repo_url.split('/')[-1]
    path = f"./modules/{module_name}"
    
    # 1. Клонируем или скачиваем архив
    os.system(f"git clone {repo_url} {path}")
    
    # 2. Устанавливаем зависимости модуля
    if os.path.exists(f"{path}/requirements.txt"):
        subprocess.run(["pip", "install", "-r", f"{path}/requirements.txt"])
    
    # 3. Динамически импортируем роуты модуля в FastAPI
    spec = importlib.util.spec_from_file_location(module_name, f"{path}/router.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module.router # Возвращаем роутер для подключения к основному приложению
