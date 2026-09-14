
def best_recipe_image(soup, base_url):
    """Prefer the recipe page's own main/share image."""
    candidates = []
    for attrs in (
        {"property":"og:image"},
        {"name":"twitter:image"},
        {"property":"twitter:image"},
    ):
        tag=soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            candidates.append(tag.get("content"))
    # JSON-LD Recipe image is often the most semantically precise fallback.
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data=json.loads(tag.string or tag.get_text() or "{}")
        except Exception:
            continue
        stack=data if isinstance(data,list) else [data]
        while stack:
            obj=stack.pop()
            if isinstance(obj,dict):
                typ=obj.get("@type")
                types=typ if isinstance(typ,list) else [typ]
                if "Recipe" in types:
                    im=obj.get("image")
                    if isinstance(im,str): candidates.append(im)
                    elif isinstance(im,list):
                        candidates.extend(x for x in im if isinstance(x,str))
                    elif isinstance(im,dict) and isinstance(im.get("url"),str):
                        candidates.append(im["url"])
                stack.extend(v for v in obj.values() if isinstance(v,(dict,list)))
            elif isinstance(obj,list):
                stack.extend(obj)
    from urllib.parse import urljoin
    for u in candidates:
        u=urljoin(base_url,u)
        if u.startswith("http") and not any(x in u.lower() for x in ("logo","icon","avatar")):
            return u
    return ""

def enrich_missing_images(items):
    """Visit each source recipe page only when its image is missing."""
    missing=[x for x in items if not x.get("image") and x.get("url")]
    print(f"Bildkontroll: {len(missing)} recept saknar bild")
    session=requests.Session()
    session.headers.update(HEAD)
    fixed=0
    for i,item in enumerate(missing,1):
        try:
            rr=session.get(item["url"],timeout=20)
            rr.raise_for_status()
            im=best_recipe_image(BeautifulSoup(rr.text,"html.parser"),item["url"])
            if im:
                item["image"]=im
                fixed+=1
        except Exception as e:
            print("IMAGE", item.get("source"), item.get("url"), type(e).__name__)
    print(f"Bildkontroll: hittade {fixed} nya originalbilder")
    return items

import json,re,hashlib,time
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"recipes.json"
HEAD={"User-Agent":"Mozilla/5.0 (compatible; MatappenRecipeIndexer/1.0; personal use)"}
TIMEOUT=15

PAGES={
"ICA":[
 "https://www.ica.se/recept/vardag/","https://www.ica.se/recept/vardag/middag/",
 "https://www.ica.se/recept/ingredienser/kyckling/","https://www.ica.se/recept/ingredienser/kottfars/",
 "https://www.ica.se/recept/ingredienser/lax/","https://www.ica.se/recept/ingredienser/torsk/",
 "https://www.ica.se/recept/pasta/","https://www.ica.se/recept/korv/",
 "https://www.ica.se/recept/vegetariskt/","https://www.ica.se/recept/soppa/",
 "https://www.ica.se/recept/gryta/","https://www.ica.se/recept/under-30-minuter/"
],
"Arla":[
 "https://www.arla.se/recept/samling/kyckling-vardag/","https://www.arla.se/recept/samling/vardag-pasta/",
 "https://www.arla.se/recept/samling/kyckling-pasta/","https://www.arla.se/recept/samling/kottfars-pasta/",
 "https://www.arla.se/recept/samling/kottfars-vardag/","https://www.arla.se/recept/samling/lax-vardag/",
 "https://www.arla.se/recept/samling/fisk-vardag/","https://www.arla.se/recept/samling/vegetarisk-vardag/"
],
"Köket":[
 "https://www.koket.se/recept","https://www.koket.se/vardag","https://www.koket.se/populara-recept",
 "https://www.koket.se/mat/typ-av-maltid/vardagsmiddag","https://www.koket.se/kyckling",
 "https://www.koket.se/lax","https://www.koket.se/pasta","https://www.koket.se/torsk",
 "https://www.koket.se/korv","https://www.koket.se/vegetariskt"
]}

def get(u):
 r=requests.get(u,headers=HEAD,timeout=TIMEOUT);r.raise_for_status();return r.text

def mins(v):
 if not v:return None
 s=str(v)
 h=re.search(r"(\d+)H",s);m=re.search(r"(\d+)M",s)
 if s.startswith("PT"):return (int(h.group(1))*60 if h else 0)+(int(m.group(1)) if m else 0)
 n=re.findall(r"\d+",s)
 return int(n[0]) if n else None

def normalize(obj,source,url):
 name=obj.get("name") or obj.get("headline")
 if not isinstance(name,str) or len(name.strip())<3:return None
 ing=obj.get("recipeIngredient") or []
 if not isinstance(ing,list):ing=[]
 image=obj.get("image")
 if isinstance(image,list):image=image[0] if image else None
 if isinstance(image,dict):image=image.get("url")
 u=obj.get("url") or url
 if isinstance(u,dict):u=u.get("@id") or url
 u=urljoin(url,str(u))
 text=(name+" "+" ".join(map(str,ing))).lower()
 tags=[]
 for tag,words in {
   "kyckling":["kyckling"],"kött":["kött","färs","fläsk","biff","korv"],
   "pasta":["pasta","spaghetti","lasagne","makaron"],"gryta":["gryta","stroganoff","chili"],
   "fredag":["taco","burrito","quesadilla"]
 }.items():
   if any(w in text for w in words):tags.append(tag)
 return {"id":hashlib.sha1(u.encode()).hexdigest()[:20],"name":name.strip(),"source":source,
 "url":u,"minutes":mins(obj.get("totalTime") or obj.get("cookTime") or obj.get("prepTime")),
 "ingredients":[str(x).strip() for x in ing if str(x).strip()][:80],
 "image":image if isinstance(image,str) else None,"tags":tags,"external":True}

def parse_recipe(html,source,url):
 soup=BeautifulSoup(html,"html.parser");out=[]
 for tag in soup.find_all("script",type="application/ld+json"):
  try:data=json.loads(tag.get_text(strip=True))
  except:continue
  stack=data if isinstance(data,list) else [data]
  while stack:
   x=stack.pop()
   if isinstance(x,list):stack.extend(x);continue
   if not isinstance(x,dict):continue
   if isinstance(x.get("@graph"),list):stack.extend(x["@graph"])
   typ=x.get("@type")
   if typ=="Recipe" or (isinstance(typ,list) and "Recipe" in typ):
    r=normalize(x,source,url)
    if r:out.append(r)
 # Some source pages expose the recipe photo only as social metadata.
 og=soup.find("meta",property="og:image") or soup.find("meta",attrs={"name":"twitter:image"})
 fallback_image=og.get("content") if og and og.get("content") else None
 if fallback_image:
  fallback_image=urljoin(url,fallback_image)
  for r in out:
   if not r.get("image"): r["image"]=fallback_image
 return out

def links(html,base,source):
 soup=BeautifulSoup(html,"html.parser");host=urlparse(base).netloc;out=[];seen=set()
 for a in soup.find_all("a",href=True):
  u=urljoin(base,a["href"].split("#")[0]);p=urlparse(u).path.lower()
  if urlparse(u).netloc!=host:continue
  ok=False
  if source=="ICA":ok=p.startswith("/recept/") and len([x for x in p.split("/") if x])>=2 and "/ingredienser/" not in p and "/vardag/" not in p
  elif source=="Arla":ok=p.startswith("/recept/") and "/samling/" not in p
  else:ok=p.count("/")>=1 and not any(x in p for x in ["/mat/typ-av-maltid","/populara-recept"])
  if ok and u not in seen:seen.add(u);out.append(u)
 return out[:500]

existing=json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
byurl={r.get("url"):r for r in existing if r.get("url")}
fallback=[r for r in existing if not r.get("external")]
candidates=[]
for source,pages in PAGES.items():
 for page in pages:
  try:
   html=get(page)
   for r in parse_recipe(html,source,page):
    byurl[r["url"]]=r
   candidates += [(source,u) for u in links(html,page,source)]
  except Exception as e:
   print(source,page,type(e).__name__)

seen=set()
for source,u in candidates[:2500]:
 if u in seen:continue
 seen.add(u)
 try:
  for r in parse_recipe(get(u),source,u):
   byurl[r["url"]]=r
 except Exception:
  pass

external=sorted(byurl.values(),key=lambda r:(r.get("source",""),r.get("name","")))
allrecipes=fallback+external
allrecipes = enrich_missing_images(allrecipes)
OUT.write_text(json.dumps(allrecipes,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Saved {len(allrecipes)} recipes ({len(external)} external)")
