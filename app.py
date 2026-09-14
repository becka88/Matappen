
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
st.markdown('<div class="matappen-eyebrow">Familjens matplanering</div>', unsafe_allow_html=True)
st.markdown('<div class="matappen-hero">Matappen</div>', unsafe_allow_html=True)
st.markdown('<div class="matappen-subtle">Veckomat, handling och fryskoll — utan onödigt admin.</div>', unsafe_allow_html=True)

# Live ICA data (cached for six hours; refreshable in Handla)
ica_data = get_current_ica_offers()
live_offers = ica_data.get("offers", [])

# Build plan dynamically
used = set()
plan = []
for i, d in enumerate(DAYS):
    kh = kids_here(i, st.session_state.kids_arrive)
    r = choose_recipe(i, kh, st.session_state.taco and kh, used, live_offers)
    used.add(r["name"])
    plan.append({
        "day": d,
        "kids": kh,
        "recipe": r,
        "portions": portions(kh, st.session_state.lunchboxes),
        "offer": offer_for_recipe(r, live_offers),
    })

tabs = st.tabs(["🍽 Idag", "📅 Vecka", "🛒 Handla", "📖 Recept", "••• Mer"])

# ---------- IDAG ----------
with tabs[0]:
    today_idx = min(date.today().weekday(), 6)
    p = plan[today_idx]

    st.write("")
    with st.container(border=True):
        st.markdown(f'<div class="matappen-eyebrow">{p["day"]} · {"Barnen hemma" if p["kids"] else "Vuxenkväll"}</div>', unsafe_allow_html=True)
        st.markdown(f"## {p['recipe']['name']}")
        st.markdown(
            f'<span class="matappen-chip">⏱ {p["recipe"]["mins"]} min</span>'
            f'<span class="matappen-chip">🍽 {p["portions"]} portioner</span>'
            f'<span class="matappen-chip">🥡 Matlåda {p["recipe"]["lunch"]}/5</span>',
            unsafe_allow_html=True,
        )
        if p.get("offer"):
            st.success(f"🔥 ICA-match: {p['offer'].get('name')} — {p['offer'].get('offer')}")
        with st.expander("Visa recept"):
            st.write("**Ingredienser**")
            for k, v in p["recipe"]["ings"].items():
                st.write(f"• {k}: {v}")
            st.write("**Gör så här**")
            for n, s in enumerate(p["recipe"]["steps"], 1):
                st.write(f"{n}. {s}")

    st.write("")
    st.markdown("### Snabbt att göra")
    cols = st.columns(3)
    quick_home = ["Mjölk", "Bröd", "Ägg"]
    for i, item in enumerate(quick_home):
        if cols[i].button(f"+ {item}", key=f"homequick_{item}"):
            if item not in st.session_state.snabblista:
                st.session_state.snabblista.append(item)
            st.rerun()

    st.write("")
    st.markdown("### Läget hemma")
    level_score = {"Fullt": 3, "Okej": 2, "Börjar ta slut": 1, "Slut": 0}
    mellis_status = min(
        st.session_state.freezer_levels.values(),
        key=lambda x: level_score.get(x, 0),
    ) if st.session_state.freezer_levels else "Okej"

    a, b = st.columns(2)
    a.metric("Mellis", mellis_status)
    b.metric("Snabblista", f"{len(st.session_state.snabblista)} varor")
    st.caption(f"❄️ {st.session_state.freezer_exact.get('Middagsportioner', 0)} färdiga middagsportioner i frysen")

    if any(v in ["Börjar ta slut", "Slut"] for v in st.session_state.freezer_levels.values()):
        st.warning("Mellis börjar ta slut. Kolla Recept → Mellis när ni vill fylla på.")

# ---------- VECKAN ----------
with tabs[1]:
    st.markdown("### Veckans middagar")
    st.caption("Barnveckan skiftar automatiskt på torsdag.")

    for p in plan:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.markdown(f"**{p['day']}**")
                st.markdown(f"### {p['recipe']['name']}")
                st.markdown(
                    f'<span class="matappen-chip">{"👨‍👩‍👧‍👦 Barnen hemma" if p["kids"] else "🌙 Vuxenkväll"}</span>'
                    f'<span class="matappen-chip">⏱ {p["recipe"]["mins"]} min</span>'
                    f'<span class="matappen-chip">🍽 {p["portions"]} port</span>',
                    unsafe_allow_html=True,
                )
            with right:
                if p.get("offer"):
                    st.markdown("🔥 **ICA**")

            with st.expander("Recept & ingredienser"):
                if p.get("offer"):
                    st.success(f"ICA just nu: {p['offer'].get('name')} — {p['offer'].get('offer')}")
                st.write("**Ingredienser**")
                for k, v in p["recipe"]["ings"].items():
                    st.write(f"• {k}: {v}")
                st.write("**Gör så här**")
                for n, s in enumerate(p["recipe"]["steps"], 1):
                    st.write(f"{n}. {s}")
                st.caption(f"Matlåda {p['recipe']['lunch']}/5 · Frys {p['recipe']['freeze']}/5")

# ---------- HANDLA ----------
with tabs[2]:
    shop_view = st.segmented_control(
        "Handla",
        ["Inköpslista", "Snabblista", "ICA-erbjudanden"],
        default="Inköpslista",
        label_visibility="collapsed",
    )

    if shop_view == "Inköpslista":
        st.markdown("### Inköpslistan")
        st.caption("Veckans recept och Snabblistan är redan sammanslagna.")

        agg = Counter()
        for p in plan:
            for ing in p["recipe"]["ings"]:
                agg[ing] += 1

        quick = [x.strip() for x in st.session_state.snabblista if x.strip()]
        merged = set(agg.keys()) | set(quick)

        def category(item):
            x = item.lower()
            if any(k in x for k in ["mjölk", "yoghurt", "ost", "grädde", "ägg"]): return "Mejeri"
            if any(k in x for k in ["kyckling", "färs", "korv", "fläsk", "högrev", "skinka"]): return "Kött & chark"
            if any(k in x for k in ["potatis", "morot", "lök", "sallad", "broccoli", "banan", "chili"]): return "Frukt & grönt"
            if any(k in x for k in ["diskmedel", "toapapper", "hushåll", "tvätt"]): return "Hushåll"
            return "Skafferi / övrigt"

        rows = []
        for ing in sorted(merged, key=lambda x: (category(x), x.lower())):
            src = []
            if ing in agg: src.append(f"{agg[ing]} rätter")
            if ing in quick: src.append("Snabb")
            offer_hit = next(
                (o for o in live_offers if ing.lower() in (o.get("name", "") + " " + o.get("query", "")).lower()),
                None,
            )
            rows.append({
                "✓": False,
                "Avdelning": category(ing),
                "Vara": ing,
                "Från": " + ".join(src),
                "ICA": ("🔥 " + offer_hit.get("offer", "")) if offer_hit else "",
            })

        edited = st.data_editor(
            rows,
            hide_index=True,
            use_container_width=True,
            height=min(580, 42 + len(rows) * 35),
            column_config={"✓": st.column_config.CheckboxColumn("✓")},
            disabled=["Avdelning", "Vara", "Från", "ICA"],
        )

        if st.button("Rensa avbockade", type="primary"):
            checked = [r["Vara"] for r in edited if r.get("✓")]
            st.session_state.snabblista = [x for x in st.session_state.snabblista if x not in checked]
            st.rerun()

        sio = io.StringIO()
        w = csv.DictWriter(sio, fieldnames=["Avdelning", "Vara", "Från", "ICA"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in ["Avdelning", "Vara", "Från", "ICA"]})
        st.download_button("Spara listan som CSV", sio.getvalue(), "inkopslista.csv", "text/csv")

    elif shop_view == "Snabblista":
        st.markdown("### Lägg till på vägen")
        st.caption("För sådant någon märker håller på att ta slut.")

        cols = st.columns(3)
        for i, item in enumerate(st.session_state.common_items):
            if cols[i % 3].button(f"+ {item}", key=f"quick_{item}"):
                if item not in st.session_state.snabblista:
                    st.session_state.snabblista.append(item)
                st.rerun()

        with st.form("add_quick_item", clear_on_submit=True):
            new_item = st.text_input("Annan vara", placeholder="Kaffe, tandkräm, ketchup …")
            if st.form_submit_button("Lägg till"):
                val = new_item.strip()
                if val and val not in st.session_state.snabblista:
                    st.session_state.snabblista.append(val)
                    st.rerun()

        if st.session_state.snabblista:
            st.markdown("#### På Snabblistan")
            for i, item in enumerate(list(st.session_state.snabblista)):
                with st.container(border=True):
                    a, b = st.columns([5, 1])
                    a.write(f"**{item}**")
                    if b.button("×", key=f"rm_{i}_{item}", help="Ta bort"):
                        st.session_state.snabblista.remove(item)
                        st.rerun()
        else:
            st.success("Snabblistan är tom.")

    else:
        st.markdown("### ICA Maxi Växjö")
        a, b = st.columns(2)
        a.metric("Status", ica_data["status"])
        b.metric("Verifierade träffar", len(live_offers))
        st.caption(f"Kontrollerad butik: {ica_data['store']} · Vecka {ica_data['week']}")

        if st.button("Hämta ICA igen"):
            get_current_ica_offers.clear()
            st.rerun()

        if ica_data.get("errors"):
            st.warning("ICA kunde inte läsas fullt ut från alla källor. Matappen visar bara det som kunnat verifieras.")

        meat, other = [], []
        for o in live_offers:
            txt = (o.get("name", "") + " " + o.get("query", "")).lower()
            (meat if any(t in txt for t in MEAT_TERMS) else other).append(o)

        if meat:
            st.markdown("#### Kött, kyckling & chark")
            for o in meat[:30]:
                with st.container(border=True):
                    st.write(f"**{o.get('name', 'Vara')}**")
                    st.markdown(f'<div class="matappen-price">🔥 {o.get("offer", "Erbjudande")}</div>', unsafe_allow_html=True)
                    st.caption(o.get("source", "ICA"))
        else:
            st.info("Inga kötterbjudanden kunde verifieras just nu.")

        with st.expander("Övriga erbjudanden"):
            for o in other[:40]:
                st.write(f"**{o.get('name','Vara')}** — {o.get('offer','Erbjudande')}")

# ---------- RECEPT ----------
with tabs[3]:
    recipe_type = st.segmented_control(
        "Typ",
        ["Middag", "Mellis", "Alla"],
        default="Middag",
        label_visibility="collapsed",
    )
    q = st.text_input("Sök", placeholder="Sök recept eller ingrediens", label_visibility="collapsed")
    recipe_filter = st.radio(
        "Filter",
        ["Alla", "Snabbt", "Barnvänligt", "Matlåda", "Frys", "Vuxen"],
        horizontal=True,
        label_visibility="collapsed",
    )

    filtered = []
    for r in RECIPES:
        if recipe_type != "Alla" and r["cat"] != recipe_type:
            continue
        if recipe_filter == "Snabbt" and r["mins"] > 30:
            continue
        if recipe_filter == "Barnvänligt" and "barnvänlig" not in r["tags"]:
            continue
        if recipe_filter == "Matlåda" and r["lunch"] < 4:
            continue
        if recipe_filter == "Frys" and r["freeze"] < 4:
            continue
        if recipe_filter == "Vuxen" and "vuxen" not in r["tags"]:
            continue
        hay = (r["name"] + " " + " ".join(r["ings"].keys()) + " " + " ".join(r["tags"])).lower()
        if q.lower() not in hay:
            continue
        filtered.append(r)

    if recipe_type == "Mellis":
        priority = {"Slut": 0, "Börjar ta slut": 1, "Okej": 2, "Fullt": 3}
        low = sorted(st.session_state.freezer_levels.items(), key=lambda x: priority.get(x[1], 9))
        if low and low[0][1] in ["Slut", "Börjar ta slut"]:
            st.info(f"Bra nästa sats: **{low[0][0]}** · nivån är {low[0][1]}.")

    for r in filtered:
        with st.container(border=True):
            st.markdown(f"### {r['name']}")
            tags = "".join(f'<span class="matappen-chip">{tag}</span>' for tag in r["tags"][:4])
            st.markdown(
                f'<span class="matappen-chip">⏱ {r["mins"]} min</span>'
                f'<span class="matappen-chip">❄️ {r["freeze"]}/5</span>{tags}',
                unsafe_allow_html=True,
            )
            with st.expander("Öppna recept"):
                st.write("**Ingredienser**")
                for k, v in r["ings"].items():
                    st.write(f"• {k}: {v}")
                st.write("**Gör så här**")
                for i, s in enumerate(r["steps"], 1):
                    st.write(f"{i}. {s}")
                if r["cat"] == "Mellis":
                    st.info("Frys portionsvis eller styckvis och märk gärna med namn och datum.")
                rating = st.select_slider(
                    "Familjens betyg",
                    ["👎", "😐", "👍", "❤️"],
                    value=st.session_state.ratings.get(r["name"], "👍"),
                    key="rate_" + r["name"],
                )
                st.session_state.ratings[r["name"]] = rating

# ---------- MER ----------
with tabs[4]:
    more_view = st.segmented_control(
        "Mer",
        ["Frysen", "Familjen", "Om appen"],
        default="Frysen",
        label_visibility="collapsed",
    )

    if more_view == "Frysen":
        st.markdown("### Fryskoll")
        st.caption("Mellis ungefärligt. Middagsportioner och köttpaket exakt.")

        st.markdown("#### Mellis")
        nivåer = ["Fullt", "Okej", "Börjar ta slut", "Slut"]
        for item in list(st.session_state.freezer_levels):
            current = st.session_state.freezer_levels[item]
            st.session_state.freezer_levels[item] = st.selectbox(
                item, nivåer, index=nivåer.index(current), key="lvl_" + item
            )

        st.markdown("#### Exakt lager")
        for item in list(st.session_state.freezer_exact):
            st.session_state.freezer_exact[item] = st.number_input(
                item, 0, 100, int(st.session_state.freezer_exact[item]), 1, key="exact_" + item
            )

    elif more_view == "Familjen":
        st.markdown("### Familjen")
        st.session_state.kids_arrive = st.radio(
            "Vad händer på torsdag?",
            ["Barnen kommer", "Barnen åker"],
            index=0 if st.session_state.kids_arrive else 1,
            horizontal=True,
        ) == "Barnen kommer"

        st.session_state.lunchboxes = st.slider(
            "Matlådor efter en vanlig middag",
            0, 4, st.session_state.lunchboxes
        )
        st.session_state.taco = st.checkbox(
            "Tacos på fredag när barnen är hemma",
            st.session_state.taco
        )
        st.session_state.budget = st.number_input(
            "Målbudget per vecka",
            500, 3000, st.session_state.budget, 100
        )
        st.caption("När barnen inte är hemma prioriteras friare vuxenmat. Matlådorna räknas ändå med.")

    else:
        st.markdown("### Matappen v9")
        st.write("En privat familjeapp för veckomat, handling, mellis, recept och fryskoll.")
        st.write("ICA-data markeras bara som verifierad när Matappen faktiskt kan läsa den från butikens publika källor.")
        if st.button("Logga ut"):
            st.session_state["authenticated"] = False
            st.rerun()

st.write("")
st.caption("Matappen v9 · privat familjeapp")
