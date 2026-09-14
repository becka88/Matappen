import json,re,datetime,time
from pathlib import Path
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"offers.json"
STORE_ID="1003571"
STORE_NAME="Maxi ICA Stormarknad Växjö"
OFFERS_URL=f"https://www.ica.se/erbjudanden/maxi-ica-stormarknad-vaxjo-{STORE_ID}/"
API=f"https://handlaprivatkund.ica.se/stores/{STORE_ID}/api/webproductpagews/v6/product-pages/search"
HEAD={"User-Agent":"Mozilla/5.0 (compatible; Matappen/1.0; family meal planner)"}
TERMS=["kyckling","kycklingfilé","köttfärs","nötfärs","blandfärs","falukorv","korv",
       "fläskfilé","fläskytterfilé","kotlett","högrev","bacon","lax","fisk",
       "potatis","morötter","paprika","champinjoner","pasta","ost","grädde","yoghurt"]

def txt(v):
    if v is None:return ""
    if isinstance(v,(int,float)):return str(v)
    if isinstance(v,str):return v.strip()
    return ""

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def first(d,keys):
    for k in keys:
        if k in d and txt(d[k]): return txt(d[k])
    return ""

def looks_promo(d):
    keys=" ".join(map(str,d.keys())).lower()
    return any(x in keys for x in ["promotion","offer","campaign","stammis","discount"]) or \
           any(x in txt(d.get("type")).lower() for x in ["promotion","offer"])

def product_name(d):
    return first(d,["name","productName","displayName","title","articleName","description"])

def price_text(d):
    vals=[]
    for k,v in d.items():
        kl=str(k).lower()
        if any(x in kl for x in ["price","promotion","offer","campaign"]):
            if isinstance(v,(str,int,float)): vals.append(txt(v))
            elif isinstance(v,dict):
                for kk,vv in v.items():
                    if isinstance(vv,(str,int,float)) and any(x in str(kk).lower() for x in ["price","text","label","value"]):
                        vals.append(txt(vv))
    return " · ".join(dict.fromkeys(x for x in vals if x))[:180]

def add(out,name,price,source="ICA"):
    name=re.sub(r"\s+"," ",name or "").strip()
    price=re.sub(r"\s+"," ",price or "").strip()
    if len(name)<3:return
    key=re.sub(r"[^a-zåäö0-9]+"," ",name.lower()).strip()
    if not key:return
    if key not in out or (price and not out[key].get("price")):
        out[key]={"name":name[:120],"price":price[:180],"source":source}

def api_offers(out):
    for term in TERMS:
        try:
            r=requests.get(API,params={"q":term,"tag":"web","maxPageSize":60},headers=HEAD,timeout=20)
            r.raise_for_status()
            data=r.json()
            for d in walk(data):
                name=product_name(d)
                if not name: continue
                promo=""
                for k,v in d.items():
                    if any(x in str(k).lower() for x in ["promotion","offer","campaign"]):
                        if isinstance(v,dict):
                            promo=price_text(v) or first(v,["name","title","description","text","label"])
                        elif isinstance(v,list) and v:
                            promo=" · ".join(price_text(x) or first(x,["name","title","description","text","label"]) for x in v if isinstance(x,dict))
                        elif isinstance(v,str): promo=v
                        if promo: break
                if promo or looks_promo(d):
                    add(out,name,promo or price_text(d),"ICA online")
        except Exception as e:
            print("API",term,type(e).__name__)
        time.sleep(.15)

def page_offers(out):
    # The public store offer page is also checked. We only accept structured blocks
    # that contain both a plausible product name and an offer/price signal.
    try:
        r=requests.get(OFFERS_URL,headers=HEAD,timeout=25);r.raise_for_status()
        html=r.text
        soup=BeautifulSoup(html,"html.parser")
        for s in soup.find_all("script",type="application/ld+json"):
            try:data=json.loads(s.get_text(strip=True))
            except:continue
            for d in walk(data):
                name=product_name(d)
                p=price_text(d)
                if name and (p or looks_promo(d)): add(out,name,p,"ICA erbjudanden")
        # Defensive scan of embedded app JSON.
        for s in soup.find_all("script"):
            raw=s.string or ""
            if len(raw)<100:continue
            if "offer" not in raw.lower() and "promotion" not in raw.lower():continue
            for m in re.finditer(r'"(?:name|productName|displayName)"\s*:\s*"([^"]{3,100})"',raw):
                window=raw[m.start():m.start()+1200]
                pm=re.search(r'"(?:priceText|promotionText|offerText|price)"\s*:\s*"([^"]{1,100})"',window)
                if pm:add(out,m.group(1),pm.group(1),"ICA erbjudanden")
    except Exception as e:
        print("PAGE",type(e).__name__)

old={}
if OUT.exists():
    try: old=json.loads(OUT.read_text(encoding="utf-8"))
    except: old={}
found={}
page_offers(found)
api_offers(found)

today=datetime.datetime.now(datetime.timezone.utc).isoformat()
if found:
    result={"store_id":STORE_ID,"store":STORE_NAME,"updated_at":today,"status":"live",
            "source_url":OFFERS_URL,"offers":sorted(found.values(),key=lambda x:x["name"].lower())}
else:
    # Never pretend stale data is current. Preserve last successful rows only as stale reference.
    prev=old.get("offers",[]) if isinstance(old,dict) else []
    result={"store_id":STORE_ID,"store":STORE_NAME,"updated_at":today,"status":"unavailable",
            "source_url":OFFERS_URL,"offers":prev,"note":"ICA kunde inte verifieras vid senaste körningen; gamla träffar används inte för veckoplanering."}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"ICA status={result['status']} offers={len(result['offers'])}")
