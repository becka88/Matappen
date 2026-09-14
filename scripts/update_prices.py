import json,re,time,datetime
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"prices.json"
REC=ROOT/"recipes.json"
STORE="1003571"
URL=f"https://handlaprivatkund.ica.se/stores/{STORE}/api/webproductpagews/v6/product-pages/search"
S=requests.Session()
S.headers.update({
 "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
 "Accept":"application/json,text/plain,*/*","Accept-Language":"sv-SE,sv;q=0.9",
 "Referer":f"https://handlaprivatkund.ica.se/stores/{STORE}"
})

def clean(x): return re.sub(r"\s+"," ",str(x or "")).strip()
def canon(x): return clean(x).lower().replace("é","e")
def ing(line):
 s=canon(line)
 s=re.sub(r"^\d+(?:[.,/]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*","",s)
 s=re.sub(r"^(kg|g|mg|l|dl|cl|ml|msk|tsk|krm|st|stycken|förp|burk|påse|paket)\s+","",s)
 s=re.sub(r"\([^)]*\)","",s)
 s=re.split(r",| till | efter smak| gärna| valfri",s)[0].strip()
 aliases={"äggula":"ägg","äggulor":"ägg","vitlöksklyfta":"vitlök","vitlöksklyftor":"vitlök","morötter":"morot","lökar":"lök"}
 return aliases.get(s,s)

base=["mjölk","ägg","smör","grädde","crème fraiche","pasta","spaghetti","makaroner","ris","potatis","lök","gul lök","röd lök",
"vitlök","vitlökspulver","vetemjöl","socker","olivolja","rapsolja","köttfärs","nötfärs","blandfärs","kyckling","kycklingfilé",
"lax","torsk","fisk","falukorv","korv","majs","krossade tomater","passerade tomater","kokosmjölk","yoghurt","fil","bröd","ost",
"riven ost","morot","bönor","kikärter","paprika","gurka","tomat","sallad","svamp","champinjoner","bacon","skinka","tortilla",
"tacosås","havregryn","bakpulver","vaniljsocker","kanel","curry","paprikapulver","oregano","timjan","buljong","soja","senap",
"ketchup","majonnäs","matolja","citron","lime","äpple","banan","apelsin","päron"]

raw=json.loads(REC.read_text(encoding="utf-8"))
recipes=raw if isinstance(raw,list) else raw.get("recipes",[])
terms=set(base)
for r in recipes:
 for x in r.get("ingredients",[]) or []:
  q=ing(x)
  if 2<=len(q)<=50 and "vatten" not in q and q not in {"salt","peppar","salt och peppar"}:
   terms.add(q)
terms=list(dict.fromkeys(base+sorted(terms)))[:600]

def payload_data(payload):
 return payload.get("data",payload) if isinstance(payload,dict) else {}

def products(payload):
 payload=payload_data(payload)
 out=[]
 for g in payload.get("productGroups",[]) or []:
  out += g.get("decoratedProducts",[]) or g.get("products",[]) or []
 return out or payload.get("products",[]) or []

def get(d,*ks):
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
 text=clean(get(x,"promotion","promotionText","offerText"))
 pprice=num(get(x,"promotionPrice","promotionalPrice"))
 if promos and isinstance(promos,list):
  p=promos[0]
  if isinstance(p,dict):
   text=text or clean(get(p,"description","name","text","promotionText"))
   pprice=pprice or num(get(p,"price","promotionPrice","promotionalPrice"))
 return text,pprice

rows={}
ok=fail=0
for q in terms:
 try:
  response=None
  for attempt in range(3):
   response=S.get(URL,params={"q":q,"tag":"web","maxPageSize":30},timeout=30)
   if response.status_code==202:
    time.sleep(1.2*(attempt+1));continue
   response.raise_for_status();break
  if response is None or response.status_code==202:
   fail+=1;continue
  ps=products(response.json())
  if ps: ok+=1
  else: continue
  for x in ps[:30]:
   price=num(get(x,"price","currentPrice","salesPrice","displayPrice"))
   name=clean(get(x,"name","productName","displayName"))
   if not price or not name: continue
   promo,promo_price=promotion_info(x)
   pid=clean(get(x,"retailerProductId","productId","id"))
   key=(pid or name+"|"+str(price)).lower()
   if key not in rows:
    rows[key]={"queries":[q],"name":name,"brand":clean(get(x,"brand","brandName")),
      "price":round(price,2),"promotion_price":round(promo_price,2) if promo_price else None,
      "pack":clean(get(x,"packSizeDescription","unitOfMeasure","packageSize","size")),
      "unit_price":clean(get(x,"unitPrice","comparisonPrice")),"promotion":promo,
      "product_id":pid,"available":get(x,"available","inStock")}
   elif q not in rows[key]["queries"]:
    rows[key]["queries"].append(q)
 except Exception:
  fail+=1
 time.sleep(.06)

products_out=list(rows.values())
status="live" if products_out and ok>=20 else "unavailable"
result={"store_id":STORE,"store":"Maxi ICA Stormarknad Växjö",
 "updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "status":status,"queries_ok":ok,"queries_failed":fail,
 "products":products_out if status=="live" else []}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"ICA prices status={status} products={len(products_out)} queries_ok={ok} failed={fail}")
