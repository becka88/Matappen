import json,re,time,datetime
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"prices.json"; REC=ROOT/"recipes.json"
STORE="1003571"; URL=f"https://handlaprivatkund.ica.se/stores/{STORE}/api/webproductpagews/v6/product-pages/search"
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; Matappen/1.3)","Accept":"application/json","Accept-Language":"sv-SE,sv;q=0.9"})
def clean(x):return re.sub(r"\s+"," ",str(x or "")).strip()
def ing(line):
 s=clean(line).lower();s=re.sub(r"^\d+(?:[.,/]\d+)?\s*","",s);s=re.sub(r"^(kg|g|l|dl|cl|ml|msk|tsk|krm|st|förp|burk|påse)\s+","",s);s=re.sub(r"\([^)]*\)","",s);s=re.split(r",| till | efter smak",s)[0].strip()
 return {"äggula":"ägg","äggulor":"ägg","vitlöksklyfta":"vitlök","vitlöksklyftor":"vitlök"}.get(s,s)
base=["mjölk","ägg","smör","grädde","creme fraiche","pasta","ris","potatis","gul lök","vitlök","vitlökspulver","vetemjöl","socker","olivolja","rapsolja","köttfärs","kyckling","lax","torsk","falukorv","majs","krossade tomater","kokosmjölk","yoghurt","bröd","ost","morötter","bönor","kikärter"]
raw=json.loads(REC.read_text(encoding="utf-8")); recipes=raw if isinstance(raw,list) else raw.get("recipes",[])
terms=set(base)
for r in recipes:
 for x in r.get("ingredients",[]) or []:
  q=ing(x)
  if 2<=len(q)<=45 and "vatten" not in q:terms.add(q)
terms=list(dict.fromkeys(base+sorted(terms)))[:220]
def products(payload):
 out=[]
 for g in payload.get("productGroups",[]) or []:out+=g.get("decoratedProducts",[]) or g.get("products",[]) or []
 return out or payload.get("products",[]) or []
def get(d,*ks):
 for k in ks:
  if d.get(k) not in (None,""):return d[k]
def num(v):
 if isinstance(v,(int,float)):return float(v)
 if isinstance(v,dict):
  for k in ("value","amount","price"):
   if k in v:return num(v[k])
 m=re.search(r"\d+(?:[.,]\d+)?",str(v or ""));return float(m.group().replace(",",".")) if m else None
rows=[];seen=set();ok=fail=0
for q in terms:
 try:
  r=S.get(URL,params={"q":q,"tag":"web","maxPageSize":12},timeout=25)
  if r.status_code==202:time.sleep(2);r=S.get(URL,params={"q":q,"tag":"web","maxPageSize":12},timeout=25)
  r.raise_for_status(); ps=products(r.json());ok+=bool(ps)
  for x in ps[:12]:
   price=num(get(x,"price","currentPrice","salesPrice","displayPrice"))
   name=clean(get(x,"name","productName","displayName"))
   if not price or not name:continue
   promos=x.get("promotions") or []; promo=clean(get(x,"promotion","promotionText","offerText"))
   if not promo and promos and isinstance(promos[0],dict):promo=clean(get(promos[0],"name","text","description"))
   row={"query":q,"name":name,"brand":clean(get(x,"brand","brandName")),"price":round(price,2),"pack":clean(get(x,"packSizeDescription","unitOfMeasure","packageSize","size")),"unit_price":clean(get(x,"unitPrice","comparisonPrice")),"promotion":promo,"product_id":clean(get(x,"productId","id","retailerProductId"))}
   key=(row["product_id"] or name+"|"+str(price)).lower()
   if key not in seen:seen.add(key);rows.append(row)
 except Exception:fail+=1
 time.sleep(.08)
status="live" if rows and ok>=10 else "unavailable"
OUT.write_text(json.dumps({"store_id":STORE,"store":"Maxi ICA Stormarknad Växjö","updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"status":status,"queries_ok":ok,"queries_failed":fail,"products":rows if status=="live" else []},ensure_ascii=False,indent=2),encoding="utf-8")
print(f"ICA online prices status={status} products={len(rows)} queries_ok={ok} failed={fail}")
