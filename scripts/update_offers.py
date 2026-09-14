import json, re, datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"offers.json"
STORE_ID="1003571"
STORE_NAME="Maxi ICA Stormarknad Växjö"
URL=f"https://www.ica.se/erbjudanden/maxi-ica-stormarknad-vaxjo-{STORE_ID}/"
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36","Accept-Language":"sv-SE,sv;q=0.9"}

def clean(s): return re.sub(r"\s+"," ",str(s or "")).strip()

def price_from_text(text):
    pats=[
      r"\b\d+\s+för\s+\d+(?:[,:]\d+)?\s*kr\b",
      r"\b\d+(?:[,:]\d+)?\s*kr\s*/\s*(?:kg|st|liter|l)\b",
      r"\b\d+(?:[,:]\d+)?\s*:-\s*/?\s*(?:kg|st|liter|l)?\b",
    ]
    hits=[]
    for pat in pats: hits += re.findall(pat,text,re.I)
    return clean(hits[-1]) if hits else ""

def card_for(node):
    best=None
    for parent in node.parents:
        txt=clean(parent.get_text(" ",strip=True))
        if len(txt)>1800: break
        if "Lägg i inköpslista" in txt and ("Ord.pris" in txt or "Jmfpris" in txt):
            best=parent
    return best

def extract_image_cards(soup):
    out=[]; seen=set()
    for img in soup.find_all("img"):
        alt=clean(img.get("alt",""))
        if not re.match(r"^Illustration av\s+",alt,re.I): continue
        name=re.sub(r"^Illustration av\s+","",alt,flags=re.I).strip()
        card=card_for(img)
        if not card: continue
        text=clean(card.get_text(" ",strip=True))
        price=price_from_text(text)
        if not name or not price: continue
        details=""
        m=re.search(r"(.{0,320}(?:Ord\.pris|Jmfpris).{0,180}?kr)",text,re.I)
        if m: details=clean(m.group(1))
        key=(name.lower(),price.lower())
        if key not in seen:
            seen.add(key);out.append({"name":name[:180],"price":price[:80],"details":details[:420],"source":"ICA erbjudanden"})
    return out

def extract_marker_cards(soup):
    out=[];seen=set()
    for marker in soup.find_all(string=re.compile(r"Lägg i inköpslista",re.I)):
        card=card_for(marker.parent)
        if not card: continue
        text=clean(card.get_text(" ",strip=True))
        img=card.find("img",alt=re.compile(r"Illustration av",re.I))
        name=re.sub(r"^Illustration av\s+","",clean(img.get("alt","")),flags=re.I) if img else ""
        if not name:
            # Prefer a heading inside the card.
            h=card.find(["h2","h3","h4"])
            name=clean(h.get_text(" ",strip=True)) if h else ""
        price=price_from_text(text)
        if not name or not price: continue
        details=""
        m=re.search(r"(.{0,320}(?:Ord\.pris|Jmfpris).{0,180}?kr)",text,re.I)
        if m: details=clean(m.group(1))
        key=(name.lower(),price.lower())
        if key not in seen:
            seen.add(key);out.append({"name":name[:180],"price":price[:80],"details":details[:420],"source":"ICA erbjudanden"})
    return out

def merge(*groups):
    d={}
    for rows in groups:
        for x in rows:
            d.setdefault((x["name"].lower(),x["price"].lower()),x)
    return list(d.values())

now=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
    r=requests.get(URL,headers=HEADERS,timeout=40)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    page_text=clean(soup.get_text(" ",strip=True))
    counts=[int(x) for x in re.findall(r"Visar\s+(\d+)\s+(?:stycken|erbjudanden)",page_text,re.I)]
    # The page can show "Komboerbjudande Visar 4" before "Veckans erbjudanden Visar 137".
    page_count=max(counts) if counts else None

    offers=merge(extract_image_cards(soup),extract_marker_cards(soup))
    offers=sorted(offers,key=lambda x:x["name"].lower())

    status="live" if offers else "unavailable"
    coverage="complete" if status=="live" and page_count and len(offers)>=page_count else ("partial" if status=="live" else "unavailable")
    result={"store_id":STORE_ID,"store":STORE_NAME,"updated_at":now,"status":status,
            "source_url":URL,"page_offer_count":page_count,"coverage":coverage,"offers":offers if status=="live" else []}
    if page_count and len(offers)<page_count:
        result["note"]=f"{len(offers)} av {page_count} erbjudanden hämtades."
except Exception as e:
    result={"store_id":STORE_ID,"store":STORE_NAME,"updated_at":now,"status":"unavailable",
            "source_url":URL,"page_offer_count":None,"coverage":"unavailable","offers":[],
            "note":f"{type(e).__name__}"}

OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"ICA offers status={result['status']} parsed={len(result['offers'])} page={result.get('page_offer_count')} coverage={result.get('coverage')}")
