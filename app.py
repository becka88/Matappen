
import streamlit as st
import hmac
from pathlib import Path
from datetime import date, timedelta
from collections import Counter, defaultdict
import json, csv, io, re
import requests
from bs4 import BeautifulSoup



st.set_page_config(page_title="Matappen", page_icon="🍽️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* Mobile-first Matappen */
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: rgba(0,0,0,0);}
.block-container {
    max-width: 920px;
    padding-top: 1.25rem;
    padding-bottom: 5rem;
}
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.stApp {
    background: #f7f7f4;
}
h1 {
    letter-spacing: -0.04em;
    font-size: clamp(2rem, 7vw, 3.1rem) !important;
    margin-bottom: .15rem !important;
}
h2, h3 {
    letter-spacing: -0.025em;
}
p, label, .stCaption {
    line-height: 1.45;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: white;
    border-radius: 20px;
    border: 1px solid rgba(0,0,0,.07);
    box-shadow: 0 2px 14px rgba(0,0,0,.035);
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid rgba(0,0,0,.06);
    padding: .9rem 1rem;
    border-radius: 16px;
}
div[data-testid="stMetricLabel"] {
    font-size: .8rem;
}
div[data-testid="stMetricValue"] {
    font-size: 1.25rem;
}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    min-height: 46px;
    border-radius: 14px;
    font-weight: 650;
    width: 100%;
}
.stTextInput input, .stNumberInput input {
    min-height: 46px;
    border-radius: 12px;
}
div[role="radiogroup"] {
    gap: .35rem;
}
.stTabs [data-baseweb="tab-list"] {
    gap: .35rem;
    overflow-x: auto;
    padding: .25rem;
    border-radius: 16px;
    background: rgba(255,255,255,.75);
    position: sticky;
    top: .4rem;
    z-index: 999;
    backdrop-filter: blur(14px);
    border: 1px solid rgba(0,0,0,.05);
}
.stTabs [data-baseweb="tab"] {
    min-height: 44px;
    border-radius: 12px;
    padding-left: .9rem;
    padding-right: .9rem;
    white-space: nowrap;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    box-shadow: 0 1px 6px rgba(0,0,0,.08);
}
div[data-testid="stExpander"] {
    background: white;
    border-radius: 16px;
    border: 1px solid rgba(0,0,0,.06);
    overflow: hidden;
}
[data-testid="stDataEditor"] {
    border-radius: 16px;
    overflow: hidden;
}
.matappen-eyebrow {
    font-size: .78rem;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: .08em;
    opacity: .55;
    margin-bottom: .2rem;
}
.matappen-hero {
    font-size: clamp(1.7rem, 6vw, 2.6rem);
    font-weight: 780;
    line-height: 1.08;
    letter-spacing: -.045em;
    margin: 0 0 .4rem 0;
}
.matappen-subtle {
    opacity: .64;
    font-size: .95rem;
}
.matappen-chip {
    display: inline-block;
    padding: .35rem .65rem;
    border-radius: 999px;
    background: #efefe9;
    margin: 0 .3rem .3rem 0;
    font-size: .82rem;
    font-weight: 620;
}
.matappen-price {
    font-weight: 760;
    font-size: 1.05rem;
}
@media (max-width: 640px) {
    .block-container {
        padding-left: .85rem;
        padding-right: .85rem;
        padding-top: .7rem;
    }
    h1 {font-size: 2.15rem !important;}
    div[data-testid="column"] {
        min-width: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: .65rem;
        padding-right: .65rem;
        font-size: .9rem;
    }
}

/* Matappen is primarily a phone app */
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}
@media (max-width: 640px) {
    .block-container {
        padding-left: .72rem !important;
        padding-right: .72rem !important;
        padding-top: .55rem !important;
        padding-bottom: 7rem !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: .45rem !important;
    }
    div[data-testid="stMetric"] {
        padding: .75rem .8rem !important;
    }
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
        min-height: 50px !important;
        font-size: .98rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        top: .2rem !important;
        margin-left: -.2rem;
        margin-right: -.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        min-height: 48px !important;
        font-size: .88rem !important;
        padding-left: .6rem !important;
        padding-right: .6rem !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px !important;
    }
    .matappen-hero {
        font-size: 2.15rem !important;
    }
}


/* v10: calmer, app-like hierarchy */
:root {
    --mat-bg: #f6f5f0;
    --mat-card: #ffffff;
    --mat-text: #20231f;
    --mat-muted: #6e746b;
    --mat-accent: #315f47;
    --mat-soft: #e9efe9;
    --mat-warm: #f1e7d6;
}
.stApp { background: var(--mat-bg) !important; color: var(--mat-text); }
.mat-topbar {
    display:flex; align-items:center; justify-content:space-between;
    gap:.7rem; margin:.1rem 0 .65rem 0;
}
.mat-brand { font-size:1.38rem; font-weight:800; letter-spacing:-.04em; }
.mat-status {
    display:inline-flex; align-items:center; gap:.3rem;
    background:var(--mat-soft); padding:.35rem .6rem;
    border-radius:999px; font-size:.78rem; font-weight:700;
}
.mat-kicker {
    font-size:.74rem; font-weight:800; text-transform:uppercase;
    letter-spacing:.08em; color:var(--mat-muted); margin-bottom:.25rem;
}
.mat-meal {
    font-size:clamp(1.7rem,7vw,2.55rem); line-height:1.04;
    font-weight:820; letter-spacing:-.045em; margin:.1rem 0 .55rem 0;
}
.mat-meta { color:var(--mat-muted); font-size:.91rem; }
.mat-section {
    font-size:1.18rem; font-weight:790; letter-spacing:-.025em;
    margin:1.15rem 0 .55rem 0;
}
.mat-day {
    font-weight:800; font-size:.82rem; text-transform:uppercase;
    letter-spacing:.065em; color:var(--mat-muted);
}
.mat-weekmeal { font-size:1.12rem; font-weight:760; margin:.15rem 0 .3rem 0; }
.mat-pill {
    display:inline-block; background:#f0f1ed; border-radius:999px;
    padding:.3rem .55rem; font-size:.78rem; font-weight:650;
    margin:.12rem .18rem .1rem 0;
}
.mat-offer {
    background:#edf5ee; border-radius:14px; padding:.65rem .75rem;
    font-size:.88rem; margin:.65rem 0 .2rem 0;
}
.mat-empty {
    border:1px dashed rgba(0,0,0,.16); border-radius:18px;
    padding:1.2rem; text-align:center; color:var(--mat-muted);
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 0 !important;
    box-shadow: 0 3px 18px rgba(33,42,35,.055) !important;
}
div[data-testid="stExpander"] {
    border: 0 !important;
    box-shadow: 0 2px 12px rgba(33,42,35,.045);
}
.stButton > button[kind="primary"] {
    font-weight: 780 !important;
}
@media (max-width: 640px) {
    .mat-topbar { margin-top:0; }
    .mat-brand { font-size:1.26rem; }
    .mat-meal { font-size:2rem; }
    .mat-section { margin-top:1rem; }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
}
</style>
""", unsafe_allow_html=True)


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
 # --- Middagar: vardagsfavoriter ---
 {"name":"Korv stroganoff","cat":"Middag","tags":["barnvänlig","matlåda","snabb"],"mins":25,"freeze":4,"lunch":5,"base":6,
  "ings":{"Falukorv":"800 g","Ris":"6 port","Gul lök":"1 st","Matlagningsgrädde":"3 dl","Tomatpuré":"3 msk","Morötter":"4 st"},
  "steps":["Koka riset.","Stek skivad korv och hackad lök tills de får färg.","Rör ner tomatpuré och grädde och låt sjuda cirka 10 minuter.","Servera med ris och morotsstavar."]},
 {"name":"Spaghetti med långkokt köttfärssås","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":45,"freeze":5,"lunch":5,"base":6,
  "ings":{"Nötfärs":"800 g","Spaghetti":"600 g","Krossade tomater":"800 g","Gul lök":"2 st","Morötter":"3 st","Vitlök":"2 klyftor"},
  "steps":["Bryn färsen ordentligt och tillsätt hackad lök och vitlök.","Riv morötterna och rör ner tillsammans med tomaterna.","Låt såsen puttra medan pastan kokar, gärna 25–30 minuter.","Smaka av och servera med spaghetti."]},
 {"name":"Krämig kycklingpasta med spenat","cat":"Middag","tags":["barnvänlig","matlåda","snabb"],"mins":30,"freeze":3,"lunch":4,"base":6,
  "ings":{"Kycklingfilé":"800 g","Pasta":"600 g","Matlagningsgrädde":"4 dl","Babyspenat":"150 g","Vitlök":"2 klyftor","Parmesan":"100 g"},
  "steps":["Koka pastan.","Strimla och stek kycklingen med salt och peppar.","Tillsätt vitlök, grädde och spenat och låt såsen sjuda några minuter.","Vänd ner pastan och toppa med parmesan."]},
 {"name":"Kycklingpasta med soltorkad tomat","cat":"Middag","tags":["barnvänlig","matlåda","snabb"],"mins":30,"freeze":3,"lunch":5,"base":6,
  "ings":{"Kycklingfilé":"800 g","Pasta":"600 g","Soltorkade tomater":"100 g","Matlagningsgrädde":"4 dl","Ärter":"250 g","Citron":"1 st"},
  "steps":["Koka pastan något kortare än paketets tid.","Stek kycklingbitar gyllene.","Tillsätt strimlade soltorkade tomater och grädde och sjud kort.","Vänd ner pasta och ärter och avsluta med lite citron."]},
 {"name":"Kyckling Alfredo med broccoli","cat":"Middag","tags":["barnvänlig","snabb","matlåda"],"mins":30,"freeze":3,"lunch":4,"base":6,
  "ings":{"Kycklingfilé":"800 g","Pasta":"600 g","Broccoli":"1 stort huvud","Matlagningsgrädde":"4 dl","Parmesan":"120 g","Vitlök":"2 klyftor"},
  "steps":["Koka pasta och broccoli, men spara lite pastavatten.","Stek kycklingen i bitar.","Häll på grädde, vitlök och parmesan och späd med lite pastavatten.","Vänd ner pasta och broccoli och servera direkt."]},
 {"name":"Pastagratäng med köttfärs och mozzarella","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":45,"freeze":5,"lunch":5,"base":6,
  "ings":{"Nötfärs":"700 g","Pasta":"500 g","Krossade tomater":"500 g","Gul lök":"1 st","Mozzarella":"250 g","Riven ost":"100 g"},
  "steps":["Koka pastan nästan färdig.","Bryn färs och lök och tillsätt tomaterna.","Blanda sås och pasta i en ugnsform.","Toppa med mozzarella och ost och gratinera tills ytan är gyllene."]},
 {"name":"Tacopasta","cat":"Middag","tags":["barnvänlig","fredag","matlåda"],"mins":25,"freeze":3,"lunch":4,"base":6,
  "ings":{"Nötfärs":"700 g","Pasta":"500 g","Tacokrydda":"1 påse","Crème fraiche":"3 dl","Majs":"1 burk","Riven ost":"150 g"},
  "steps":["Koka pastan.","Stek färsen och krydda med taco.","Rör ner crème fraiche och majs.","Blanda med pasta och toppa med ost."]},
 {"name":"Kycklingtacos","cat":"Middag","tags":["barnvänlig","fredag","snabb"],"mins":25,"freeze":2,"lunch":3,"base":6,
  "ings":{"Kyckling":"900 g","Tortilla":"12 st","Ost":"200 g","Salsa":"1 burk","Sallad":"1 st","Majs":"1 burk"},
  "steps":["Strimla och stek kycklingen med tacokrydda.","Hacka sallad och ställ fram tillbehören i skålar.","Låt alla bygga sina egna tacos."]},
 {"name":"Chili con carne","cat":"Middag","tags":["matlåda","frys","barnvänlig"],"mins":35,"freeze":5,"lunch":5,"base":6,
  "ings":{"Nötfärs":"700 g","Kidneybönor":"2 burkar","Krossade tomater":"800 g","Gul lök":"1 st","Paprika":"2 st","Ris":"6 port"},
  "steps":["Koka riset.","Bryn färs och lök.","Tillsätt paprika, tomater och bönor och låt puttra cirka 20 minuter.","Krydda milt vid bordet om barnen vill ha mindre hetta."]},
 {"name":"Pannbiff med gräddsås och potatis","cat":"Middag","tags":["husman","barnvänlig","matlåda"],"mins":45,"freeze":4,"lunch":5,"base":6,
  "ings":{"Blandfärs":"800 g","Potatis":"1.5 kg","Gul lök":"2 st","Matlagningsgrädde":"4 dl","Ägg":"1 st","Lingonsylt":"1 burk"},
  "steps":["Koka potatisen.","Blanda färs med ägg, kryddor och hälften av löken och forma biffar.","Stek biffarna och resten av löken.","Vispa ur pannan med grädde till en snabb sås och servera med potatis."]},
 {"name":"Köttbullar med potatismos","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":45,"freeze":5,"lunch":5,"base":6,
  "ings":{"Blandfärs":"800 g","Potatis":"1.5 kg","Mjölk":"3 dl","Ägg":"1 st","Gul lök":"1 st","Grädde":"3 dl"},
  "steps":["Koka potatisen mjuk.","Blanda färs, ägg och finhackad lök och rulla köttbullar.","Stek köttbullarna i omgångar.","Mosa potatisen med mjölk och gör en enkel gräddsås i stekpannan."]},
 {"name":"Köttfärslimpa med gräddsås","cat":"Middag","tags":["husman","matlåda","frys"],"mins":60,"freeze":5,"lunch":5,"base":6,
  "ings":{"Blandfärs":"900 g","Potatis":"1.5 kg","Ägg":"2 st","Gul lök":"1 st","Grädde":"4 dl","Morötter":"5 st"},
  "steps":["Blanda färsen med ägg, lök och kryddor och forma till en limpa.","Tillaga i ugn tills genomstekt.","Koka potatis och morötter under tiden.","Gör sås av stekskyn och grädde."]},
 {"name":"Lasagne","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":65,"freeze":5,"lunch":5,"base":8,
  "ings":{"Nötfärs":"900 g","Lasagneplattor":"1 pkt","Krossade tomater":"800 g","Gul lök":"2 st","Mjölk":"7 dl","Riven ost":"250 g"},
  "steps":["Koka ihop en mustig köttfärssås med lök och tomat.","Gör en enkel vit sås på mjölk och redning.","Varva såser och lasagneplattor i en form.","Toppa med ost och baka tills plattorna är mjuka."]},
 {"name":"Lasagnesoppa","cat":"Middag","tags":["snabb","matlåda","barnvänlig"],"mins":35,"freeze":4,"lunch":5,"base":6,
  "ings":{"Nötfärs":"600 g","Lasagneplattor":"8 st","Krossade tomater":"800 g","Buljong":"1 l","Gul lök":"1 st","Crème fraiche":"2 dl"},
  "steps":["Bryn färs och lök i en gryta.","Häll på tomater och buljong.","Bryt ner lasagneplattorna och sjud tills de är mjuka.","Servera med en klick crème fraiche."]},
 {"name":"Makaronipudding med korv","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":45,"freeze":4,"lunch":5,"base":6,
  "ings":{"Falukorv":"600 g","Makaroner":"500 g","Ägg":"4 st","Mjölk":"6 dl","Gul lök":"1 st","Riven ost":"150 g"},
  "steps":["Koka makaronerna och stek korv och lök.","Lägg allt i en ugnsform.","Vispa ihop ägg och mjölk och häll över.","Toppa med ost och grädda tills puddingen stannat."]},
 {"name":"Korv med rotfruktsmos","cat":"Middag","tags":["barnvänlig","vardag"],"mins":35,"freeze":3,"lunch":4,"base":6,
  "ings":{"Köttkorv":"800 g","Potatis":"1 kg","Morötter":"500 g","Palsternacka":"300 g","Mjölk":"2 dl","Senap":"1 tub"},
  "steps":["Skala och koka rotfrukterna mjuka.","Värm eller stek korven.","Mosa rotfrukterna med mjölk och lite smör.","Servera med senap."]},
 {"name":"Ugnskorv med tomat, lök och ost","cat":"Middag","tags":["barnvänlig","enkel"],"mins":40,"freeze":3,"lunch":4,"base":6,
  "ings":{"Falukorv":"800 g","Potatis":"1.4 kg","Tomater":"4 st","Gul lök":"2 st","Riven ost":"150 g","Senap":"3 msk"},
  "steps":["Skär skåror i korven och lägg i en form.","Fyll med tomat, lök och lite senap och toppa med ost.","Baka i ugn och koka potatis under tiden."]},
 {"name":"Kycklinggryta med curry och äpple","cat":"Middag","tags":["barnvänlig","matlåda","snabb"],"mins":30,"freeze":4,"lunch":5,"base":6,
  "ings":{"Kycklingfilé":"800 g","Ris":"6 port","Matlagningsgrädde":"4 dl","Äpple":"2 st","Curry":"2 tsk","Gul lök":"1 st"},
  "steps":["Koka riset.","Stek kyckling och lök.","Pudra över curry och tillsätt grädde och tärnat äpple.","Sjud tills kycklingen är klar och servera med ris."]},
 {"name":"Krämig kycklinggryta med paprika","cat":"Middag","tags":["barnvänlig","matlåda"],"mins":35,"freeze":4,"lunch":5,"base":6,
  "ings":{"Kycklinglårfilé":"900 g","Ris":"6 port","Paprika":"2 st","Crème fraiche":"3 dl","Kycklingfond":"2 msk","Gul lök":"1 st"},
  "steps":["Koka riset.","Bryn kycklingen och tillsätt lök och paprika.","Rör ner crème fraiche, fond och en skvätt vatten.","Låt sjuda tills kycklingen är mör."]},
 {"name":"Kyckling i ugn med citron och vitlök","cat":"Middag","tags":["enkel","matlåda","barnvänlig"],"mins":45,"freeze":4,"lunch":5,"base":6,
  "ings":{"Kycklinglårfilé":"1 kg","Potatis":"1.5 kg","Citron":"2 st","Vitlök":"4 klyftor","Morötter":"5 st","Crème fraiche":"2 dl"},
  "steps":["Lägg potatis och morötter i en stor form och rosta en stund.","Lägg på kycklingen och krydda med citron och vitlök.","Tillaga tills kycklingen är genomstekt och servera med crème fraiche."]},
 {"name":"Fläskytterfilé med potatisgratäng","cat":"Middag","tags":["helg","vuxen","matlåda"],"mins":60,"freeze":3,"lunch":4,"base":6,
  "ings":{"Fläskytterfilé":"1 kg","Potatis":"1.5 kg","Grädde":"5 dl","Vitlök":"2 klyftor","Riven ost":"150 g","Sallad":"1 påse"},
  "steps":["Skiva potatis och lägg med grädde, vitlök och ost i en form.","Baka tills gratängen är mjuk och gyllene.","Bryn köttet och tillaga färdigt i ugn eller panna.","Låt köttet vila före skivning."]},
 {"name":"Fläskfilégryta med champinjoner","cat":"Middag","tags":["vuxen","matlåda","helg"],"mins":40,"freeze":4,"lunch":5,"base":6,
  "ings":{"Fläskfilé":"900 g","Champinjoner":"400 g","Matlagningsgrädde":"4 dl","Dijonsenap":"2 msk","Gul lök":"1 st","Ris":"6 port"},
  "steps":["Koka riset.","Bryn skivat kött i omgångar och lägg åt sidan.","Stek lök och champinjoner och tillsätt grädde och senap.","Lägg tillbaka köttet och sjud försiktigt tills allt är klart."]},
 {"name":"Fläskfilépasta med svamp och citron","cat":"Middag","tags":["vuxen","snabb","matlåda"],"mins":30,"freeze":3,"lunch":4,"base":6,
  "ings":{"Fläskfilé":"800 g","Pasta":"600 g","Champinjoner":"300 g","Matlagningsgrädde":"3 dl","Citron":"1 st","Parmesan":"80 g"},
  "steps":["Koka pastan.","Stek tunt skivad fläskfilé och svamp hastigt.","Häll på grädde och låt koka ihop.","Vänd ner pasta och smaka av med citron och parmesan."]},
 {"name":"Pasta carbonara","cat":"Middag","tags":["snabb","barnvänlig","matlåda"],"mins":20,"freeze":2,"lunch":4,"base":6,
  "ings":{"Spaghetti":"600 g","Bacon":"300 g","Ägg":"5 st","Parmesan":"120 g","Svartpeppar":"1 tsk"},
  "steps":["Koka spaghetti och spara lite pastavatten.","Stek bacon krispigt.","Vispa ihop ägg, parmesan och svartpeppar.","Vänd ihop allt från värmen och späd med pastavatten tills såsen blir krämig."]},
 {"name":"Baconpasta med ärter","cat":"Middag","tags":["snabb","barnvänlig","matlåda"],"mins":20,"freeze":2,"lunch":4,"base":6,
  "ings":{"Pasta":"600 g","Bacon":"300 g","Ärter":"300 g","Crème fraiche":"3 dl","Parmesan":"80 g"},
  "steps":["Koka pastan.","Stek bacon och tillsätt ärter.","Rör ner crème fraiche och lite pastavatten.","Blanda med pastan och toppa med parmesan."]},
 {"name":"Krämig chorizopasta","cat":"Middag","tags":["vuxen","snabb","matlåda"],"mins":30,"freeze":3,"lunch":5,"base":6,
  "ings":{"Chorizo":"500 g","Pasta":"600 g","Paprika":"2 st","Matlagningsgrädde":"4 dl","Gul lök":"1 st","Parmesan":"80 g"},
  "steps":["Koka pastan.","Stek skivad chorizo med lök och paprika.","Tillsätt grädde och låt såsen koka ihop.","Blanda med pasta och parmesan."]},
 {"name":"Krämig kycklingpasta med chipotle","cat":"Middag","tags":["vuxen","snabb","matlåda","het"],"mins":30,"freeze":3,"lunch":5,"base":6,
  "ings":{"Kycklingfilé":"800 g","Pasta":"600 g","Matlagningsgrädde":"4 dl","Chipotlepasta":"2 msk","Lime":"1 st","Vitlök":"3 klyftor"},
  "steps":["Koka pastan.","Stek kycklingbitar med vitlök.","Rör ner chipotle och grädde och låt såsen sjuda några minuter.","Vänd ner pasta och avsluta med lime."]},
 {"name":"Asiatisk köttfärsgryta med ris","cat":"Middag","tags":["vuxen","snabb","matlåda"],"mins":30,"freeze":4,"lunch":5,"base":6,
  "ings":{"Nötfärs":"700 g","Ris":"6 port","Paprika":"2 st","Soja":"4 msk","Ingefära":"1 bit","Vitlök":"3 klyftor"},
  "steps":["Koka riset.","Stek färsen hårt så den får ordentlig yta.","Tillsätt paprika, vitlök och riven ingefära.","Smaka av med soja och lite chili om ni vill ha mer hetta."]},
 {"name":"Grekiska färsbiffar med citronpotatis","cat":"Middag","tags":["vuxen","matlåda","helg"],"mins":50,"freeze":4,"lunch":5,"base":6,
  "ings":{"Nötfärs":"800 g","Potatis":"1.5 kg","Fetaost":"200 g","Citron":"2 st","Vitlök":"2 klyftor","Tzatziki":"3 dl"},
  "steps":["Rosta potatisklyftor med citron och kryddor.","Blanda färs med smulad fetaost och vitlök och forma biffar.","Stek biffarna tills genomstekta.","Servera med potatis och tzatziki."]},
 {"name":"Shepherd's pie","cat":"Middag","tags":["matlåda","frys","vuxen"],"mins":65,"freeze":5,"lunch":5,"base":8,
  "ings":{"Nötfärs":"900 g","Potatis":"1.8 kg","Morötter":"4 st","Gul lök":"2 st","Tomatpuré":"3 msk","Mjölk":"3 dl"},
  "steps":["Koka potatis och gör ett ganska fast mos.","Bryn färs, lök och morötter och rör ner tomatpuré och lite vatten.","Lägg färsen i en form och bred moset ovanpå.","Gratinera tills toppen fått färg."]},
 {"name":"Het högrevsgryta","cat":"Middag","tags":["vuxen","matlåda","frys","långkok"],"mins":150,"freeze":5,"lunch":5,"base":8,
  "ings":{"Högrev":"1.3 kg","Gul lök":"2 st","Morötter":"5 st","Chili":"2 st","Krossade tomater":"400 g","Ris":"8 port"},
  "steps":["Bryn högreven i omgångar.","Fräs lök, morötter och chili.","Lägg tillbaka köttet, tillsätt tomater och vatten så det nästan täcker.","Låt sjuda mycket försiktigt tills köttet faller isär."]},
 {"name":"Mustig gulasch med högrev","cat":"Middag","tags":["vuxen","frys","matlåda","långkok"],"mins":140,"freeze":5,"lunch":5,"base":8,
  "ings":{"Högrev":"1.2 kg","Potatis":"1 kg","Paprika":"3 st","Gul lök":"2 st","Krossade tomater":"800 g","Paprikapulver":"2 msk"},
  "steps":["Bryn köttet ordentligt.","Fräs lök och paprika med paprikapulver.","Tillsätt tomat och vatten och låt sjuda tills köttet är mört.","Lägg i potatis mot slutet och koka tills den är mjuk."]},
 {"name":"Kycklingfärsbiffar med rostad potatis","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":45,"freeze":5,"lunch":5,"base":6,
  "ings":{"Kycklingfärs":"800 g","Potatis":"1.5 kg","Ägg":"1 st","Vitlök":"1 klyfta","Crème fraiche":"3 dl","Gurka":"1 st"},
  "steps":["Rosta potatisklyftor i ugn.","Blanda kycklingfärs med ägg och kryddor och forma biffar.","Stek biffarna tills de är helt genomstekta.","Servera med gurka och crème fraiche."]},
 {"name":"Kycklingbullar i mild currysås","cat":"Middag","tags":["barnvänlig","matlåda","frys"],"mins":35,"freeze":5,"lunch":5,"base":6,
  "ings":{"Kycklingfärs":"800 g","Ris":"6 port","Ägg":"1 st","Matlagningsgrädde":"4 dl","Curry":"2 tsk","Morötter":"4 st"},
  "steps":["Koka riset.","Forma små bollar av kycklingfärs, ägg och kryddor och stek dem runt om.","Häll på grädde och curry och låt bollarna sjuda färdigt.","Servera med ris och rivna morötter."]},
 {"name":"Burritos med köttfärs","cat":"Middag","tags":["barnvänlig","fredag","matlåda"],"mins":35,"freeze":4,"lunch":4,"base":6,
  "ings":{"Nötfärs":"700 g","Tortilla":"8 st","Ris":"4 port","Svarta bönor":"1 burk","Salsa":"1 burk","Riven ost":"200 g"},
  "steps":["Koka riset och stek färsen med tacokrydda.","Blanda färs, ris och bönor.","Fördela fyllningen i tortillas, toppa med salsa och ost och rulla ihop.","Gratinera kort i ugn."]},
 {"name":"Tacogratäng","cat":"Middag","tags":["barnvänlig","fredag","matlåda"],"mins":40,"freeze":4,"lunch":5,"base":6,
  "ings":{"Nötfärs":"700 g","Tacokrydda":"1 påse","Crème fraiche":"4 dl","Majs":"1 burk","Riven ost":"200 g","Nachochips":"1 påse"},
  "steps":["Stek färsen och krydda.","Lägg färsen i en form och fördela majs och crème fraiche ovanpå.","Toppa med ost och gratinera.","Servera med nachochips och sallad."]},

 # --- Mellis / frys ---
 {"name":"Pizzabullar","cat":"Mellis","tags":["frys","batch","barnvänlig"],"mins":50,"freeze":5,"lunch":3,"base":20,
  "ings":{"Vetemjöl":"8 dl","Jäst":"25 g","Mjölk":"3 dl","Skinka":"250 g","Ost":"250 g","Tomatsås":"2 dl"},
  "steps":["Gör en mjuk deg och låt jäsa.","Kavla ut, bred på tomatsås, skinka och ost.","Rulla ihop, skär i bitar och grädda.","Låt svalna helt och frys styckvis."]},
 {"name":"Köttfärspiroger","cat":"Mellis","tags":["frys","batch","protein"],"mins":70,"freeze":5,"lunch":5,"base":16,
  "ings":{"Nötfärs":"600 g","Gul lök":"1 st","Pirogdeg":"2 pkt","Ost":"150 g","Ägg":"1 st"},
  "steps":["Stek färs och lök och låt fyllningen svalna.","Fyll degbitar med färs och ost och vik ihop.","Pensla med ägg och grädda.","Frys när pirogerna svalnat."]},
 {"name":"Bananpannkakor","cat":"Mellis","tags":["frys","snabb","barnvänlig"],"mins":20,"freeze":4,"lunch":2,"base":16,
  "ings":{"Banan":"4 st","Ägg":"6 st","Havregryn":"4 dl","Kanel":"1 tsk"},
  "steps":["Mixa allt till en smet.","Stek små pannkakor på medelvärme.","Låt svalna och frys med bakplåtspapper mellan lagren."]},
 {"name":"Ost- och skinkhorn","cat":"Mellis","tags":["frys","batch","barnvänlig"],"mins":45,"freeze":5,"lunch":3,"base":16,
  "ings":{"Deg":"2 pkt","Skinka":"250 g","Ost":"250 g","Ägg":"1 st"},
  "steps":["Dela degen i trianglar.","Lägg på skinka och ost och rulla ihop.","Pensla med ägg och grädda tills gyllene.","Frys efter avsvalning."]},
 {"name":"Miniquesadillas med kyckling","cat":"Mellis","tags":["frys","protein","barnvänlig"],"mins":25,"freeze":4,"lunch":4,"base":12,
  "ings":{"Tortilla":"6 st","Tillagad kyckling":"300 g","Riven ost":"250 g","Majs":"1 liten burk"},
  "steps":["Fördela kyckling, ost och majs på halva tortillabröden.","Vik ihop och stek lätt på båda sidor.","Skär varje quesadilla i två delar och låt svalna.","Frys styckvis."]},
 {"name":"Havre- och bananmuffins","cat":"Mellis","tags":["frys","batch","barnvänlig"],"mins":35,"freeze":5,"lunch":2,"base":12,
  "ings":{"Banan":"3 st","Ägg":"3 st","Havregryn":"5 dl","Mjölk":"2 dl","Bakpulver":"2 tsk","Kanel":"1 tsk"},
  "steps":["Mixa banan, ägg och mjölk.","Rör ner havregryn, bakpulver och kanel.","Fördela i muffinsformar och grädda tills de stannat.","Kyl och frys."]},
 {"name":"Pannkaksrullar med skinka och ost","cat":"Mellis","tags":["frys","batch","protein"],"mins":40,"freeze":4,"lunch":4,"base":12,
  "ings":{"Pannkakor":"12 st","Skinka":"300 g","Riven ost":"250 g","Crème fraiche":"2 dl"},
  "steps":["Lägg skinka, ost och en liten klick crème fraiche på varje pannkaka.","Rulla ihop och lägg tätt i en form.","Värm kort i ugn tills osten smält.","Låt svalna och frys styckvis."]},
 {"name":"Frukostwraps med ägg och skinka","cat":"Mellis","tags":["frys","protein","mättande"],"mins":30,"freeze":4,"lunch":4,"base":10,
  "ings":{"Tortilla":"10 st","Ägg":"8 st","Skinka":"300 g","Riven ost":"200 g"},
  "steps":["Gör mjuk äggröra.","Fördela ägg, skinka och ost på tortillas.","Rulla tätt och låt svalna.","Frys styckvis och värm vid behov."]},
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
        if r["name"] in st.session_state.get("disliked_recipes", []): score-=100
        if i<4 and r["mins"]<=40: score+=5
        if r["lunch"]>=4: score+=3
        if offer_for_recipe(r, offers or []): score+=12
        ranked.append((score,r))
    return sorted(ranked,key=lambda x:x[0],reverse=True)[0][1]


def ranked_recipes(i, kids, taco, used=None, offers=None):
    """Return good dinner alternatives in UX-friendly order."""
    used = used or set()
    options = [r for r in RECIPES if r["cat"] == "Middag"]
    ranked = []
    for r in options:
        score = 0
        if taco and i == 4 and "taco" in r["name"].lower():
            score += 20
        if kids and "barnvänlig" in r["tags"]:
            score += 9
        if not kids and "vuxen" in r["tags"]:
            score += 9
        if i < 4 and r["mins"] <= 35:
            score += 5
        if r["lunch"] >= 4:
            score += 3
        if r["freeze"] >= 4:
            score += 1
        if offer_for_recipe(r, offers or []):
            score += 12
        if r["name"] in used:
            score -= 7
        if r["name"] in st.session_state.get("disliked_recipes", []):
            score -= 100
        ranked.append((score, r["mins"], r["name"], r))
    ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
    return [x[3] for x in ranked]

def recipe_by_name(name):
    return next((r for r in RECIPES if r["name"] == name), None)

def swap_meal(day_index, current_name, kids, taco, offers):
    options = ranked_recipes(day_index, kids, taco, set(), offers)
    names = [r["name"] for r in options]
    try:
        pos = names.index(current_name)
    except ValueError:
        pos = -1
    next_recipe = options[(pos + 1) % len(options)]
    st.session_state.meal_overrides[day_index] = next_recipe["name"]


def dislike_and_replace(day_index, recipe_name, kids, taco, offers):
    """Downvote a planned recipe and immediately replace it."""
    if recipe_name not in st.session_state.disliked_recipes:
        st.session_state.disliked_recipes.append(recipe_name)

    options = ranked_recipes(day_index, kids, taco, {recipe_name}, offers)
    replacement = next(
        (r for r in options
         if r["name"] != recipe_name
         and r["name"] not in st.session_state.disliked_recipes),
        None,
    )
    if replacement:
        st.session_state.meal_overrides[day_index] = replacement["name"]

# ---------- State ----------
defaults={
 "kids_arrive":True,"lunchboxes":2,"taco":True,"budget":1200,
 "snabblista":[],
 "common_items":["Mjölk","Yoghurt","Bröd","Ägg","Diskmedel","Toapapper"],
 "freezer_levels":{"Pizzabullar":"Okej","Köttfärspiroger":"Okej","Bananpannkakor":"Fullt"},
 "freezer_exact":{"Middagsportioner":2,"Kycklingpaket":1,"Köttfärspaket":0},
 "ratings":{},"pantry":[],"offers":["Falukorv 800 g – 2 för 65 kr (verifierat exempel)"],
 "meal_overrides":{},"shopping_checked":[],"disliked_recipes":[],"screen":"Idag"
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v


st.markdown("""
<style>
/* ===== Matappen v12: PHONE FIRST ===== */
#MainMenu, footer, [data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display:none !important;
}
header[data-testid="stHeader"] {
    background:transparent !important;
    height:0 !important;
}
.block-container {
    width:100% !important;
    max-width:520px !important;
    padding:14px 14px 90px 14px !important;
    margin:0 auto !important;
}
.stApp {
    background:#F7F6F1 !important;
}
html, body, [class*="css"] {
    font-family:Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}
h1,h2,h3,p { letter-spacing:normal; }

.phone-head {
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin:2px 0 12px 0;
}
.phone-brand {
    font-size:1.34rem;
    line-height:1;
    font-weight:850;
    letter-spacing:-.04em;
}
.phone-private {
    font-size:.72rem;
    font-weight:750;
    background:#E7EFE8;
    padding:6px 9px;
    border-radius:999px;
}
.screen-title {
    font-size:1.72rem;
    font-weight:850;
    letter-spacing:-.045em;
    line-height:1.05;
    margin:18px 0 5px;
}
.screen-sub {
    font-size:.9rem;
    color:#6B716A;
    margin-bottom:15px;
}
.day-label {
    font-size:.76rem;
    text-transform:uppercase;
    letter-spacing:.09em;
    font-weight:800;
    color:#72776F;
    margin-bottom:6px;
}
.hero-meal {
    font-size:1.85rem;
    font-weight:850;
    line-height:1.06;
    letter-spacing:-.045em;
    margin:2px 0 10px;
}
.meta-row {
    font-size:.88rem;
    color:#666D65;
    line-height:1.55;
}
.tag {
    display:inline-block;
    font-size:.76rem;
    font-weight:700;
    border-radius:999px;
    background:#F0F0EB;
    padding:5px 8px;
    margin:6px 4px 0 0;
}
.offer-box {
    margin-top:12px;
    background:#EDF5EE;
    border-radius:14px;
    padding:11px 12px;
    font-size:.86rem;
    line-height:1.4;
}
.section-label {
    font-size:1.08rem;
    font-weight:820;
    letter-spacing:-.025em;
    margin:24px 0 10px;
}
.week-name {
    font-size:1.16rem;
    line-height:1.14;
    font-weight:800;
    letter-spacing:-.025em;
    margin:3px 0 6px;
}
.muted {
    color:#71766F;
    font-size:.84rem;
}
.empty {
    padding:22px 14px;
    border-radius:16px;
    border:1px dashed rgba(0,0,0,.16);
    text-align:center;
    color:#71766F;
    background:rgba(255,255,255,.45);
}

/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background:#FFFFFF !important;
    border:0 !important;
    border-radius:20px !important;
    box-shadow:0 2px 14px rgba(35,40,35,.055) !important;
    padding:2px !important;
}
div[data-testid="stExpander"] {
    background:#FFFFFF !important;
    border:0 !important;
    border-radius:16px !important;
    box-shadow:none !important;
}
details summary {
    min-height:48px !important;
    align-items:center !important;
}

/* Touch targets */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
    width:100% !important;
    min-height:52px !important;
    border-radius:15px !important;
    font-size:.97rem !important;
    font-weight:750 !important;
    margin:2px 0 !important;
}
.stTextInput input,
.stNumberInput input,
div[data-baseweb="select"] > div {
    min-height:50px !important;
    border-radius:14px !important;
}
div[data-testid="stCheckbox"] label {
    min-height:47px !important;
    align-items:center !important;
    padding:3px 0 !important;
}
div[data-testid="stCheckbox"] p {
    font-size:.98rem !important;
}

/* Top navigation: one calm row, no tabs */
div[data-testid="stSegmentedControl"] {
    position:sticky;
    top:6px;
    z-index:1000;
    background:rgba(247,246,241,.94);
    backdrop-filter:blur(10px);
    padding:5px 0 8px;
}
div[data-testid="stSegmentedControl"] [role="radiogroup"] {
    width:100% !important;
}
div[data-testid="stSegmentedControl"] label {
    min-height:45px !important;
    font-size:.86rem !important;
}

/* We avoid columns in v12, but make any framework leftovers stack safely. */
@media (max-width:640px) {
    .block-container {
        max-width:100% !important;
        padding-left:12px !important;
        padding-right:12px !important;
    }
    .hero-meal { font-size:1.72rem; }
}
</style>
""", unsafe_allow_html=True)


# ---------- UI ----------
st.markdown(
    '<div class="phone-head"><div class="phone-brand">🍽️ Matappen</div>'
    '<div class="phone-private">● Privat</div></div>',
    unsafe_allow_html=True
)

screen = st.segmented_control(
    "Navigation",
    ["Idag", "Vecka", "Handla", "Mer"],
    default=st.session_state.screen if st.session_state.screen in ["Idag","Vecka","Handla","Mer"] else "Idag",
    label_visibility="collapsed",
)
if screen:
    st.session_state.screen = screen

ica_data = get_current_ica_offers()
live_offers = ica_data.get("offers", [])

# Build weekly plan once.
used = set()
plan = []
for i, d in enumerate(DAYS):
    kh = kids_here(i, st.session_state.kids_arrive)
    auto = choose_recipe(i, kh, st.session_state.taco and kh, used, live_offers)
    override = recipe_by_name(st.session_state.meal_overrides.get(i))
    r = override or auto
    used.add(r["name"])
    plan.append({
        "day": d,
        "kids": kh,
        "recipe": r,
        "portions": portions(kh, st.session_state.lunchboxes),
        "offer": offer_for_recipe(r, live_offers),
    })

# Shared helpers for shopping
def shop_category(item):
    x = item.lower()
    if any(k in x for k in ["mjölk","yoghurt","ost","grädde","crème","ägg","parmesan","mozzarella"]):
        return "🥛 Mejeri"
    if any(k in x for k in ["kyckling","färs","korv","fläsk","högrev","skinka","bacon","chorizo"]):
        return "🥩 Kött & chark"
    if any(k in x for k in ["potatis","morot","lök","sallad","broccoli","banan","chili","paprika","citron","lime","äpple","gurka","tomat","spenat","champinjon"]):
        return "🥕 Frukt & grönt"
    if any(k in x for k in ["diskmedel","toapapper","hushåll","tvätt"]):
        return "🧻 Hushåll"
    return "🥫 Skafferi"

# ===== IDAG =====
if st.session_state.screen == "Idag":
    today_idx = min(date.today().weekday(), 6)
    p = plan[today_idx]
    tomorrow = plan[(today_idx + 1) % 7]

    st.markdown('<div class="screen-title">Idag</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="day-label">{p["day"]} · {"Barnen hemma" if p["kids"] else "Vuxenkväll"}</div>'
        f'<div class="hero-meal">{p["recipe"]["name"]}</div>'
        f'<div class="meta-row">⏱ {p["recipe"]["mins"]} min<br>'
        f'🍽 {p["portions"]} portioner · 🥡 Matlåda {p["recipe"]["lunch"]}/5</div>',
        unsafe_allow_html=True
    )
    if p["offer"]:
        st.markdown(
            f'<div class="offer-box">🔥 <b>ICA-erbjudande matchar</b><br>'
            f'{p["offer"].get("name","")} · {p["offer"].get("offer","")}</div>',
            unsafe_allow_html=True
        )

    with st.expander("👩‍🍳 Visa recept"):
        st.write("**Ingredienser**")
        for k, v in p["recipe"]["ings"].items():
            st.write(f"{k} · {v}")
        st.write("**Gör så här**")
        for n, step in enumerate(p["recipe"]["steps"], 1):
            st.write(f"{n}. {step}")

    if st.button("👎 Inte sugen – ge mig något annat", type="primary"):
        dislike_and_replace(
            today_idx, p["recipe"]["name"], p["kids"],
            st.session_state.taco and p["kids"], live_offers
        )
        st.rerun()

    if st.button("↻ Byt bara idag"):
        swap_meal(
            today_idx, p["recipe"]["name"], p["kids"],
            st.session_state.taco and p["kids"], live_offers
        )
        st.rerun()

    st.markdown('<div class="section-label">Lägg till på inköpslistan</div>', unsafe_allow_html=True)
    with st.form("mobile_quick_add", clear_on_submit=True):
        item = st.text_input("Vara", placeholder="T.ex. mjölk eller diskmedel", label_visibility="collapsed")
        if st.form_submit_button("＋ Lägg till"):
            val = item.strip()
            if val and val not in st.session_state.snabblista:
                st.session_state.snabblista.append(val)
            st.rerun()

    st.markdown('<div class="section-label">I morgon</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            f'<div class="day-label">{tomorrow["day"]}</div>'
            f'<div class="week-name">{tomorrow["recipe"]["name"]}</div>'
            f'<span class="tag">⏱ {tomorrow["recipe"]["mins"]} min</span>'
            f'<span class="tag">{"👨‍👩‍👧‍👦 Barn" if tomorrow["kids"] else "🌙 Vuxen"}</span>',
            unsafe_allow_html=True
        )

# ===== VECKA =====
elif st.session_state.screen == "Vecka":
    st.markdown('<div class="screen-title">Veckan</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-sub">En middag per dag. Ogilla eller byt utan att röra resten.</div>', unsafe_allow_html=True)

    for i, p in enumerate(plan):
        with st.container(border=True):
            st.markdown(
                f'<div class="day-label">{p["day"]}</div>'
                f'<div class="week-name">{p["recipe"]["name"]}</div>'
                f'<span class="tag">{"👨‍👩‍👧‍👦 Barn" if p["kids"] else "🌙 Vuxen"}</span>'
                f'<span class="tag">⏱ {p["recipe"]["mins"]} min</span>'
                f'<span class="tag">🥡 {p["recipe"]["lunch"]}/5</span>',
                unsafe_allow_html=True
            )
            if p["offer"]:
                st.markdown(
                    f'<div class="offer-box">🔥 {p["offer"].get("offer","ICA-erbjudande")}</div>',
                    unsafe_allow_html=True
                )

            with st.expander("Visa recept"):
                for k, v in p["recipe"]["ings"].items():
                    st.write(f"{k} · {v}")
                st.write("")
                for n, step in enumerate(p["recipe"]["steps"], 1):
                    st.write(f"{n}. {step}")

            if st.button("👎 Inte sugen – byt ut", key=f"week_dislike_{i}"):
                dislike_and_replace(
                    i, p["recipe"]["name"], p["kids"],
                    st.session_state.taco and p["kids"], live_offers
                )
                st.rerun()

            if st.button("↻ Byt bara den här", key=f"week_swap_{i}"):
                swap_meal(
                    i, p["recipe"]["name"], p["kids"],
                    st.session_state.taco and p["kids"], live_offers
                )
                st.rerun()

    if st.button("Återställ veckans byten"):
        st.session_state.meal_overrides = {}
        st.rerun()

# ===== HANDLA =====
elif st.session_state.screen == "Handla":
    st.markdown('<div class="screen-title">Handla</div>', unsafe_allow_html=True)

    mode = st.segmented_control(
        "Handla vy",
        ["Lista", "Lägg till", "ICA"],
        default="Lista",
        label_visibility="collapsed"
    )

    agg = Counter()
    for p in plan:
        for ing in p["recipe"]["ings"]:
            agg[ing] += 1
    quick = [x.strip() for x in st.session_state.snabblista if x.strip()]
    merged = set(agg.keys()) | set(quick)

    if mode == "Lista":
        checked = set(st.session_state.shopping_checked)
        done = len([x for x in merged if x in checked])
        total = len(merged)

        st.markdown(f'<div class="screen-sub">{done} av {total} avbockade</div>', unsafe_allow_html=True)
        if total:
            st.progress(done / total)
        else:
            st.markdown('<div class="empty">Inköpslistan är tom.</div>', unsafe_allow_html=True)

        groups = {}
        for item in sorted(merged, key=lambda x: (shop_category(x), x.lower())):
            groups.setdefault(shop_category(item), []).append(item)

        new_checked = set(checked)
        for cat, items in groups.items():
            st.markdown(f'<div class="section-label">{cat}</div>', unsafe_allow_html=True)
            for item in items:
                hit = next(
                    (o for o in live_offers if item.lower() in (o.get("name","")+" "+o.get("query","")).lower()),
                    None
                )
                label = item + (f"  🔥 {hit.get('offer','')}" if hit else "")
                selected = st.checkbox(label, value=item in checked, key=f"mobile_buy_{cat}_{item}")
                if selected:
                    new_checked.add(item)
                else:
                    new_checked.discard(item)

        st.session_state.shopping_checked = list(new_checked)

        if st.button("✓ Ta bort allt som är köpt", type="primary"):
            bought = set(st.session_state.shopping_checked)
            st.session_state.snabblista = [x for x in st.session_state.snabblista if x not in bought]
            st.session_state.shopping_checked = []
            st.rerun()

    elif mode == "Lägg till":
        st.markdown('<div class="screen-sub">Sådant ni märker saknas hemma.</div>', unsafe_allow_html=True)
        with st.form("shopping_add_form", clear_on_submit=True):
            custom = st.text_input("Ny vara", placeholder="Skriv en vara")
            if st.form_submit_button("＋ Lägg till", type="primary"):
                val = custom.strip()
                if val and val not in st.session_state.snabblista:
                    st.session_state.snabblista.append(val)
                st.rerun()

        for item in ["Mjölk","Yoghurt","Bröd","Ägg","Diskmedel","Toapapper"]:
            if st.button(f"＋ {item}", key=f"onehand_{item}"):
                if item not in st.session_state.snabblista:
                    st.session_state.snabblista.append(item)
                st.rerun()

        if st.session_state.snabblista:
            st.markdown('<div class="section-label">Tillagt manuellt</div>', unsafe_allow_html=True)
            for i, item in enumerate(list(st.session_state.snabblista)):
                with st.container(border=True):
                    st.write(f"**{item}**")
                    if st.button("Ta bort", key=f"remove_mobile_quick_{i}"):
                        st.session_state.snabblista.remove(item)
                        st.rerun()

    else:
        st.markdown(
            f'<div class="screen-sub">{ica_data["status"]} · vecka {ica_data["week"]} · '
            f'{len(live_offers)} verifierade träffar</div>',
            unsafe_allow_html=True
        )
        if st.button("↻ Uppdatera erbjudanden"):
            get_current_ica_offers.clear()
            st.rerun()

        if ica_data.get("errors"):
            st.info("Matappen visar bara erbjudanden som kunnat verifieras.")

        if not live_offers:
            st.markdown('<div class="empty">Inga erbjudanden kunde verifieras just nu.</div>', unsafe_allow_html=True)

        for o in live_offers[:30]:
            with st.container(border=True):
                st.write(f"**{o.get('name','Vara')}**")
                st.write(f"🔥 {o.get('offer','Erbjudande')}")

# ===== MER =====
else:
    st.markdown('<div class="screen-title">Mer</div>', unsafe_allow_html=True)
    section = st.selectbox(
        "Vad vill du göra?",
        ["Recept", "Frysen", "Familjen", "Nedröstade recept", "App"]
    )

    if section == "Recept":
        st.markdown('<div class="section-label">Receptbanken</div>', unsafe_allow_html=True)
        q = st.text_input("Sök recept", placeholder="T.ex. kyckling, pasta, 30 min")
        recipe_type = st.selectbox("Typ", ["Middag","Mellis"])
        recipe_filter = st.selectbox("Filter", ["Alla","≤30 min","Barnvänligt","Matlåda","Frys","Vuxen"])

        filtered = []
        for r in RECIPES:
            if r["cat"] != recipe_type:
                continue
            hay = (r["name"]+" "+" ".join(r["ings"].keys())+" "+" ".join(r["tags"])).lower()
            if q.strip().lower() not in hay:
                continue
            if recipe_filter == "≤30 min" and r["mins"] > 30: continue
            if recipe_filter == "Barnvänligt" and "barnvänlig" not in r["tags"]: continue
            if recipe_filter == "Matlåda" and r["lunch"] < 4: continue
            if recipe_filter == "Frys" and r["freeze"] < 4: continue
            if recipe_filter == "Vuxen" and "vuxen" not in r["tags"]: continue
            filtered.append(r)

        if not filtered:
            st.markdown('<div class="empty">Inga recept matchar.</div>', unsafe_allow_html=True)

        for r in filtered:
            with st.expander(f"{r['name']} · {r['mins']} min"):
                st.caption(f"❄️ Frys {r['freeze']}/5 · 🥡 Matlåda {r['lunch']}/5")
                st.write("**Ingredienser**")
                for k,v in r["ings"].items():
                    st.write(f"{k} · {v}")
                st.write("**Gör så här**")
                for n,step in enumerate(r["steps"],1):
                    st.write(f"{n}. {step}")

    elif section == "Frysen":
        st.markdown('<div class="section-label">Mellis</div>', unsafe_allow_html=True)
        levels = ["Fullt","Okej","Börjar ta slut","Slut"]
        for item in list(st.session_state.freezer_levels):
            cur = st.session_state.freezer_levels[item]
            st.session_state.freezer_levels[item] = st.selectbox(
                item, levels, index=levels.index(cur), key=f"v12_freeze_{item}"
            )

        st.markdown('<div class="section-label">Exakt lager</div>', unsafe_allow_html=True)
        for item in list(st.session_state.freezer_exact):
            st.session_state.freezer_exact[item] = st.number_input(
                item, 0, 100, int(st.session_state.freezer_exact[item]), 1, key=f"v12_exact_{item}"
            )

    elif section == "Familjen":
        st.session_state.kids_arrive = st.radio(
            "På torsdag",
            ["Barnen kommer","Barnen åker"],
            index=0 if st.session_state.kids_arrive else 1
        ) == "Barnen kommer"
        st.session_state.lunchboxes = st.slider(
            "Matlådor efter en middag", 0, 4, st.session_state.lunchboxes
        )
        st.session_state.taco = st.toggle(
            "Tacos på fredag när barnen är hemma",
            value=st.session_state.taco
        )
        st.session_state.budget = st.number_input(
            "Veckobudget", 500, 3000, st.session_state.budget, 100
        )

    elif section == "Nedröstade recept":
        if st.session_state.disliked_recipes:
            for name in st.session_state.disliked_recipes:
                with st.container(border=True):
                    st.write(f"👎 **{name}**")
            if st.button("Återställ alla", type="primary"):
                st.session_state.disliked_recipes = []
                st.rerun()
        else:
            st.markdown('<div class="empty">Du har inte röstat ner några recept.</div>', unsafe_allow_html=True)

    else:
        st.write("**Matappen v12**")
        st.caption("Byggd för mobil först.")
        if st.button("Logga ut", type="primary"):
            st.session_state["authenticated"] = False
            st.rerun()
