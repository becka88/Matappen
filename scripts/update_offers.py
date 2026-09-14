import json, re, datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "offers.json"
STORE_ID = "1003571"
STORE_NAME = "Maxi ICA Stormarknad Växjö"
URL = f"https://www.ica.se/erbjudanden/maxi-ica-stormarknad-vaxjo-{STORE_ID}/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Matappen/1.2; +https://github.com/becka88/Matappen)",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.7",
}

def clean(s):
    return re.sub(r"\s+"," ",s or "").strip()

def extract_cards(soup):
    offers=[]; seen=set()
    for marker in soup.find_all(string=re.compile(r"Lägg i inköpslista", re.I)):
        node=marker.parent; card=None
        for parent in node.parents:
            text=clean(parent.get_text(" ", strip=True))
            if 20 <= len(text) <= 1200 and ("Ord.pris" in text or "Jmfpris" in text):
                card=parent
                if parent.find("img", alt=re.compile(r"Illustration av", re.I)):
                    break
        if not card: continue
        text=clean(card.get_text(" ", strip=True))
        img=card.find("img", alt=re.compile(r"Illustration av", re.I))
        name=""
        if img:
            name=re.sub(r"^Illustration av\s*","",clean(img.get("alt","")),flags=re.I)
        if not name:
            name=clean(re.split(r"\b(?:Ord\.pris|Jmfpris)\b",text,1)[0])
            name=re.sub(r"^(?:Veckans erbjudanden|Visar \d+ erbjudanden)\s*","",name)
        prices=re.findall(r"(?:\d+\s+för\s+\d+(?:[,:]\d+)?\s*kr|\d+(?:[,:]\d+)?\s*kr\s*/\s*(?:kg|st|liter))", text, re.I)
        price=clean(prices[-1] if prices else "")
        if not price:
            m=re.search(r"(\d+(?:[,:]\d+)?\s*:-\s*(?:/\s*(?:kg|st))?)",text,re.I)
            price=clean(m.group(1)) if m else ""
        desc=""
        m=re.search(r"(.{0,260}Ord\.pris[^.]*kr)",text,re.I)
        if m: desc=clean(m.group(1))
        if not name or not price: continue
        key=(name+"|"+price).lower()
        if key in seen: continue
        seen.add(key)
        offers.append({"name":name[:160],"price":price[:80],"details":desc[:300],"source":"ICA erbjudanden"})
    return offers

def extract_from_text(soup):
    lines=[clean(x) for x in soup.stripped_strings if clean(x)]
    offers=[]; seen=set()
    for i,line in enumerate(lines):
        if not ("Ord.pris" in line or "Jmfpris" in line): continue
        name=lines[i-1] if i else ""
        if len(name)>160 or len(name)<2: continue
        window=lines[i+1:i+9]; price=""
        for x in window:
            if re.search(r"\d+\s+för\s+\d+(?:[,:]\d+)?\s*kr",x,re.I) or re.search(r"\d+(?:[,:]\d+)?\s*kr\s*/(?:kg|st|liter)",x,re.I):
                price=x; break
        if not price:
            for j,x in enumerate(window):
                if re.fullmatch(r"\d+(?:[,:]\d+)?\s*:-",x):
                    unit=window[j+1] if j+1<len(window) and re.fullmatch(r"/(?:kg|st|liter)",window[j+1]) else ""
                    price=x+unit; break
        if name and price:
            key=(name+"|"+price).lower()
            if key not in seen:
                seen.add(key)
                offers.append({"name":name,"price":price,"details":line[:300],"source":"ICA erbjudanden"})
    return offers

now=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
    r=requests.get(URL,headers=HEADERS,timeout=30)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    page_text=clean(soup.get_text(" ",strip=True))
    count_match=re.search(r"Visar\s+(\d+)\s+(?:stycken|erbjudanden)",page_text,re.I)
    page_count=int(count_match.group(1)) if count_match else None

    offers=extract_cards(soup)
    backup=extract_from_text(soup)
    by={(x["name"]+"|"+x["price"]).lower():x for x in offers}
    for x in backup:
        by.setdefault((x["name"]+"|"+x["price"]).lower(),x)
    offers=list(by.values())

    status="live" if len(offers)>=5 else "unavailable"
    coverage="complete" if status=="live" and page_count and len(offers)>=max(5,int(page_count*0.8)) else ("partial" if status=="live" else "unavailable")
    result={
      "store_id":STORE_ID,"store":STORE_NAME,"updated_at":now,"status":status,
      "source_url":URL,"page_offer_count":page_count,"coverage":coverage,
      "offers":sorted(offers,key=lambda x:x["name"].lower()) if status=="live" else [],
    }
    if status!="live":
        result["note"]=f"ICA-sidan svarade, men bara {len(offers)} erbjudanden kunde verifieras."
except Exception as e:
    result={"store_id":STORE_ID,"store":STORE_NAME,"updated_at":now,"status":"unavailable",
            "source_url":URL,"offers":[],"coverage":"unavailable","note":f"ICA kunde inte verifieras: {type(e).__name__}"}

OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"ICA status={result['status']} offers={len(result['offers'])} page_offers={result.get('page_offer_count')} coverage={result.get('coverage')}")
for x in result["offers"][:15]:
    print(" -",x["name"],"|",x["price"])
