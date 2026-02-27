import os, shutil, psutil, datetime, json, zipfile
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODULES_DIR = "modules"
DATA_FILE = "data.json"
LOG_FILE = "system.log"
SESSION_ID = "zenith_777_secure"

for d in [MODULES_DIR]: 
    if not os.path.exists(d): os.makedirs(d)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [{"id": "1", "user": "admin", "pass": "12345", "role": "Owner"}]}, f)

def add_log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().strftime('%H:%M:%S')} - {msg}\n")

# --- API ---
@app.post("/api/login")
async def login(d: dict, r: Response):
    db = json.load(open(DATA_FILE))
    for u in db["users"]:
        if d.get("user") == u["user"] and d.get("pass") == u["pass"]:
            r.set_cookie(key="session", value=SESSION_ID, path="/")
            add_log(f"Вход пользователя: {u['user']}")
            return {"ok": True}
    return {"ok": False}

@app.get("/api/users")
async def get_users():
    return json.load(open(DATA_FILE))["users"]

@app.get("/api/logs")
async def get_logs():
    if not os.path.exists(LOG_FILE): return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return [{"entry": l.strip()} for l in f.readlines()[-30:]]

@app.get("/api/stats")
async def stats():
    return {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}

@app.get("/api/modules/list")
async def list_mods():
    mods = []
    for d in os.listdir(MODULES_DIR):
        p = os.path.join(MODULES_DIR, d, "config.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                try: mods.append(json.load(f))
                except: continue
    return mods

@app.post("/api/modules/upload")
async def upload_zip(file: UploadFile = File(...)):
    path = os.path.join(MODULES_DIR, file.filename)
    with open(path, "wb") as b: shutil.copyfileobj(file.file, b)
    folder = os.path.join(MODULES_DIR, file.filename.replace(".zip", ""))
    if os.path.exists(folder): shutil.rmtree(folder)
    with zipfile.ZipFile(path, 'r') as z: z.extractall(folder)
    os.remove(path)
    add_log(f"Установлен модуль: {file.filename}")
    return {"ok": True}

@app.delete("/api/modules/{mod_id}")
async def delete_mod(mod_id: str):
    # Удаляем папку модуля по ID
    for d in os.listdir(MODULES_DIR):
        p = os.path.join(MODULES_DIR, d, "config.json")
        if os.path.exists(p):
            with open(p, "r") as f:
                if json.load(f).get("id") == mod_id:
                    shutil.rmtree(os.path.join(MODULES_DIR, d))
                    return {"ok": True}
    return {"ok": False}

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    page = "index.html" if session == SESSION_ID else "login.html"
    with open(page, "r", encoding="utf-8") as f: return f.read()
