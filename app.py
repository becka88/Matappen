
import streamlit as st
import hmac
from pathlib import Path
from datetime import date, timedelta
from collections import Counter, defaultdict
import json, csv, io, re
import requests
from bs4 import BeautifulSoup


st.set_page_config(page_title="Matappen", page_icon="🍽️", layout="wide")

# ---------- Private access ----------
def require_login():
    """Stop the app before any family data or ICA UI is shown unless authenticated."""
    if st.session_state.get("authenticated", False):
        return

    try:
        expected_password = str(st.secrets["APP_PASSWORD"])
    except Exception:
        st.title("🔐 Matappen")
        st.error("Appen är inte färdigkonfigurerad ännu.")
        st.info('Ägaren behöver lägga till `APP_PASSWORD = "ditt-lösenord"` under Streamlit → Advanced settings → Secrets.')
        st.stop()

    st.title("🔐 Matappen")
    st.write("Privat familjeapp")
    with st.form("login_form", clear_on_submit=False):
        password = st.text_input("Lösenord", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Logga in", use_container_width=True)

    if submitted:
        if hmac.compare_digest(password, expected_password):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Fel lösenord.")
    st.stop()

require_login()

# Small logout control in the sidebar after successful login.
with st.sidebar:
    st.caption("🔒 Privat Matapp")
    if st.button("Logga ut", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()



# ---------- ICA live data ----------
STORE_ID = "1003571"
STORE_NAME = "Maxi ICA Stormarknad Växjö"
OFFER_URL = f"https://www.ica.se/erbjudanden/maxi-ica-stormarknad-vaxjo-{STORE_ID}/"
ONLINE_SEARCH_URL = f"https://handlaprivatkund.ica.se/stores/{STORE_ID}/api/webproductpagews/v6/product-pages/search"
MEAT_TERMS = ["falukorv","köttfärs","nötfärs","blandfärs","kyckling","fläskytterfilé",
              "fläskfilé","högrev","kotlett","bacon","korv"]
EXTRA_TERMS = ["yoghurt","mjölk","ost","potatis","morötter"]

def _week_bounds(today=None):
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

def _clean(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()

def _deep_values(obj, key_words):
    out=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            if any(w in str(k).lower() for w in key_words):
                if isinstance(v, (str,int,float)) and _clean(v):
                    out.append(_clean(v))
            out.extend(_deep_values(v, key_words))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_deep_values(v, key_words))
    return out

def _first_value(obj, keys, default=""):
    if not isinstance(obj, dict):
        return default
    low={str(k).lower():v for k,v in obj.items()}
    for key in keys:
        if key.lower() in low and isinstance(low[key.lower()], (str,int,float)):
            return _clean(low[key.lower()])
    # recursive fallback
    vals=_deep_values(obj, [k.lower() for k in keys])
    return vals[0] if vals else default

def _promotion_text(product):
    vals=_deep_values(product, ["promotion","campaign","offer","deal","discount"])
    # Keep useful values, remove booleans and URLs/noise
    clean=[]
    for v in vals:
        if v.lower() in ["true","false","none","null"]: 
            continue
        if v.startswith("http"):
            continue
        if v not in clean:
            clean.append(v)
    return " · ".join(clean[:5])

def _extract_products(payload):
    products=[]
    if isinstance(payload, dict):
        for k,v in payload.items():
            if str(k).lower() in ["decoratedproducts","products","items"] and isinstance(v,list):
                products.extend([x for x in v if isinstance(x,dict)])
            else:
                products.extend(_extract_products(v))
    elif isinstance(payload, list):
        for v in payload:
            products.extend(_extract_products(v))
    return products

def fetch_online_promotions(terms=None):
    """Targeted live check against ICA's store-scoped online product endpoint."""
    terms = terms or (MEAT_TERMS + EXTRA_TERMS)
    headers={"User-Agent":"Mozilla/5.0 (compatible; Matappen/1.0)","Accept":"application/json"}
    found={}
    errors=[]
    for term in terms:
        try:
            r=requests.get(
                ONLINE_SEARCH_URL,
                params={"q":term,"tag":"web","maxPageSize":60},
                headers=headers, timeout=12
            )
            r.raise_for_status()
            payload=r.json()
            for p in _extract_products(payload):
                promo=_promotion_text(p)
                if not promo:
                    continue
                name=_first_value(p,["name","productName","displayName","title"],term)
                brand=_first_value(p,["brand","brandName"],"")
                price=_first_value(p,["price","currentPrice","sellingPrice"],"")
                unit=_first_value(p,["unitPrice","comparativePrice","pricePerUnit"],"")
                sku=_first_value(p,["sku","id","productId","gtin"],name)
                key=sku or name
                found[key]={
                    "name":name, "brand":brand, "price":price, "unit_price":unit,
                    "offer":promo, "source":"ICA online", "verified":True,
                    "query":term
                }
        except Exception as e:
            errors.append(f"{term}: {type(e).__name__}")
    return list(found.values()), errors

def fetch_offer_page():
    """Read ICA's official store offer page. This may expose only part of the cards server-side."""
    headers={"User-Agent":"Mozilla/5.0 (compatible; Matappen/1.0)"}
    r=requests.get(OFFER_URL,headers=headers,timeout=15)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    text="\n".join(soup.stripped_strings)
    if STORE_NAME.lower() not in text.lower():
        raise RuntimeError("Fel ICA-butik i svaret")
    m=re.search(r"Alla\s*\((\d+)\)", text)
    stated_count=int(m.group(1)) if m else None

    # Parse a conservative subset of visible offer cards from text.
    lines=[_clean(x) for x in soup.stripped_strings if _clean(x)]
    offers=[]
    price_re=re.compile(r"^(?:\d+\s+för\s+)?\d+(?::\d+)?\s*kr(?:/kg|/st)?$",re.I)
    for i,line in enumerate(lines):
        if price_re.match(line):
            # Search backwards for plausible product title and details.
            name=""
            details=""
            for j in range(i-1,max(-1,i-8),-1):
                cand=lines[j]
                if cand in ["Lägg i inköpslista","Veckans erbjudanden","Filter för erbjudanden"]:
                    continue
                if "Ord.pris" in cand or "Jmfpris" in cand:
                    details=cand
                    continue
                if len(cand)<80 and not re.search(r"\d+\s*(g|kg|ml|liter)",cand,re.I):
                    name=cand
                    break
            if name:
                offers.append({
                    "name":name,"brand":"","price":"","unit_price":"",
                    "offer":line,"details":details,"source":"ICA erbjudandesida",
                    "verified":True
                })
    # dedupe
    unique={}
    for o in offers:
        unique[(o["name"],o["offer"])]=o
    return list(unique.values()), stated_count

def load_snapshot():
    p=Path(__file__).with_name("current_offers_snapshot.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"offers":[],"captured_at":None}

@st.cache_data(ttl=21600, show_spinner=False)
def get_current_ica_offers():
    page_offers=[]; online_offers=[]; page_count=None; errors=[]
    try:
        page_offers,page_count=fetch_offer_page()
    except Exception as e:
        errors.append("Erbjudandesidan: "+type(e).__name__)
    try:
        online_offers,online_errors=fetch_online_promotions()
        errors.extend(online_errors[:3])
    except Exception as e:
        errors.append("Onlinebutiken: "+type(e).__name__)

    merged={}
    for o in page_offers+online_offers:
        key=(o.get("name","").lower(),o.get("offer","").lower())
        merged[key]=o

    snapshot=load_snapshot()
    if merged:
        status="Live"
        offers=list(merged.values())
    elif snapshot.get("offers"):
        status="Sparad reservkopia"
        offers=snapshot["offers"]
    else:
        status="Ingen data"
        offers=[]
    mon,sun=_week_bounds()
    return {
        "store":STORE_NAME,"store_id":STORE_ID,"status":status,
        "offers":offers,"stated_count":page_count,"errors":errors,
        "checked_at":date.today().isoformat(),
        "week":f"{mon.isoformat()}–{sun.isoformat()}",
        "url":OFFER_URL
    }

def offer_for_recipe(recipe, offers):
    hay=" ".join([recipe["name"]]+list(recipe["ings"].keys())).lower()
    best=None
    for o in offers:
        name=(o.get("name","")+" "+o.get("query","")).lower()
        tokens=[t for t in MEAT_TERMS if t in name]
        if any(t in hay for t in tokens):
            best=o
            break
    return best

# ---------- Data ----------
RECIPES = [
 {"name":"Korv stroganoff","cat":"Middag","tags":["barnvänlig","matlåda"],"mins":25,"freeze":4,"lunch":5,"base":4,
  "ings":{"Falukorv":"800 g","Ris":"500 g","Gul lök":"2 st","Grädde":"3 dl","Tomatpuré":"1 st","Morötter":"500 g"},
  "steps":["Hacka och stek lök och falukorv.","Rör ner tomatpuré och grädde.","Låt sjuda 10 minuter och servera med ris och morötter."]},
 {"name":"Spaghetti och köttfärssås","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":35,"freeze":5,"lunch":5,"base":6,
  "ings":{"Nötfärs":"900 g","Spaghetti":"700 g","Krossade tomater":"2 st","Gul lök":"2 st","Morötter":"500 g"},
  "steps":["Bryn färs och lök.","Tillsätt tomat och rivna morötter.","Låt puttra minst 15 minuter och koka spaghetti."]},
 {"name":"Krämig kycklingpasta","cat":"Middag","tags":["barnvänlig","matlåda"],"mins":30,"freeze":3,"lunch":4,"base":6,
  "ings":{"Kyckling":"900 g","Pasta":"600 g","Crème fraiche":"4 dl","Broccoli":"1 st","Parmesan":"100 g"},
  "steps":["Stek kycklingen.","Koka pasta och broccoli.","Blanda med crème fraiche och parmesan."]},
 {"name":"Fläskytterfilé med potatisgratäng","cat":"Middag","tags":["helg","vuxen"],"mins":55,"freeze":3,"lunch":4,"base":4,
  "ings":{"Fläskytterfilé":"900 g","Potatis":"1.5 kg","Grädde":"5 dl","Vitlök":"1 st","Sallad":"1 st"},
  "steps":["Skiva potatis och lägg med grädde och vitlök i form.","Baka gratängen tills mjuk.","Bryn och tillaga köttet till önskad temperatur."]},
 {"name":"Het högrevsgryta","cat":"Middag","tags":["vuxen","matlåda","frys","långkok"],"mins":150,"freeze":5,"lunch":5,"base":6,
  "ings":{"Högrev":"1.2 kg","Gul lök":"2 st","Morötter":"600 g","Chili":"2 st","Ris":"600 g"},
  "steps":["Bryn högreven i omgångar.","Fräs lök, morot och chili.","Låt köttet sjuda mört 2–3 timmar och servera med ris."]},
 {"name":"Kycklingtacos","cat":"Middag","tags":["barnvänlig","fredag"],"mins":25,"freeze":2,"lunch":3,"base":4,
  "ings":{"Kyckling":"900 g","Tortilla":"2 pkt","Ost":"200 g","Salsa":"1 st","Sallad":"1 st"},
  "steps":["Strimla och stek kycklingen med kryddor.","Förbered tillbehören.","Servera allt separat så alla bygger sin egen taco."]},
 {"name":"Pizzabullar","cat":"Mellis","tags":["frys","batch","barnvänlig"],"mins":50,"freeze":5,"lunch":3,"base":20,
  "ings":{"Vetemjöl":"8 dl","Jäst":"25 g","Mjölk":"3 dl","Skinka":"250 g","Ost":"250 g","Tomatsås":"2 dl"},
  "steps":["Gör en mjuk deg och låt jäsa.","Kavla ut, bred på tomatsås, skinka och ost.","Rulla, skär i bitar och grädda. Frys styckvis när de svalnat."]},
 {"name":"Köttfärspiroger","cat":"Mellis","tags":["frys","batch","protein"],"mins":70,"freeze":5,"lunch":5,"base":16,
  "ings":{"Nötfärs":"600 g","Gul lök":"1 st","Pirogdeg":"2 pkt","Ost":"150 g","Ägg":"1 st"},
  "steps":["Stek färs och lök och låt svalna.","Fyll degbitar med färs och ost och vik ihop.","Pensla med ägg, grädda och frys efter avsvalning."]},
 {"name":"Bananpannkakor","cat":"Mellis","tags":["frys","snabb","barnvänlig"],"mins":20,"freeze":4,"lunch":2,"base":16,
  "ings":{"Banan":"4 st","Ägg":"6 st","Havregryn":"4 dl","Kanel":"1 tsk"},
  "steps":["Mixa alla ingredienser.","Stek små pannkakor.","Låt svalna med bakplåtspapper mellan och frys."]},
 {"name":"Ost- och skinkhorn","cat":"Mellis","tags":["frys","batch"],"mins":45,"freeze":5,"lunch":3,"base":16,
  "ings":{"Deg":"2 pkt","Skinka":"250 g","Ost":"250 g","Ägg":"1 st"},
  "steps":["Dela degen i trianglar.","Lägg på skinka och ost och rulla ihop.","Pensla med ägg, grädda och frys."]},
]

DAYS=["Måndag","Tisdag","Onsdag","Torsdag","Fredag","Lördag","Söndag"]

def kids_here(day_index, kids_arrive_thursday):
    # One weekly view split at Thursday; user chooses which side of the handover has kids.
    return day_index >= 3 if kids_arrive_thursday else day_index < 3

def portions(kids, lunchboxes):
    eaters=4 if kids else 2
    return eaters+lunchboxes

def choose_recipe(i,kids,taco,used,offers=None):
    options=[r for r in RECIPES if r["cat"]=="Middag"]
    if taco and i==4:
        return next(r for r in options if "taco" in r["name"].lower())
    ranked=[]
    for r in options:
        score=0
        if kids and "barnvänlig" in r["tags"]: score+=8
        if not kids and "vuxen" in r["tags"]: score+=8
        if r["name"] in used: score-=20
        if i<4 and r["mins"]<=40: score+=5
        if r["lunch"]>=4: score+=3
        if offer_for_recipe(r, offers or []): score+=12
        ranked.append((score,r))
    return sorted(ranked,key=lambda x:x[0],reverse=True)[0][1]

# ---------- State ----------
defaults={
 "kids_arrive":True,"lunchboxes":2,"taco":True,"budget":1200,
 "snabblista":[],
 "common_items":["Mjölk","Yoghurt","Bröd","Ägg","Diskmedel","Toapapper"],
 "freezer_levels":{"Pizzabullar":"Okej","Köttfärspiroger":"Okej","Bananpannkakor":"Fullt"},
 "freezer_exact":{"Middagsportioner":2,"Kycklingpaket":1,"Köttfärspaket":0},
 "ratings":{},"pantry":[],"offers":["Falukorv 800 g – 2 för 65 kr (verifierat exempel)"]
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

# ---------- UI ----------
st.title("🍽️ Matappen")
st.caption("Familjens veckomat, matlådor, mellis, recept, frys och inköpslista")

tabs=st.tabs(["🏠 Hem","📅 Veckoplan","🔥 ICA erbjudanden","🍎 Mellis","📖 Recept","🛒 Inköpslista","➕ Snabblista","❄️ Frys","⚙️ Familjen"])

with tabs[8]:
    st.header("Familjen")
    st.session_state.kids_arrive=st.radio(
        "Vad händer vid torsdagsskiftet?",
        ["Barnen kommer på torsdag","Barnen åker på torsdag"],
        index=0 if st.session_state.kids_arrive else 1
    )=="Barnen kommer på torsdag"
    st.session_state.lunchboxes=st.slider("Planerade matlådor efter en vanlig middag",0,4,st.session_state.lunchboxes)
    st.session_state.taco=st.checkbox("Försök ha tacos på fredag när barnen är hemma",st.session_state.taco)
    st.session_state.budget=st.number_input("Målbudget/vecka",500,3000,st.session_state.budget,100)
    st.info("När barnen inte är hemma prioriterar appen friare/vuxnare mat. Portionerna inkluderar ändå valda matlådor.")

# Live ICA data (cached for six hours; refreshable in the ICA tab)
ica_data=get_current_ica_offers()
live_offers=ica_data.get("offers",[])

# Build plan dynamically
used=set(); plan=[]
for i,d in enumerate(DAYS):
    kh=kids_here(i,st.session_state.kids_arrive)
    r=choose_recipe(i,kh,st.session_state.taco and kh,used,live_offers)
    used.add(r["name"])
    plan.append({"day":d,"kids":kh,"recipe":r,"portions":portions(kh,st.session_state.lunchboxes),"offer":offer_for_recipe(r,live_offers)})

with tabs[0]:
    today_idx=date.today().weekday()
    idx=min(today_idx,6)
    p=plan[idx]
    st.subheader("Idag")
    c1,c2,c3=st.columns(3)
    c1.metric("Hemma", "4 personer" if p["kids"] else "2 vuxna")
    c2.metric("Middag",p["recipe"]["name"])
    c3.metric("Lagas",f"{p['portions']} portioner")
    if p.get("offer"):
        st.success(f"🔥 Matchar aktuellt ICA-erbjudande: {p['offer'].get('name')} — {p['offer'].get('offer')}")
    st.write(f"**{p['recipe']['mins']} min** · matlådebetyg {p['recipe']['lunch']}/5 · frysbetyg {p['recipe']['freeze']}/5")
    st.divider()
    st.subheader("Snabbkoll")
    level_score={"Fullt":3,"Okej":2,"Börjar ta slut":1,"Slut":0}
    mellis_status=min(st.session_state.freezer_levels.values(), key=lambda x: level_score.get(x,0)) if st.session_state.freezer_levels else "Okej"
    a,b,c=st.columns(3)
    a.metric("Mellisstatus",mellis_status)
    b.metric("Färdiga middagsportioner",st.session_state.freezer_exact.get("Middagsportioner",0))
    bval=sum(x["portions"] for x in plan)
    c.metric("Planerade portioner",bval)
    if any(v in ["Börjar ta slut","Slut"] for v in st.session_state.freezer_levels.values()):
        st.warning("Något mellis börjar ta slut. Bra läge att fylla frysen.")
    st.success("💡 Söndagstips: kontrollera frysen innan nästa veckoplan görs så appen kan använda det ni redan har.")

with tabs[1]:
    st.header("Veckoplan")
    for p in plan:
        icon="👨‍👩‍👧‍👦" if p["kids"] else "🥂"
        with st.expander(f"{p['day']} {icon} — {p['recipe']['name']} · {p['portions']} port"):
            st.write(f"{'Barnen hemma' if p['kids'] else 'Vuxenkväll'} · {p['recipe']['mins']} min")
            st.write(f"Plan: {4 if p['kids'] else 2} till middag + {st.session_state.lunchboxes} matlådor.")
            if p.get("offer"):
                st.success(f"ICA just nu: {p['offer'].get('name')} — {p['offer'].get('offer')}")
            st.write("**Ingredienser:** "+", ".join(p["recipe"]["ings"].keys()))
            st.write("**Gör så här:**")
            for n,s in enumerate(p["recipe"]["steps"],1): st.write(f"{n}. {s}")
            st.caption(f"Matlåda {p['recipe']['lunch']}/5 · Frys {p['recipe']['freeze']}/5")

with tabs[2]:
    st.header("ICA Maxi Växjö – aktuella erbjudanden")
    st.caption("Appen kontrollerar rätt butik automatiskt och cachelagrar resultatet i högst 6 timmar.")

    a,b,c=st.columns(3)
    a.metric("Butik",ica_data["store"])
    b.metric("Status",ica_data["status"])
    c.metric("Vecka",ica_data["week"])
    if ica_data.get("stated_count"):
        st.write(f"ICA:s erbjudandesida anger **{ica_data['stated_count']} erbjudanden** just nu.")
    st.write(f"Appen hittade **{len(live_offers)} verifierade kampanjposter** via sina livekällor.")

    if st.button("🔄 Hämta ICA igen nu"):
        get_current_ica_offers.clear()
        st.rerun()

    if ica_data.get("errors"):
        st.warning("ICA-data kunde inte läsas fullt ut från alla källor. Appen använder det som kunde verifieras och hittar inte på priser.")

    meat=[]
    other=[]
    for o in live_offers:
        txt=(o.get("name","")+" "+o.get("query","")).lower()
        (meat if any(t in txt for t in MEAT_TERMS) else other).append(o)

    st.subheader("Kött, kyckling & chark")
    if meat:
        for o in meat[:30]:
            title=f"**{o.get('name','Vara')}**"
            if o.get("brand"): title+=f" · {o['brand']}"
            st.write(title)
            st.write(f"🔥 {o.get('offer','Erbjudande')}  ·  Källa: {o.get('source')}")
            if o.get("unit_price"): st.caption(f"Jämförpris: {o.get('unit_price')}")
    else:
        st.info("Inga kötterbjudanden kunde verifieras i den data ICA exponerade just nu.")

    with st.expander("Övriga verifierade erbjudanden"):
        for o in other[:40]:
            st.write(f"**{o.get('name','Vara')}** — {o.get('offer','Erbjudande')} · {o.get('source')}")

    st.caption("Viktigt: ICA:s publika erbjudandesida kan servera färre produktkort än det totala antalet. Därför kombinerar Matappen erbjudandesidan med butikens publika onlineproduktdata. Endast det som faktiskt går att läsa markeras som verifierat.")

with tabs[3]:
    st.header("Mellis – fyll frysen")
    st.write("Batchrecept som barnen kan ta fram snabbt.")
    mellis=[r for r in RECIPES if r["cat"]=="Mellis"]
    for r in mellis:
        with st.expander(f"{r['name']} · ca {r['base']} st · ❄️ {r['freeze']}/5"):
            st.write(f"⏱️ {r['mins']} min")
            st.write("**Ingredienser:**")
            for k,v in r["ings"].items(): st.write(f"• {k}: {v}")
            st.write("**Gör så här:**")
            for i,s in enumerate(r["steps"],1): st.write(f"{i}. {s}")
            st.info("Frys i portionspåsar eller styckvis. Märk med namn och datum.")
    priority={"Slut":0,"Börjar ta slut":1,"Okej":2,"Fullt":3}
    low=sorted(st.session_state.freezer_levels.items(), key=lambda x:priority.get(x[1],9))
    if low and low[0][1] in ["Slut","Börjar ta slut"]:
        st.success(f"Förslag just nu: gör en sats **{low[0][0]}** eftersom nivån är **{low[0][1]}**.")

with tabs[4]:
    st.header("Receptsamling")
    q=st.text_input("Sök recept eller ingrediens")
    cat=st.radio("Visa",["Alla","Middag","Mellis"],horizontal=True)
    filtered=[]
    for r in RECIPES:
        if cat!="Alla" and r["cat"]!=cat: continue
        hay=(r["name"]+" "+" ".join(r["ings"].keys())+" "+" ".join(r["tags"])).lower()
        if q.lower() not in hay: continue
        filtered.append(r)
    for r in filtered:
        with st.expander(f"{'🍽️' if r['cat']=='Middag' else '🍎'} {r['name']}"):
            x,y,z=st.columns(3)
            x.metric("Tid",f"{r['mins']} min")
            y.metric("Matlåda",f"{r['lunch']}/5")
            z.metric("Frys",f"{r['freeze']}/5")
            st.write("**Ingredienser**")
            for k,v in r["ings"].items(): st.write(f"• {k}: {v}")
            st.write("**Gör så här**")
            for i,s in enumerate(r["steps"],1): st.write(f"{i}. {s}")
            rating=st.select_slider("Familjens betyg",["👎","😐","👍","❤️"],value=st.session_state.ratings.get(r["name"],"👍"),key="rate_"+r["name"])
            st.session_state.ratings[r["name"]]=rating

with tabs[7]:
    st.header("Frysen")
    st.caption("Mellis hålls enkelt på ungefärlig nivå. Middagar och köttpaket kan räknas exakt.")

    st.subheader("Mellis – ungefärlig nivå")
    nivåer=["Fullt","Okej","Börjar ta slut","Slut"]
    for item in list(st.session_state.freezer_levels):
        current=st.session_state.freezer_levels[item]
        st.session_state.freezer_levels[item]=st.selectbox(
            item,nivåer,index=nivåer.index(current),key="lvl_"+item
        )

    st.subheader("Exakt lager")
    for item in list(st.session_state.freezer_exact):
        st.session_state.freezer_exact[item]=st.number_input(
            item,0,100,int(st.session_state.freezer_exact[item]),1,key="exact_"+item
        )

    st.info("Tanken är att ni aldrig ska behöva räkna pizzabullar. Ändra bara nivån när någon märker att det börjar bli tomt.")

with tabs[5]:
    st.header("Inköpslista")
    st.caption("Veckomaten och Snabblistan slås ihop automatiskt.")

    agg=Counter()
    for p in plan:
        for ing in p["recipe"]["ings"]:
            agg[ing]+=1

    # merge quick items without duplicates
    quick=[x.strip() for x in st.session_state.snabblista if x.strip()]
    merged=set(agg.keys()) | set(quick)

    def category(item):
        x=item.lower()
        if any(k in x for k in ["mjölk","yoghurt","ost","grädde","ägg"]): return "Mejeri"
        if any(k in x for k in ["kyckling","färs","korv","fläsk","högrev","skinka"]): return "Kött & chark"
        if any(k in x for k in ["potatis","morot","lök","sallad","broccoli","banan","chili"]): return "Frukt & grönt"
        if any(k in x for k in ["diskmedel","toapapper","hushåll","tvätt"]): return "Hushåll"
        return "Skafferi / övrigt"

    rows=[]
    for ing in sorted(merged, key=lambda x:(category(x),x.lower())):
        src=[]
        if ing in agg: src.append(f"{agg[ing]} rätter")
        if ing in quick: src.append("Snabblistan")
        offer_hit=next((o for o in live_offers if ing.lower() in (o.get("name","")+" "+o.get("query","")).lower()),None)
        rows.append({"✓":False,"Avdelning":category(ing),"Vara":ing,
                     "Från":" + ".join(src),
                     "ICA":("🔥 "+offer_hit.get("offer","")) if offer_hit else ""})

    edited=st.data_editor(
        rows,hide_index=True,use_container_width=True,
        column_config={"✓":st.column_config.CheckboxColumn("✓")},
        disabled=["Avdelning","Vara","Från","ICA"]
    )

    if st.button("Rensa avbockade från Snabblistan"):
        checked=[r["Vara"] for r in edited if r.get("✓")]
        st.session_state.snabblista=[x for x in st.session_state.snabblista if x not in checked]
        st.rerun()

    sio=io.StringIO()
    w=csv.DictWriter(sio,fieldnames=["Avdelning","Vara","Från","ICA"])
    w.writeheader()
    for r in rows:
        w.writerow({"Avdelning":r["Avdelning"],"Vara":r["Vara"],"Från":r["Från"],"ICA":r.get("ICA","")})
    st.download_button("⬇️ Spara inköpslista",sio.getvalue(),"inkopslista.csv","text/csv")

with tabs[6]:
    st.header("Snabblista")
    st.caption("För mjölk, yoghurt, diskmedel och annat någon märker tar slut. Ingen lagerhållning behövs.")

    st.subheader("Snabbknappar")
    cols=st.columns(3)
    for i,item in enumerate(st.session_state.common_items):
        if cols[i%3].button(f"+ {item}",key="quick_"+item):
            if item not in st.session_state.snabblista:
                st.session_state.snabblista.append(item)
            st.rerun()

    c1,c2=st.columns([3,1])
    new_item=c1.text_input("Lägg till valfri vara",placeholder="t.ex. kaffe, tandkräm, ketchup")
    if c2.button("Lägg till",use_container_width=True):
        val=new_item.strip()
        if val and val not in st.session_state.snabblista:
            st.session_state.snabblista.append(val)
            st.rerun()

    st.subheader("Att köpa")
    if not st.session_state.snabblista:
        st.success("Snabblistan är tom.")
    else:
        for i,item in enumerate(list(st.session_state.snabblista)):
            a,b=st.columns([5,1])
            a.write(f"• {item}")
            if b.button("Ta bort",key=f"rm_{i}_{item}"):
                st.session_state.snabblista.remove(item)
                st.rerun()

    st.info("Varor här dyker automatiskt upp på den samlade inköpslistan. Finns samma vara redan där via ett recept blir den inte dubbel.")

st.divider()
st.caption("Matappen v7 · live ICA-kontroll, familjeplanering, recept, mellis, snabblista och samlad inköpslista")
st.divider()

