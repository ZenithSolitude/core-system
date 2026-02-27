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

# --- API ---
@app.post("/api/login")
async def login(d: dict, r: Response):
    db = json.load(open(DATA_FILE))
    for u in db["users"]:
        if d.get("user") == u["user"] and d.get("pass") == u["pass"]:
            r.set_cookie(key="session", value=SESSION_ID, path="/")
            return {"ok": True}
    return {"ok": False}

@app.get("/api/stats")
async def stats():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

@app.get("/api/modules/list")
async def list_mods():
    mods = []
    if not os.path.exists(MODULES_DIR): return []
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
    with zipfile.ZipFile(path, 'r') as z: z.extractall(folder)
    os.remove(path)
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def index(session: str = Cookie(None)):
    page = "index.html" if session == SESSION_ID else "login.html"
    with open(page, "r", encoding="utf-8") as f: return f.read()
