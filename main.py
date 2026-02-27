import os, shutil, psutil, datetime, json, zipfile
from fastapi import FastAPI, UploadFile, File, Response, Cookie, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODULES_DIR = "modules"
DATA_FILE = "data.json"
SESSION_ID = "zenith_777_secure"

# Создаем папки и файлы если их нет
if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [{"id": "1", "user": "admin", "pass": "12345", "role": "Owner"}]}, f)

# --- ЛОГИН ---
@app.post("/api/login")
async def login(d: dict, response: Response):
    try:
        with open(DATA_FILE, "r") as f:
            db = json.load(f)
        
        user_val = d.get("user")
        pass_val = d.get("pass")
        
        for u in db["users"]:
            if u["user"] == user_val and u["pass"] == pass_val:
                response.set_cookie(key="session", value=SESSION_ID, path="/", httponly=False)
                return {"ok": True}
        return {"ok": False, "msg": "Wrong login/pass"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}

# --- СИСТЕМА ---
@app.get("/api/stats")
async def stats():
    return {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}

@app.get("/api/modules/list")
async def list_mods():
    mods = []
    if not os.path.exists(MODULES_DIR): return []
    for d in os.listdir(MODULES_DIR):
        bp = os.path.join(MODULES_DIR, d)
        if not os.path.isdir(bp): continue
        for root, dirs, files in os.walk(bp):
            if "config.json" in files:
                with open(os.path.join(root, "config.json"), "r", encoding="utf-8") as f:
                    m = json.load(f)
                    m["folder"] = d
                    mods.append(m)
                    break
    return mods

@app.post("/api/modules/upload")
async def upload_zip(file: UploadFile = File(...)):
    mod_name = file.filename.replace(".zip", "")
    temp_p = os.path.join(MODULES_DIR, file.filename)
    extr_p = os.path.join(MODULES_DIR, mod_name)
    with open(temp_p, "wb") as b: shutil.copyfileobj(file.file, b)
    with zipfile.ZipFile(temp_p, 'r') as z: z.extractall(extr_p)
    os.remove(temp_p)
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    page = "index.html" if session == SESSION_ID else "login.html"
    if not os.path.exists(page): return f"Error: {page} not found"
    with open(page, "r", encoding="utf-8") as f: return f.read()
