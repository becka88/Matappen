import json, re, hashlib, time, concurrent.futures
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"recipes.json"
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; MatappenRecipeIndexer/4.0)","Accept-Language":"sv-SE,sv;q=0.9"}
TIMEOUT=7; MAX_LINKS_PER_SEED=18; MAX_TOTAL_PAGES=180; MAX_WORKERS=12; MAX_RUNTIME_SECONDS=150
SOURCES={
"ICA":{"hosts":{"www.ica.se","ica.se"},"seeds":["https://www.ica.se/recept/vardag/","https://www.ica.se/recept/middag/","https://www.ica.se/recept/kyckling/","https://www.ica.se/recept/kottfars/","https://www.ica.se/recept/pasta/","https://www.ica.se/recept/vegetariskt/","https://www.ica.se/recept/fisk/","https://www.ica.se/recept/lax/","https://www.ica.se/recept/korv/"]},
"Arla":{"hosts":{"www.arla.se","arla.se"},"seeds":["https://www.arla.se/recept/samling/kyckling-vardag/","https://www.arla.se/recept/samling/vardag-pasta/","https://www.arla.se/recept/samling/kottfars-vardag/","https://www.arla.se/recept/samling/vegetarisk-vardag/"]},
"Köket":{"hosts":{"www.koket.se","koket.se"},"seeds":["https://www.koket.se/recept","https://www.koket.se/vardag","https://www.koket.se/kyckling","https://www.koket.se/pasta","https://www.koket.se/kottfars"]}}
def clean(v):return re.sub(r"\s+"," ",str(v or "")).strip()
def get(u):r=requests.get(u,headers=HEADERS,timeout=TIMEOUT);r.raise_for_status();return r.text
def source_ok(s,u):
 try:return urlparse(u).netloc.lower() in SOURCES[s]["hosts"]
 except:return False
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():
   if isinstance(x,(dict,list)):yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
def mins(v):
 if not v:return None
 s=str(v); h=re.search(r"(\d+)H",s); m=re.search(r"(\d+)M",s)
 if s.startswith("PT"):return (int(h.group(1))*60 if h else 0)+(int(m.group(1)) if m else 0)
 n=re.search(r"\d+",s);return int(n.group()) if n else None
def portions(v):
 if isinstance(v,list):v=v[0] if v else None
 n=re.search(r"\d+",str(v or ""));return int(n.group()) if n else None
def image(v,b):
 for x in (v if isinstance(v,list) else [v]):
  if isinstance(x,dict):x=x.get("url")
  if isinstance(x,str):
   u=urljoin(b,x)
   if u.startswith("http"):return u
def tags(n,i):
 t=(n+" "+" ".join(i)).lower();out=[]
 groups={"kyckling":["kyckling"],"köttfärs":["köttfärs","nötfärs","blandfärs","färs"],"fisk":["fisk","torsk","sej"],"lax":["lax"],"korv":["korv","falukorv"],"pasta":["pasta","spaghetti","lasagne","makaron","penne"],"vegetariskt":["vegetar","linser","bönor","tofu","halloumi"]}
 for k,ws in groups.items():
  if any(w in t for w in ws):out.append(k)
 return out
def normalize(o,s,p):
 n=clean(o.get("name") or o.get("headline"));ings=o.get("recipeIngredient") or []
 if not isinstance(ings,list):return None
 ings=[clean(x) for x in ings if clean(x)]
 if len(n)<3 or len(ings)<2:return None
 raw=o.get("url") or p
 if isinstance(raw,dict):raw=raw.get("@id") or raw.get("url") or p
 u=urljoin(p,str(raw))
 if not source_ok(s,u):u=p
 if not source_ok(s,u):return None
 return {"id":hashlib.sha1(u.encode()).hexdigest()[:20],"name":n,"source":s,"url":u,"minutes":mins(o.get("totalTime") or o.get("cookTime") or o.get("prepTime")),"portions":portions(o.get("recipeYield")),"ingredients":ings,"image":image(o.get("image"),p),"tags":tags(n,ings),"external":True}
def parse_page(s,u):
 try:
  soup=BeautifulSoup(get(u),"html.parser");out=[]
  for el in soup.find_all("script",type=re.compile(r"ld\+json",re.I)):
   try:d=json.loads(el.string or el.get_text() or "")
   except:continue
   for o in walk(d):
    typ=o.get("@type");types=typ if isinstance(typ,list) else [typ]
    if "Recipe" in types:
     r=normalize(o,s,u)
     if r:out.append(r)
  return out
 except:return []
def looks_recipe(s,u):
 p=urlparse(u).path.lower().rstrip("/")
 if s=="ICA":return p.startswith("/recept/") and len([x for x in p.split("/") if x])>=2
 if s=="Arla":return p.startswith("/recept/") and "/samling/" not in p
 if s=="Köket":return p.count("/")>=1 and not any(x in p for x in ("/mat/","/artiklar/","/program/","/tv/","/nyheter/","/profil/"))
 return False
def discover(s,seed):
 try:soup=BeautifulSoup(get(seed),"html.parser")
 except:return []
 out=[];seen=set()
 for a in soup.find_all("a",href=True):
  u=urljoin(seed,a["href"].split("#")[0])
  if source_ok(s,u) and looks_recipe(s,u) and u not in seen:
   seen.add(u);out.append(u)
   if len(out)>=MAX_LINKS_PER_SEED:break
 return out
started=time.monotonic();by={}
try:old=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
except:old=[]
for r in old if isinstance(old,list) else []:
 if r.get("external") is True and r.get("source") in SOURCES and source_ok(r["source"],r.get("url","")) and isinstance(r.get("ingredients"),list) and len(r["ingredients"])>=2:by[r["url"]]=r
buckets=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 jobs=[(s,seed,ex.submit(discover,s,seed)) for s,cfg in SOURCES.items() for seed in cfg["seeds"]]
 for s,seed,f in jobs:
  try:links=f.result()
  except:links=[]
  if links:buckets.append([(s,u) for u in links])
cands=[];seen=set()
while len(cands)<MAX_TOTAL_PAGES and any(buckets):
 nxt=[]
 for b in buckets:
  if not b:continue
  s,u=b.pop(0)
  if u not in seen:seen.add(u);cands.append((s,u))
  if b:nxt.append(b)
  if len(cands)>=MAX_TOTAL_PAGES:break
 buckets=nxt
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
 fs=[ex.submit(parse_page,s,u) for s,u in cands]
 for f in concurrent.futures.as_completed(fs):
  if time.monotonic()-started>MAX_RUNTIME_SECONDS:break
  try:
   for r in f.result():by[r["url"]]=r
  except:pass
recipes=sorted(by.values(),key=lambda r:(r.get("source",""),r.get("name","").lower()))
OUT.write_text(json.dumps(recipes,ensure_ascii=False,indent=2),encoding="utf-8")
def cov(ws):
 return sum(any(w in (r.get("name","")+" "+" ".join(r.get("ingredients",[]))+" "+" ".join(r.get("tags",[]))).lower() for w in ws) for r in recipes)
print(f"Saved {len(recipes)} verified source recipes. Coverage: köttfärs={cov(['köttfärs','nötfärs','blandfärs','färs'])} kyckling={cov(['kyckling'])} pasta={cov(['pasta','spaghetti','lasagne','makaron','penne'])} fisk={cov(['fisk','torsk','sej','lax'])}.")
