import json, re, hashlib, time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recipes.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MatappenRecipeIndexer/2.0; personal family meal planner)",
    "Accept-Language": "sv-SE,sv;q=0.9",
}
TIMEOUT = 20

SOURCES = {
    "ICA": {
        "hosts": {"www.ica.se", "ica.se"},
        "seeds": [
            "https://www.ica.se/recept/vardag/",
            "https://www.ica.se/recept/middag/",
            "https://www.ica.se/recept/kyckling/",
            "https://www.ica.se/recept/kottfars/",
            "https://www.ica.se/recept/lax/",
            "https://www.ica.se/recept/torsk/",
            "https://www.ica.se/recept/pasta/",
            "https://www.ica.se/recept/korv/",
            "https://www.ica.se/recept/vegetariskt/",
            "https://www.ica.se/recept/soppa/",
            "https://www.ica.se/recept/gryta/",
            "https://www.ica.se/recept/under-30-minuter/",
        ],
    },
    "Arla": {
        "hosts": {"www.arla.se", "arla.se"},
        "seeds": [
            "https://www.arla.se/recept/samling/kyckling/",
            "https://www.arla.se/recept/samling/kyckling-vardag/",
            "https://www.arla.se/recept/samling/snabb-kyckling/",
            "https://www.arla.se/recept/samling/vardag-pasta/",
            "https://www.arla.se/recept/samling/kottfars-vardag/",
            "https://www.arla.se/recept/samling/lax-vardag/",
            "https://www.arla.se/recept/samling/fisk-vardag/",
            "https://www.arla.se/recept/samling/vegetarisk-vardag/",
        ],
    },
    "Köket": {
        "hosts": {"www.koket.se", "koket.se"},
        "seeds": [
            "https://www.koket.se/recept",
            "https://www.koket.se/vardag",
            "https://www.koket.se/kyckling",
            "https://www.koket.se/lax",
            "https://www.koket.se/pasta",
            "https://www.koket.se/torsk",
            "https://www.koket.se/korv",
            "https://www.koket.se/vegetariskt",
        ],
    },
}

session = requests.Session()
session.headers.update(HEADERS)

def get(url):
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def minutes(value):
    if not value:
        return None
    s = str(value)
    h = re.search(r"(\d+)H", s)
    m = re.search(r"(\d+)M", s)
    if s.startswith("PT"):
        return (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)
    nums = re.findall(r"\d+", s)
    return int(nums[0]) if nums else None

def recipe_yield(value):
    if isinstance(value, list):
        value = value[0] if value else None
    n = re.search(r"\d+", str(value or ""))
    return int(n.group()) if n else None

def image_url(value, base):
    candidates = []
    if isinstance(value, str):
        candidates.append(value)
    elif isinstance(value, list):
        for x in value:
            if isinstance(x, str):
                candidates.append(x)
            elif isinstance(x, dict) and x.get("url"):
                candidates.append(x["url"])
    elif isinstance(value, dict) and value.get("url"):
        candidates.append(value["url"])
    for u in candidates:
        u = urljoin(base, str(u))
        if u.startswith("http") and not any(x in u.lower() for x in ("logo", "icon", "avatar")):
            return u
    return None

def source_url_ok(source, url):
    try:
        host = urlparse(url).netloc.lower()
        return host in SOURCES[source]["hosts"]
    except Exception:
        return False

def tags_for(name, ingredients):
    text = (name + " " + " ".join(ingredients)).lower()
    rules = {
        "kyckling": ["kyckling"],
        "kött": ["kött", "färs", "fläsk", "biff", "korv"],
        "pasta": ["pasta", "spaghetti", "lasagne", "makaron", "penne"],
        "gryta": ["gryta", "stroganoff", "chili"],
        "fredag": ["taco", "burrito", "quesadilla", "pizza"],
        "vegetariskt": ["vegetar", "linser", "bönor", "tofu", "halloumi"],
    }
    return [tag for tag, words in rules.items() if any(w in text for w in words)]

def normalize(obj, source, page_url, fallback_image=None):
    name = clean(obj.get("name") or obj.get("headline"))
    ingredients = obj.get("recipeIngredient") or []
    if not isinstance(ingredients, list):
        return None
    ingredients = [clean(x) for x in ingredients if clean(x)]

    # A Matappen catalog recipe must be a real source recipe with its actual ingredient list.
    if len(name) < 3 or len(ingredients) < 2:
        return None

    raw_url = obj.get("url") or obj.get("mainEntityOfPage") or page_url
    if isinstance(raw_url, dict):
        raw_url = raw_url.get("@id") or raw_url.get("url") or page_url
    url = urljoin(page_url, str(raw_url))
    if not source_url_ok(source, url):
        url = page_url
    if not source_url_ok(source, url):
        return None

    img = image_url(obj.get("image"), page_url) or fallback_image

    return {
        "id": hashlib.sha1(url.encode("utf-8")).hexdigest()[:20],
        "name": name,
        "source": source,
        "url": url,
        "minutes": minutes(obj.get("totalTime") or obj.get("cookTime") or obj.get("prepTime")),
        "portions": recipe_yield(obj.get("recipeYield")),
        "ingredients": ingredients,
        "image": img,
        "tags": tags_for(name, ingredients),
        "external": True,
    }

def walk_json(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            if isinstance(v, (dict, list)):
                yield from walk_json(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk_json(v)

def parse_recipe_page(html, source, page_url):
    soup = BeautifulSoup(html, "html.parser")
    og = (
        soup.find("meta", property="og:image")
        or soup.find("meta", attrs={"name": "twitter:image"})
        or soup.find("meta", property="twitter:image")
    )
    fallback_image = urljoin(page_url, og.get("content")) if og and og.get("content") else None

    found = []
    for script in soup.find_all("script", type=re.compile(r"ld\+json", re.I)):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        for obj in walk_json(data):
            typ = obj.get("@type")
            types = typ if isinstance(typ, list) else [typ]
            if "Recipe" not in types:
                continue
            r = normalize(obj, source, page_url, fallback_image)
            if r:
                found.append(r)
    return found

def looks_like_recipe_link(source, url):
    p = urlparse(url).path.lower().rstrip("/")
    if source == "ICA":
        return p.startswith("/recept/") and len([x for x in p.split("/") if x]) >= 2
    if source == "Arla":
        return p.startswith("/recept/") and "/samling/" not in p
    if source == "Köket":
        # Köket recipe pages are validated later by Recipe JSON-LD.
        bad = ("/mat/", "/artiklar/", "/program/", "/tv/", "/nyheter/", "/populara-recept")
        return p.count("/") >= 1 and not any(x in p for x in bad)
    return False

def discover_links(html, base, source):
    soup = BeautifulSoup(html, "html.parser")
    allowed = SOURCES[source]["hosts"]
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        url = urljoin(base, a["href"].split("#")[0])
        if urlparse(url).netloc.lower() not in allowed:
            continue
        if not looks_like_recipe_link(source, url):
            continue
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out[:700]

# Preserve only previously verified external recipes from the three approved sources.
old = []
if OUT.exists():
    try:
        old = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        old = []

by_url = {}
for r in old if isinstance(old, list) else []:
    if (
        r.get("external") is True
        and r.get("source") in SOURCES
        and source_url_ok(r["source"], r.get("url", ""))
        and isinstance(r.get("ingredients"), list)
        and len(r["ingredients"]) >= 2
    ):
        by_url[r["url"]] = r

candidates = []
seed_ok = 0

for source, cfg in SOURCES.items():
    for seed in cfg["seeds"]:
        try:
            html = get(seed)
            seed_ok += 1

            # Some collection pages themselves can contain Recipe JSON-LD.
            for r in parse_recipe_page(html, source, seed):
                by_url[r["url"]] = r

            candidates.extend((source, u) for u in discover_links(html, seed, source))
        except Exception as e:
            print("SEED_FAIL", source, seed, type(e).__name__)

# Prioritize unique links and cap runtime.
seen = set()
unique = []
for source, url in candidates:
    if url in seen:
        continue
    seen.add(url)
    unique.append((source, url))

parsed_pages = 0
for source, url in unique[:3000]:
    try:
        recipes = parse_recipe_page(get(url), source, url)
        if recipes:
            parsed_pages += 1
        for r in recipes:
            by_url[r["url"]] = r
    except Exception:
        pass
    time.sleep(0.02)

recipes = sorted(
    by_url.values(),
    key=lambda r: (r.get("source", ""), r.get("name", "").lower()),
)

# Never put Matappen-generated/fallback recipes into recipes.json.
recipes = [
    r for r in recipes
    if r.get("external") is True
    and r.get("source") in SOURCES
    and source_url_ok(r["source"], r.get("url", ""))
    and len(r.get("ingredients") or []) >= 2
]

OUT.write_text(json.dumps(recipes, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    f"Saved {len(recipes)} verified source recipes "
    f"(seed_ok={seed_ok}, recipe_pages={parsed_pages}). "
    "Sources: ICA, Arla, Köket only."
)
