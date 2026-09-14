import json,re,time,datetime,concurrent.futures
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"prices.json"
REC=ROOT/"recipes.json"
STORE="1003571"
URL=f"https://handlaprivatkund.ica.se/stores/{STORE}/api/webproductpagews/v6/product-pages/search"
HEADERS={
 "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
 "Accept":"application/json,text/plain,*/*",
 "Accept-Language":"sv-SE,sv;q=0.9",
 "Referer":f"https://handlaprivatkund.ica.se/stores/{STORE}"
}

REQUEST_TIMEOUT=8
MAX_TERMS=90
MAX_WORKERS=10
MAX_RUNTIME_SECONDS=75
MAX_PRODUCTS_PER_TERM=18

def clean(x): return re.sub(r"\s+"," ",str(x or "")).strip()
def canon(x): return clean(x).lower().replace("é","e")

def ing(line):
 s=canon(line)
 s=re.sub(r"^\d+(?:[.,/]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*","",s)
 s=re.sub(r"^(kg|g|mg|l|dl|cl|ml|msk|tsk|krm|st|stycken|förp|burk|påse|paket)\s+","",s)
 s=re.sub(r"\([^)]*\)","",s)
 s=re.split(r",| till | efter smak| gärna| valfri",s)[0].strip()
 aliases={
   "äggula":"ägg","äggulor":"ägg",
   "vitlöksklyfta":"vitlök","vitlöksklyftor":"vitlök",
   "morötter":"morot","lökar":"lök"
 }
 return aliases.get(s,s)

base=[
 "mjölk","ägg","smör","grädde","crème fraiche","pasta","spaghetti","makaroner","ris","potatis",
 "lök","gul lök","röd lök","vitlök","vitlökspulver","vetemjöl","socker","olivolja","rapsolja",
 "köttfärs","nötfärs","blandfärs","kyckling","kycklingfilé","lax","torsk","falukorv","korv",
 "majs","krossade tomater","passerade tomater","kokosmjölk","yoghurt","fil","bröd","ost","riven ost",
 "morot","bönor","kikärter","paprika","gurka","tomat","sallad","svamp","champinjoner","bacon","skinka",
 "tortilla","tacosås","havregryn","bakpulver","vaniljsocker","kanel","curry","paprikapulver","oregano",
 "timjan","buljong","soja","senap","ketchup","majonnäs","citron","lime","äpple","banan"
]

def payload_data(payload):
 return payload.get("data",payload) if isinstance(payload,dict) else {}

def products(payload):
 payload=payload_data(payload)
 out=[]
 for g in payload.get("productGroups",[]) or []:
  out += g.get("decoratedProducts",[]) or g.get("products",[]) or []
 return out or payload.get("products",[]) or []

def getv(d,*ks):
 if not isinstance(d,dict): return None
 for k in ks:
  if d.get(k) not in (None,""): return d[k]

def num(v):
 if isinstance(v,(int,float)): return float(v)
 if isinstance(v,dict):
  for k in ("amount","value","price"):
   if k in v:
    n=num(v[k])
    if n is not None:return n
 m=re.search(r"\d+(?:[.,]\d+)?",str(v or ""))
 return float(m.group().replace(",",".")) if m else None

def promotion_info(x):
 promos=x.get("promotions") or []
 text=clean(getv(x,"promotion","promotionText","offerText"))
 pprice=num(getv(x,"promotionPrice","promotionalPrice"))
 if promos and isinstance(promos,list):
  p=promos[0]
  if isinstance(p,dict):
   text=text or clean(getv(p,"description","name","text","promotionText"))
   pprice=pprice or num(getv(p,"price","promotionPrice","promotionalPrice"))
 return text,pprice

def fetch_term(q):
 try:
  s=requests.Session()
  s.headers.update(HEADERS)
  r=s.get(URL,params={"q":q,"tag":"web","maxPageSize":MAX_PRODUCTS_PER_TERM},timeout=REQUEST_TIMEOUT)
  r.raise_for_status()
  ps=products(r.json())[:MAX_PRODUCTS_PER_TERM]
  rows=[]
  for x in ps:
   price=num(getv(x,"price","currentPrice","salesPrice","displayPrice"))
   name=clean(getv(x,"name","productName","displayName"))
   if not price or not name: continue
   promo,promo_price=promotion_info(x)
   pid=clean(getv(x,"retailerProductId","productId","id"))
   rows.append({
     "query":q,"name":name,"brand":clean(getv(x,"brand","brandName")),
     "price":round(price,2),
     "promotion_price":round(promo_price,2) if promo_price else None,
     "pack":clean(getv(x,"packSizeDescription","unitOfMeasure","packageSize","size")),
     "unit_price":clean(getv(x,"unitPrice","comparisonPrice")),
     "promotion":promo,"product_id":pid,
     "available":getv(x,"available","inStock")
   })
  return q,rows,None
 except Exception as e:
  return q,[],type(e).__name__

# Build a compact search list from real recipe ingredients + staples.
terms=list(base)
try:
 raw=json.loads(REC.read_text(encoding="utf-8"))
 recipes=raw if isinstance(raw,list) else raw.get("recipes",[])
 for r in recipes:
  for x in r.get("ingredients",[]) or []:
   q=ing(x)
   if 2<=len(q)<=45 and "vatten" not in q and q not in {"salt","peppar","salt och peppar"}:
    terms.append(q)
except Exception:
 pass

# Unique, preserving order; hard cap.
terms=list(dict.fromkeys(terms))[:MAX_TERMS]

started=time.time()
rows={}
ok=fail=0

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
 futures={ex.submit(fetch_term,q):q for q in terms}
 for fut in concurrent.futures.as_completed(futures):
  if time.time()-started > MAX_RUNTIME_SECONDS:
   break
  q,items,err=fut.result()
  if err:
   fail+=1
   continue
  ok+=1
  for x in items:
   key=(x["product_id"] or (x["name"]+"|"+str(x["price"]))).lower()
   if key not in rows:
    x["queries"]=[q]
    x.pop("query",None)
    rows[key]=x
   elif q not in rows[key]["queries"]:
    rows[key]["queries"].append(q)

products_out=list(rows.values())
status="live" if products_out and ok>=10 else "unavailable"

result={
 "store_id":STORE,
 "store":"Maxi ICA Stormarknad Växjö",
 "updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "status":status,
 "queries_ok":ok,
 "queries_failed":fail,
 "products":products_out if status=="live" else []
}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
elapsed=round(time.time()-started,1)
print(f"ICA prices status={status} products={len(products_out)} queries_ok={ok} failed={fail} elapsed={elapsed}s")
