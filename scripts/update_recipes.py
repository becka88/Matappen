import json, re, hashlib, time, concurrent.futures
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recipes.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MatappenRecipeIndexer/3.1)", "Accept-Language": "sv-SE,sv;q=0.9"}
TIMEOUT = 8
MAX_LINKS_PER_SOURCE = 80
MAX_TOTAL_PAGES = 180
MAX_WORKERS = 10
MAX_RUNTIME_SECONDS = 6 * 60

SOURCES = {
    "ICA": {"hosts": {"www.ica.se","ica.se"}, "seeds": [
        "https://www.ica.se/recept/vardag/", "https://www.ica.se/recept/middag/",
        "https://www.ica.se/recept/kyckling/", "https://www.ica.se/recept/kottfars/",
        "https://www.ica.se/recept/pasta/", "https://www.ica.se/recept/vegetariskt/"]},
    "Arla": {"hosts": {"www.arla.se","arla.se"}, "seeds": [
        "https://www.arla.se/recept/samling/kyckling-vardag/",
        "https://www.arla.se/recept/samling/vardag-pasta/",
        "https://www.arla.se/recept/samling/kottfars-vardag/",
        "https://www.arla.se/recept/samling/vegetarisk-vardag/"]},
    "Köket": {"hosts": {"www.koket.se","koket.se"}, "seeds": [
        "https://www.koket.se/recept", "https://www.koket.se/vardag",
        "https://www.koket.se/kyckling", "https://www.koket.se/pasta"]},
}

def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def get(url):
    r=requests.get(url,headers=HEADERS,timeout=TIMEOUT); r.raise_for_status(); return r.text

def source_ok(source,url):
    try: return urlparse(url).netloc.lower() in SOURCES[source]["hosts"]
    except Exception: return False

def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():
            if isinstance(x,(dict,list)): yield from walk(x)
    elif isinstance(v,list):
        for x in v: yield from walk(x)

def mins(v):
    if not v: return None
    s=str(v)
    if s.startswith("PT"):
        h=re.search(r"(\d+)H",s); m=re.search(r"(\d+)M",s)
        return (int(h.group(1))*60 if h else 0)+(int(m.group(1)) if m else 0)
    n=re.search(r"\d+",s); return int(n.group()) if n else None

def portions(v):
    if isinstance(v,list): v=v[0] if v else None
    n=re.search(r"\d+",str(v or "")); return int(n.group()) if n else None

def image(v,base):
    vals=v if isinstance(v,list) else [v]
    for x in vals:
        if isinstance(x,dict): x=x.get("url")
        if isinstance(x,str):
            u=urljoin(base,x)
            if u.startswith("http"): return u
    return None

def tags(name,ings):
    t=(name+" "+" ".join(ings)).lower(); out=[]
    for tag,words in {"kyckling":["kyckling"],"kött":["kött","färs","biff","korv","fläsk"],"pasta":["pasta","spaghetti","lasagne","makaron","penne"],"vegetariskt":["vegetar","linser","bönor","tofu","halloumi"],"gryta":["gryta","stroganoff","chili"],"fredag":["taco","burrito","pizza","quesadilla"]}.items():
        if any(w in t for w in words): out.append(tag)
    return out

def normalize(obj,source,page):
    name=clean(obj.get("name") or obj.get("headline")); ings=obj.get("recipeIngredient") or []
    if not isinstance(ings,list): return None
    ings=[clean(x) for x in ings if clean(x)]
    if len(name)<3 or len(ings)<2: return None
    raw=obj.get("url") or page
    if isinstance(raw,dict): raw=raw.get("@id") or raw.get("url") or page
    url=urljoin(page,str(raw))
    if not source_ok(source,url): url=page
    if not source_ok(source,url): return None
    return {"id":hashlib.sha1(url.encode()).hexdigest()[:20],"name":name,"source":source,"url":url,"minutes":mins(obj.get("totalTime") or obj.get("cookTime") or obj.get("prepTime")),"portions":portions(obj.get("recipeYield")),"ingredients":ings,"image":image(obj.get("image"),page),"tags":tags(name,ings),"external":True}

def parse_page(source,url):
    try:
        soup=BeautifulSoup(get(url),"html.parser"); found=[]
        for s in soup.find_all("script",type=re.compile(r"ld\+json",re.I)):
            raw=s.string or s.get_text() or ""
            if not raw.strip(): continue
            try: data=json.loads(raw)
            except Exception: continue
            for obj in walk(data):
                typ=obj.get("@type"); types=typ if isinstance(typ,list) else [typ]
                if "Recipe" in types:
                    r=normalize(obj,source,url)
                    if r: found.append(r)
        return found
    except Exception: return []

def looks_recipe(source,url):
    p=urlparse(url).path.lower().rstrip("/")
    if source=="ICA": return p.startswith("/recept/") and len([x for x in p.split("/") if x])>=2
    if source=="Arla": return p.startswith("/recept/") and "/samling/" not in p
    if source=="Köket": return p.count("/")>=1 and not any(x in p for x in ("/mat/","/artiklar/","/program/","/tv/","/nyheter/"))
    return False

def discover(source,seed):
    try: soup=BeautifulSoup(get(seed),"html.parser")
    except Exception: return []
    out=[]; seen=set()
    for a in soup.find_all("a",href=True):
        u=urljoin(seed,a["href"].split("#")[0])
        if not source_ok(source,u) or not looks_recipe(source,u) or u in seen: continue
        seen.add(u); out.append(u)
        if len(out)>=MAX_LINKS_PER_SOURCE: break
    return out

started=time.time(); by_url={}
try:
    old=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
except Exception: old=[]
for r in old if isinstance(old,list) else []:
    if r.get("external") is True and r.get("source") in SOURCES and source_ok(r["source"],r.get("url","")) and isinstance(r.get("ingredients"),list) and len(r["ingredients"])>=2:
        by_url[r["url"]]=r

candidates=[]
for source,cfg in SOURCES.items():
    local=[]
    for seed in cfg["seeds"]:
        if time.time()-started>MAX_RUNTIME_SECONDS: break
        local.extend(discover(source,seed))
    seen=set(); uniq=[]
    for u in local:
        if u not in seen: seen.add(u); uniq.append(u)
    candidates.extend((source,u) for u in uniq[:MAX_LINKS_PER_SOURCE])
candidates=candidates[:MAX_TOTAL_PAGES]

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futures=[ex.submit(parse_page,s,u) for s,u in candidates]
    for fut in concurrent.futures.as_completed(futures):
        if time.time()-started>MAX_RUNTIME_SECONDS: break
        try:
            for r in fut.result(): by_url[r["url"]]=r
        except Exception: pass

recipes=sorted([r for r in by_url.values() if r.get("external") is True and r.get("source") in SOURCES and source_ok(r["source"],r.get("url","")) and isinstance(r.get("ingredients"),list) and len(r["ingredients"])>=2], key=lambda r:(r.get("source",""),r.get("name","").lower()))
OUT.write_text(json.dumps(recipes,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Saved {len(recipes)} verified source recipes in {round(time.time()-started,1)}s. Sources: ICA, Arla, Köket only.")
