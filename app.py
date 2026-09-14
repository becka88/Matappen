import os, hmac, hashlib, secrets, json, threading, time
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from catalog import search_catalog, refresh_catalog, refresh_due, count_catalog

BASE = Path(__file__).parent
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax", https_only=True)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

RECIPES = json.loads((BASE / "recipes.json").read_text(encoding="utf-8"))

DAYS = ["Måndag","Tisdag","Onsdag","Torsdag","Fredag","Lördag","Söndag"]

def authed(request: Request):
    return bool(request.session.get("auth"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not authed(request):
        return (BASE / "login.html").read_text(encoding="utf-8")
    return (BASE / "index.html").read_text(encoding="utf-8")

@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if not APP_PASSWORD:
        return HTMLResponse("APP_PASSWORD saknas i serverns miljövariabler.", status_code=500)
    if hmac.compare_digest(password, APP_PASSWORD):
        request.session["auth"] = True
        return RedirectResponse("/", status_code=303)
    html = (BASE / "login.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("<!--ERROR-->", '<div class="error">Fel lösenord</div>'), status_code=401)

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/api/bootstrap")
async def bootstrap(request: Request):
    if not authed(request):
        return JSONResponse({"error":"unauthorized"}, status_code=401)

    # Return immediately; refresh stale web catalog in background.
    if refresh_due(24):
        threading.Thread(target=refresh_catalog, kwargs={"max_detail_pages": 180}, daemon=True).start()

    recipes = search_catalog("", 160)
    # Planner uses available dinner-like recipes; fallback guarantees a usable week.
    usable = [r for r in recipes if r.get("name")]
    picked=[]
    used=set()
    for i in range(7):
        pool=[r for r in usable if r["name"] not in used]
        if not pool: pool=usable
        pool=sorted(pool, key=lambda r: (0 if (i<4 and (r.get("minutes") or 999)<=40) else 1, r.get("minutes") or 999, r["name"]))
        r=pool[i % min(len(pool), 12)]
        used.add(r["name"]); picked.append(r)

    return {
      "recipes": recipes,
      "week": [{"day":DAYS[i],"recipe":picked[i]} for i in range(7)],
      "catalog": count_catalog(),
      "family":{"kidsArrive":True,"lunchboxes":2,"tacoFriday":True},
      "quickItems":["Mjölk","Bröd","Ägg","Yoghurt","Diskmedel","Toapapper"]
    }

@app.get("/api/recipes")
async def recipes_api(request: Request, q: str = "", limit: int = 120):
    if not authed(request):
        return JSONResponse({"error":"unauthorized"}, status_code=401)
    return {"items": search_catalog(q, min(max(limit,1),300)), "catalog": count_catalog()}

@app.post("/api/refresh-recipes")
async def refresh_recipes_api(request: Request):
    if not authed(request):
        return JSONResponse({"error":"unauthorized"}, status_code=401)
    stats=refresh_catalog(max_detail_pages=240)
    return {"ok":True,"stats":stats,"catalog":count_catalog()}
