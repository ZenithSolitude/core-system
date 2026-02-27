import os, shutil, psutil, datetime, json, zipfile
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODULES_DIR = "modules"
DATA_FILE = "data.json"
SESSION_ID = "zenith_777_secure"

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [{"id": "1", "user": "admin", "pass": "12345", "role": "Owner"}]}, f)

# --- СИСТЕМНЫЕ ФУНКЦИИ ---
@app.post("/api/login")
async def login(d: dict, r: Response):
    db = json.load(open(DATA_FILE))
    for u in db["users"]:
        if d.get("user") == u["user"] and d.get("pass") == u["pass"]:
            r.set_cookie(key="session", value=SESSION_ID, httponly=True)
            return {"ok": True}
    return {"ok": False}

@app.get("/api/stats")
async def stats():
    return {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}

@app.get("/api/modules/list")
async def list_mods():
    mods = []
    for d in os.listdir(MODULES_DIR):
        base_path = os.path.join(MODULES_DIR, d)
        if not os.path.isdir(base_path): continue
        # Ищем config.json даже если он внутри подпапки
        conf_found = None
        for root, dirs, files in os.walk(base_path):
            if "config.json" in files:
                conf_found = os.path.join(root, "config.json")
                break
        if conf_found:
            with open(conf_found, "r", encoding="utf-8") as f:
                m = json.load(f)
                m["folder"] = d
                mods.append(m)
    return mods

@app.post("/api/modules/upload")
async def upload_zip(file: UploadFile = File(...)):
    mod_name = file.filename.replace(".zip", "")
    temp_path = os.path.join(MODULES_DIR, file.filename)
    extract_path = os.path.join(MODULES_DIR, mod_name)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    with zipfile.ZipFile(temp_path, 'r') as z:
        z.extractall(extract_path)
    
    os.remove(temp_path)
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    page = "index.html" if session == SESSION_ID else "login.html"
    with open(page, "r", encoding="utf-8") as f: return f.read()
