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
    "User-Agent": "Mozilla/5.0 (compatible; Matappen/1.1; +https://github.com/becka88/Matappen)",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.7",
}

FOOD_WORDS = {
 "falukorv","korv","kyckling","kycklingfilé","kött","färs","köttfärs","nötfärs",
 "fläsk","kotlett","bacon","lax","fisk","torsk","räkor","pasta","potatis","morötter",
 "rödbetor","champinjoner","svamp","majs","paprika","tomat","tomater","lök","ost",
 "grädde","crème","fraiche","yoghurt","mjölk","smör","ägg","bröd","tortilla","tacosås",
 "ris","nudlar","bönor","linser","kryddor","kokosmjölk","sås","smörgåsmat","frukt",
 "äpplen","päron","banan","juice","kaffe","skinka"
}
NONFOOD = {"strumpor","trosor","pajform","ugnsform","hörlurar","lego","tändbriketter",
           "megalighter","leksak","schampo","balsam","blöjor","tvättmedel","diskmedel"}

def clean(s):
    return re.sub(r"\s+"," ",s or "").strip()

def foodish(name, desc):
    text=(name+" "+desc).lower()
    if any(x in text for x in NONFOOD): return False
    return any(x in text for x in FOOD_WORDS)

def extract_cards(soup):
    offers=[]
    seen=set()
    # ICA's rendered page exposes each offer as a product block. We anchor on
    # "Lägg i inköpslista", then inspect the nearest compact parent.
    for marker in soup.find_all(string=re.compile(r"Lägg i inköpslista", re.I)):
        node=marker.parent
        card=None
        for parent in node.parents:
            text=clean(parent.get_text(" ", strip=True))
            if 20 <= len(text) <= 1000 and ("Ord.pris" in text or "Jmfpris" in text):
                card=parent
                # Prefer a block containing an image alt identifying the product.
                if parent.find("img", alt=re.compile(r"Illustration av", re.I)):
                    break
        if not card: continue
        text=clean(card.get_text(" ", strip=True))
        img=card.find("img", alt=re.compile(r"Illustration av", re.I))
        name=""
        if img:
            name=re.sub(r"^Illustration av\s*","",clean(img.get("alt","")),flags=re.I)
        if not name:
            # Fallback: text before brand/details/Ord.pris.
            name=clean(re.split(r"\b(?:Ord\.pris|Jmfpris)\b",text,1)[0])
            name=re.sub(r"^(?:Veckans erbjudanden|Visar \d+ erbjudanden)\s*","",name)
        # Price: use the human-readable "... kr/st", "... kr/kg" or "N för X kr".
        prices=re.findall(r"(?:\d+\s+för\s+\d+(?:[,:]\d+)?\s*kr|\d+(?:[,:]\d+)?\s*kr\s*/\s*(?:kg|st|liter))", text, re.I)
        price=clean(prices[-1] if prices else "")
        if not price:
            m=re.search(r"(\d+\s*:-\s*(?:/\s*(?:kg|st))?)",text,re.I)
            price=clean(m.group(1)) if m else ""
        desc=""
        m=re.search(r"(.{0,220}Ord\.pris[^.]*kr)",text,re.I)
        if m: desc=clean(m.group(1))
        if not name or not price or not foodish(name,desc): continue
        key=name.lower()
        if key in seen: continue
        seen.add(key)
        offers.append({"name":name[:140],"price":price[:80],"details":desc[:240],"source":"ICA erbjudanden"})
    return offers

def extract_from_text(soup):
    # Backup parser for ICA's server-rendered text.
    lines=[clean(x) for x in soup.stripped_strings if clean(x)]
    offers=[]; seen=set()
    for i,line in enumerate(lines):
        if not ("Ord.pris" in line or "Jmfpris" in line): continue
        name=lines[i-1] if i else ""
        if len(name)>140 or len(name)<2: continue
        window=lines[i+1:i+8]
        price=""
        for x in window:
            if re.search(r"\d+\s+för\s+\d+(?:[,:]\d+)?\s*kr",x,re.I) or re.search(r"\d+(?:[,:]\d+)?\s*kr\s*/(?:kg|st|liter)",x,re.I):
                price=x; break
        if not price:
            # ICA often splits "79:-" and "/kg" across nodes.
            for j,x in enumerate(window):
                if re.fullmatch(r"\d+\s*:-",x):
                    unit=window[j+1] if j+1<len(window) and re.fullmatch(r"/(?:kg|st|liter)",window[j+1]) else ""
                    price=x+unit; break
        if name and price and foodish(name,line) and name.lower() not in seen:
            seen.add(name.lower())
            offers.append({"name":name,"price":price,"details":line[:240],"source":"ICA erbjudanden"})
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
    if len(offers)<5:
        backup=extract_from_text(soup)
        by={x["name"].lower():x for x in offers}
        for x in backup: by.setdefault(x["name"].lower(),x)
        offers=list(by.values())

    # Never call one or two accidental matches "live".
    status="live" if len(offers)>=5 else "unavailable"
    result={
      "store_id":STORE_ID,"store":STORE_NAME,"updated_at":now,"status":status,
      "source_url":URL,"page_offer_count":page_count,
      "offers":sorted(offers,key=lambda x:x["name"].lower()) if status=="live" else [],
    }
    if status!="live":
        result["note"]=f"ICA-sidan svarade, men bara {len(offers)} mat-erbjudanden kunde verifieras. Veckoplanen använder dem därför inte."
except Exception as e:
    result={"store_id":STORE_ID,"store":STORE_NAME,"updated_at":now,"status":"unavailable",
            "source_url":URL,"offers":[],"note":f"ICA kunde inte verifieras: {type(e).__name__}"}

OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"ICA status={result['status']} food_offers={len(result['offers'])} page_offers={result.get('page_offer_count')}")
for x in result["offers"][:12]:
    print(" -",x["name"],"|",x["price"])
