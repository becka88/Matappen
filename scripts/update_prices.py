import json, re, time, datetime, concurrent.futures
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "prices.json"
REC = ROOT / "recipes.json"

STORE = "1003571"
STORE_NAME = "Maxi ICA Stormarknad Växjö"
URL = f"https://handlaprivatkund.ica.se/stores/{STORE}/api/webproductpagews/v6/product-pages/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "sv-SE,sv;q=0.9",
    "Referer": f"https://handlaprivatkund.ica.se/stores/{STORE}",
}

REQUEST_TIMEOUT = 20
MAX_TERMS = 45
MAX_WORKERS = 5
MAX_PRODUCTS_PER_TERM = 30
MAX_202_RETRIES = 30
MAX_RUNTIME_SECONDS = 225

def clean(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()

def canon(x):
    return clean(x).lower().replace("é", "e")

def num(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = re.search(r"\d+(?:[.,]\d+)?", v)
        return float(m.group().replace(",", ".")) if m else None
    if isinstance(v, dict):
        # Vanliga prisformer: {"amount":"23.50"}, {"value":23.5}, {"price":...}
        for k in ("amount", "value", "price", "current", "currentPrice", "salesPrice"):
            if k in v:
                n = num(v[k])
                if n is not None:
                    return n
        # Sista utväg: leta rekursivt efter ett numeriskt värde.
        for vv in v.values():
            n = num(vv)
            if n is not None:
                return n
    return None

def deep_get_first(d, keys):
    if isinstance(d, dict):
        for k in keys:
            if k in d and d[k] not in (None, ""):
                return d[k]
        for v in d.values():
            if isinstance(v, (dict, list)):
                hit = deep_get_first(v, keys)
                if hit not in (None, ""):
                    return hit
    elif isinstance(d, list):
        for v in d:
            hit = deep_get_first(v, keys)
            if hit not in (None, ""):
                return hit
    return None

def ingredient_term(line):
    s = canon(line)
    s = re.sub(r"^\d+(?:[.,/]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*", "", s)
    s = re.sub(r"^(kg|g|mg|l|dl|cl|ml|msk|tsk|krm|st|stycken|förp|burk|påse|paket)\s+", "", s)
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.split(r",| till | efter smak| gärna| valfri", s)[0].strip()
    aliases = {
        "äggula":"ägg", "äggulor":"ägg",
        "vitlöksklyfta":"vitlök", "vitlöksklyftor":"vitlök",
        "morötter":"morot", "lökar":"lök",
        "gul lök":"lök", "röd lök":"lök",
    }
    return aliases.get(s, s)

STAPLES = [
    "mjölk","ägg","smör","grädde","crème fraiche","pasta","ris","potatis","lök","vitlök",
    "vetemjöl","socker","rapsolja","olivolja","köttfärs","nötfärs","kyckling","kycklingfilé",
    "lax","torsk","falukorv","korv","krossade tomater","kokosmjölk","yoghurt","bröd","ost",
    "morot","bönor","paprika","gurka","tomat","champinjoner","bacon","skinka","tortilla",
    "havregryn","buljong","soja","senap","ketchup","majonnäs","citron","banan","salt","svartpeppar","peppar","paprikapulver","curry","oregano","timjan","kanel"
]

def product_groups(payload):
    # ICA kan returnera direkt eller inuti "data" och har ändrat formen över tid.
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        payload = payload["data"]
    groups = payload.get("productGroups", []) if isinstance(payload, dict) else []
    if isinstance(groups, list):
        return groups
    if isinstance(groups, dict):
        # Acceptera både {items:[...]} och grupper uppdelade per nyckel.
        for key in ("items", "groups", "results", "productGroups"):
            if isinstance(groups.get(key), list):
                return groups[key]
        return [v for v in groups.values() if isinstance(v, dict)]
    return []

def decorated_products(payload):
    # Leta rekursivt efter decoratedProducts. Det gör parsern tålig om ICA
    # lägger ett extra lager runt grupperna utan att prisinhämtningen går sönder.
    out = []
    seen = set()

    def add_rows(rows):
        # ICA:s decoratedProducts kan vara antingen en lista eller en dictionary/map
        # (t.ex. grupperad per viewport/id). Tidigare kastade vi bort dictionary-formen
        # om den saknade nyckeln items/products/results, vilket gav 0 produkter trots HTTP 200.
        if isinstance(rows, list):
            for row in rows:
                add_rows(row)
            return
        if not isinstance(rows, dict):
            return

        # En faktisk produkt har normalt ett namn/id och ett pris någonstans i objektet.
        # Lägg till den, men fortsätt även nedåt så wrappers/maps fungerar.
        has_identity = any(k in rows for k in ("name","productName","displayName","title","retailerProductId","productId","sku"))
        has_price = any(k in rows for k in ("price","currentPrice","salesPrice","displayPrice"))
        if has_identity and has_price:
            marker = id(rows)
            if marker not in seen:
                seen.add(marker)
                out.append(rows)

        # Kända wrappers först, därefter alla övriga värden. Detta täcker både
        # {items:[...]}, {products:[...]} och {<id>:{...produkt...}}.
        handled = set()
        for key in ("items","products","results","decoratedProducts","product","decoratedProduct"):
            if key in rows:
                handled.add(key)
                add_rows(rows[key])
        for key, value in rows.items():
            if key not in handled and isinstance(value, (dict, list)):
                add_rows(value)

    def walk(node):
        if isinstance(node, dict):
            if "decoratedProducts" in node:
                add_rows(node.get("decoratedProducts"))
            # Äldre/alternativ form där gruppen bara heter products.
            if "products" in node and any(k in node for k in ("type", "name", "productGroupType")):
                add_rows(node.get("products"))
            for v in node.values():
                if isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(payload)
    return out

def promo_info(x):
    promos = x.get("promotions") if isinstance(x, dict) else None
    text = clean(deep_get_first(x, ("promotionText","offerText")))
    promo_price = num(deep_get_first(x, ("promotionPrice","promotionalPrice")))
    if isinstance(promos, list) and promos:
        p = promos[0]
        if isinstance(p, dict):
            text = text or clean(deep_get_first(p, ("description","name","text","promotionText")))
            promo_price = promo_price or num(deep_get_first(p, ("price","promotionPrice","promotionalPrice","amount")))
    return text, promo_price

def normalize_product(x, q):
    if not isinstance(x, dict):
        return None

    name = clean(deep_get_first(x, ("name","productName","displayName","title")))
    price_raw = deep_get_first(x, ("price","currentPrice","salesPrice","displayPrice"))
    price = num(price_raw)

    if not name or price is None or price <= 0:
        return None

    promo, promo_price = promo_info(x)
    pid = clean(deep_get_first(x, ("retailerProductId","productId","id","sku")))
    brand = clean(deep_get_first(x, ("brand","brandName")))
    pack = clean(deep_get_first(x, ("packSizeDescription","unitOfMeasure","packageSize","size")))
    unit_price = clean(deep_get_first(x, ("unitPrice","comparisonPrice")))
    available = deep_get_first(x, ("available","inStock"))

    return {
        "query": q,
        "name": name,
        "brand": brand,
        "price": round(price, 2),
        "promotion_price": round(promo_price, 2) if promo_price else None,
        "pack": pack,
        "unit_price": unit_price,
        "promotion": promo,
        "product_id": pid,
        "available": available,
    }

def fetch_term(q):
    session = requests.Session()
    session.headers.update(HEADERS)
    statuses = []
    last_keys = []

    for attempt in range(MAX_202_RETRIES):
        if time.monotonic() - STARTED > MAX_RUNTIME_SECONDS:
            return q, [], "runtime", statuses, last_keys

        try:
            r = session.get(
                URL,
                params={"q": q, "tag": "web", "maxPageSize": MAX_PRODUCTS_PER_TERM},
                timeout=REQUEST_TIMEOUT,
            )
            statuses.append(r.status_code)

            # ICA:s sök-API svarar ofta 202 först. Det betyder "försök igen".
            if r.status_code == 202:
                retry_after = r.headers.get("Retry-After")
                try:
                    wait = float(retry_after) if retry_after else min(1.0 + attempt * 1.0, 10.0)
                except Exception:
                    wait = min(1.0 + attempt * 1.0, 10.0)
                time.sleep(wait)
                continue

            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(1.2 + attempt, 5.0))
                continue

            r.raise_for_status()
            payload = r.json()

            if isinstance(payload, dict):
                probe = payload.get("data") if isinstance(payload.get("data"), dict) else payload
                if isinstance(probe, dict):
                    last_keys = sorted(probe.keys())[:20]

            rows = []
            for x in decorated_products(payload):
                p = normalize_product(x, q)
                if p:
                    rows.append(p)

            # 200 med riktiga grupper men inga tolkade produkter: rapportera parserfel.
            raw_count = len(decorated_products(payload))
            if raw_count and not rows:
                return q, [], f"parser:{raw_count}", statuses, last_keys
            if not raw_count and product_groups(payload):
                # 200 + productGroups men noll hittade produkter är också parserfel,
                # inte en lyckad tom sökning. Då syns det tydligt i Action-loggen.
                g = product_groups(payload)[0]
                gkeys = sorted(g.keys())[:20] if isinstance(g, dict) else [type(g).__name__]
                return q, [], "parser-groups:" + ",".join(gkeys), statuses, last_keys

            return q, rows, None, statuses, last_keys

        except requests.RequestException as e:
            if attempt < MAX_202_RETRIES - 1:
                time.sleep(min(1.0 + attempt, 4.0))
                continue
            return q, [], type(e).__name__, statuses, last_keys
        except Exception as e:
            return q, [], type(e).__name__, statuses, last_keys

    return q, [], "202-timeout", statuses, last_keys

# Sök först efter ingredienser som faktiskt finns i receptbanken.
recipe_terms = []
try:
    raw = json.loads(REC.read_text(encoding="utf-8"))
    recipes = raw if isinstance(raw, list) else raw.get("recipes", [])
    for r in recipes:
        for x in r.get("ingredients", []) or []:
            q = ingredient_term(x)
            if 2 <= len(q) <= 40 and "vatten" not in q and q not in {"salt","peppar","salt och peppar"}:
                recipe_terms.append(q)
except Exception:
    pass

# Blanda in basvaror så vanliga manuellt tillagda varor också får pris.
recipe_terms = list(dict.fromkeys(recipe_terms))
terms = []
for i in range(max(len(recipe_terms), len(STAPLES))):
    if i < len(recipe_terms): terms.append(recipe_terms[i])
    if i < len(STAPLES): terms.append(STAPLES[i])
terms = list(dict.fromkeys(terms))[:MAX_TERMS]

# Läs gamla riktiga priser så en tillfällig ICA-störning inte tömmer databasen.
old_products = []
old_updated_at = None
try:
    old = json.loads(OUT.read_text(encoding="utf-8"))
    if isinstance(old, dict):
        old_products = old.get("products") or []
        old_updated_at = old.get("updated_at")
except Exception:
    pass

STARTED = time.monotonic()
rows = {}
ok = 0
failed = 0
status_hist = {}
parser_errors = []
sample_keys = []
sample_shape = []

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futures = {ex.submit(fetch_term, q): q for q in terms}
    for fut in concurrent.futures.as_completed(futures):
        if time.monotonic() - STARTED > MAX_RUNTIME_SECONDS:
            break

        q, items, err, statuses, keys = fut.result()
        for st in statuses:
            status_hist[str(st)] = status_hist.get(str(st), 0) + 1
        if keys and not sample_keys:
            sample_keys = keys

        if err:
            failed += 1
            if str(err).startswith("parser"):
                parser_errors.append(f"{q}:{err}")
            continue

        ok += 1
        for x in items:
            key = (x["product_id"] or (x["name"] + "|" + str(x["price"]))).lower()
            if key not in rows:
                x["queries"] = [q]
                x.pop("query", None)
                rows[key] = x
            elif q not in rows[key]["queries"]:
                rows[key]["queries"].append(q)

fresh_products = list(rows.values())

if fresh_products:
    products_out = fresh_products
    status = "live"
    updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
else:
    # Behåll tidigare äkta priser om ICA tillfälligt inte svarar.
    products_out = old_products
    status = "live" if old_products else "unavailable"
    updated_at = old_updated_at

result = {
    "store_id": STORE,
    "store": STORE_NAME,
    "updated_at": updated_at,
    "status": status,
    "queries_ok": ok,
    "queries_failed": failed,
    "products": products_out,
}

OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

elapsed = round(time.monotonic() - STARTED, 1)
print(
    f"ICA prices status={status} fresh_products={len(fresh_products)} "
    f"stored_products={len(products_out)} queries_ok={ok} failed={failed} "
    f"http={status_hist} elapsed={elapsed}s"
)
if parser_errors:
    print("PARSER_DIAGNOSTIC", "; ".join(parser_errors[:5]))
if sample_keys:
    print("ICA_RESPONSE_KEYS", ",".join(sample_keys))
