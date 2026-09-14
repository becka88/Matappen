
import json, re, sqlite3, time, hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).parent
DB = BASE / "recipe_catalog.sqlite3"
FALLBACK = json.loads((BASE / "recipes.json").read_text(encoding="utf-8"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Matappen/1.0; personal meal-planning app)"
}
TIMEOUT = 12

# Public discovery pages. The index is refreshed periodically and new links are merged,
# so the local catalog can grow over time rather than being a fixed bundle.
SOURCES = {
    "ICA": [
        "https://www.ica.se/recept/vardag/",
        "https://www.ica.se/recept/vardag/middag/",
        "https://www.ica.se/recept/ingredienser/kyckling/",
        "https://www.ica.se/recept/ingredienser/kottfars/",
        "https://www.ica.se/recept/ingredienser/korv/",
        "https://www.ica.se/recept/ingredienser/flaskfile/",
        "https://www.ica.se/recept/pasta/",
    ],
    "Arla": [
        "https://www.arla.se/recept/samling/kyckling-vardag/",
        "https://www.arla.se/recept/samling/snabb-kyckling-vardag/",
        "https://www.arla.se/recept/samling/vardag-pasta/",
        "https://www.arla.se/recept/samling/kyckling-pasta/",
        "https://www.arla.se/recept/samling/kottfars-pasta/",
    ],
    "Köket": [
        "https://www.koket.se/recept",
        "https://www.koket.se/vardag",
        "https://www.koket.se/populara-recept",
        "https://www.koket.se/recept-med-kyckling-och-kycklingfile",
        "https://www.koket.se/mat/ingredienser/kyckling",
        "https://www.koket.se/mat/ingredienser/kyckling/kycklingfile",
        "https://www.koket.se/kyckling-20-populara-vardagsrecept",
    ],
}

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS recipes (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      source TEXT NOT NULL,
      url TEXT NOT NULL UNIQUE,
      minutes INTEGER,
      ingredients_json TEXT,
      image TEXT,
      tags_json TEXT,
      fetched_at INTEGER NOT NULL,
      is_fallback INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_recipe_name ON recipes(name);
    CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
    """)
    return c

def clean_time(v):
    if not v: return None
    if isinstance(v, (int,float)): return int(v)
    s = str(v)
    # ISO 8601 PT1H30M
    if s.startswith("PT"):
        h = re.search(r"(\d+)H", s)
        m = re.search(r"(\d+)M", s)
        return (int(h.group(1))*60 if h else 0) + (int(m.group(1)) if m else 0)
    nums = [int(x) for x in re.findall(r"\d+", s)]
    if not nums: return None
    if ("tim" in s.lower() or " h" in s.lower()) and len(nums) >= 1:
        return nums[0]*60 + (nums[1] if len(nums)>1 else 0)
    return nums[0]

def classify(name, ingredients):
    t = (name + " " + " ".join(ingredients or [])).lower()
    tags = []
    if any(x in t for x in ["kyckling","korv","färs","kött","fläsk","biff"]): tags.append("kött")
    if any(x in t for x in ["pasta","spaghetti","lasagne","makaron"]): tags.append("pasta")
    if any(x in t for x in ["gryta","stroganoff","chili"]): tags.append("gryta")
    if any(x in t for x in ["taco","burrito","quesadilla"]): tags.append("fredag")
    return tags

def normalize_recipe(obj, source, url):
    name = obj.get("name") or obj.get("headline")
    if not name or not isinstance(name, str): return None
    ingredients = obj.get("recipeIngredient") or []
    if not isinstance(ingredients, list): ingredients = []
    mins = clean_time(obj.get("totalTime") or obj.get("cookTime") or obj.get("prepTime"))
    image = obj.get("image")
    if isinstance(image, list): image = image[0] if image else None
    if isinstance(image, dict): image = image.get("url")
    return {
        "id": hashlib.sha1(url.encode()).hexdigest()[:20],
        "name": name.strip(),
        "source": source,
        "url": url,
        "minutes": mins,
        "ingredients": [str(x).strip() for x in ingredients if str(x).strip()][:60],
        "image": image if isinstance(image, str) else None,
        "tags": classify(name, ingredients),
    }

def jsonld_recipes(html, source, page_url):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.get_text(strip=True))
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            obj = stack.pop()
            if isinstance(obj, dict):
                typ = obj.get("@type")
                if typ == "Recipe" or (isinstance(typ, list) and "Recipe" in typ):
                    url = obj.get("url") or page_url
                    if isinstance(url, dict): url = url.get("@id") or page_url
                    r = normalize_recipe(obj, source, urljoin(page_url, str(url)))
                    if r: found.append(r)
                graph = obj.get("@graph")
                if isinstance(graph, list): stack.extend(graph)
            elif isinstance(obj, list):
                stack.extend(obj)
    return found

def is_recipe_link(source, href):
    p = urlparse(href).path.lower()
    if source == "ICA":
        return p.startswith("/recept/") and len([x for x in p.split("/") if x]) >= 2 and not any(x in p for x in ["/vardag","/ingredienser/","/kategori/"])
    if source == "Arla":
        return p.startswith("/recept/") and "/samling/" not in p and len([x for x in p.split("/") if x]) >= 2
    if source == "Köket":
        # Individual Köket recipes generally live directly under /...; JSON-LD verification
        # on the fetched page below prevents articles from entering the catalog.
        return p.count("/") >= 1 and not any(x in p for x in ["/mat/ingredienser","/recept-med-","/populara-recept"])
    return False

def discover_links(source, url, html):
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(url).netloc
    out = []
    seen = set()
    for a in soup.find_all("a", href=True):
        u = urljoin(url, a["href"].split("#")[0])
        if urlparse(u).netloc != host: continue
        if not is_recipe_link(source, u): continue
        if u not in seen:
            seen.add(u); out.append(u)
    return out[:180]

def get(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def upsert(recipes):
    c = conn()
    now = int(time.time())
    for r in recipes:
        c.execute("""
        INSERT INTO recipes(id,name,source,url,minutes,ingredients_json,image,tags_json,fetched_at,is_fallback)
        VALUES(?,?,?,?,?,?,?,?,?,0)
        ON CONFLICT(url) DO UPDATE SET
          name=excluded.name, source=excluded.source, minutes=excluded.minutes,
          ingredients_json=excluded.ingredients_json, image=excluded.image,
          tags_json=excluded.tags_json, fetched_at=excluded.fetched_at
        """, (r["id"],r["name"],r["source"],r["url"],r["minutes"],
              json.dumps(r["ingredients"],ensure_ascii=False),r["image"],
              json.dumps(r["tags"],ensure_ascii=False),now))
    c.commit(); c.close()

def seed_fallback():
    c=conn()
    now=int(time.time())
    for r in FALLBACK:
        rid="fallback_"+hashlib.sha1(r["name"].encode()).hexdigest()[:16]
        ing=[f"{k}: {v}" for k,v in r.get("ings",{}).items()]
        c.execute("""INSERT OR IGNORE INTO recipes
        (id,name,source,url,minutes,ingredients_json,image,tags_json,fetched_at,is_fallback)
        VALUES(?,?,?,?,?,?,?,?,?,1)""",
        (rid,r["name"],"Matappen","",r.get("mins"),json.dumps(ing,ensure_ascii=False),
         None,json.dumps(r.get("tags",[]),ensure_ascii=False),now))
    c.commit(); c.close()

def refresh_catalog(max_detail_pages=220):
    seed_fallback()
    discovered=[]
    stats={"pages":0,"links":0,"recipes":0,"errors":[]}
    for source, pages in SOURCES.items():
        for page in pages:
            try:
                html=get(page); stats["pages"]+=1
                # Some collection pages themselves contain Recipe JSON-LD.
                direct=jsonld_recipes(html,source,page)
                if direct: upsert(direct); stats["recipes"]+=len(direct)
                links=discover_links(source,page,html)
                discovered.extend((source,u) for u in links)
                stats["links"]+=len(links)
            except Exception as e:
                stats["errors"].append(f"{source}: {type(e).__name__}")
    # Unique links; cap each refresh so hosting stays responsive.
    uniq=[]; seen=set()
    for x in discovered:
        if x[1] not in seen:
            seen.add(x[1]); uniq.append(x)
    for source,u in uniq[:max_detail_pages]:
        try:
            rs=jsonld_recipes(get(u),source,u)
            if rs:
                upsert(rs); stats["recipes"]+=len(rs)
        except Exception:
            continue
    c=conn()
    c.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('last_refresh',?)",(str(int(time.time())),))
    c.commit(); c.close()
    return stats

def last_refresh():
    c=conn()
    row=c.execute("SELECT value FROM meta WHERE key='last_refresh'").fetchone()
    c.close()
    return int(row["value"]) if row else 0

def refresh_due(hours=24):
    return time.time()-last_refresh() > hours*3600

def search_catalog(q="", limit=120):
    seed_fallback()
    c=conn()
    if q.strip():
        term=f"%{q.strip()}%"
        rows=c.execute("""SELECT * FROM recipes
          WHERE name LIKE ? OR ingredients_json LIKE ? OR tags_json LIKE ?
          ORDER BY is_fallback ASC, fetched_at DESC, name LIMIT ?""",
          (term,term,term,limit)).fetchall()
    else:
        rows=c.execute("""SELECT * FROM recipes
          ORDER BY is_fallback ASC, fetched_at DESC, name LIMIT ?""",(limit,)).fetchall()
    c.close()
    out=[]
    for row in rows:
        d=dict(row)
        d["ingredients"]=json.loads(d.pop("ingredients_json") or "[]")
        d["tags"]=json.loads(d.pop("tags_json") or "[]")
        d["external"]=not bool(d.pop("is_fallback"))
        out.append(d)
    return out

def count_catalog():
    seed_fallback()
    c=conn()
    row=c.execute("SELECT COUNT(*) n, SUM(CASE WHEN is_fallback=0 THEN 1 ELSE 0 END) external FROM recipes").fetchone()
    c.close()
    return {"total":row["n"],"external":row["external"] or 0}
