"""research.py - one dossier per company, free sources first.

    python research.py [--leads leads.csv] [--max 20]

Sources, in this order:
  website pages    crawl4ai if installed, else plain HTTP with tags stripped                       free
  website retry    Firecrawl, only when FIRECRAWL_API_KEY is set and the free fetch got nothing    ~1 credit / page
  own words        notes/<domain>.md that you paste yourself (dated items only)                    free
  LinkedIn posts   Apify, only when APIFY_TOKEN is set and the lead has a linkedin_url             ~$0.002 / post

A page that could not be read is recorded as "could not read", never as evidence that something is missing.
Writes runs/<run>/dossiers/<domain>.json. Re-running skips companies that already have a dossier.
"""
import argparse, asyncio, csv, datetime, html, json, re, urllib.request

from lib import ROOT, config, env, load_env, run_dir

PATHS = ["", "/about", "/pricing", "/news", "/blog"]
MAX_CHARS = 3000
MIN_CHARS = 200
UA = {"User-Agent": "Mozilla/5.0 (research-first-outreach)"}


def clean(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text or "")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def http_text(url):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8", "ignore")
    except Exception:
        return ""
    raw = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", raw)
    return clean(html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw)))


async def crawl4ai_texts(urls):
    from crawl4ai import AsyncWebCrawler
    out = {}
    async with AsyncWebCrawler(verbose=False) as c:
        for u in urls:
            try:
                r = await c.arun(url=u, page_timeout=15000)
                out[u] = clean(str(getattr(r, "markdown", "") or ""))
            except Exception:
                out[u] = ""
    return out


def firecrawl_text(url):
    key = env("FIRECRAWL_API_KEY")
    if not key:
        return ""
    body = json.dumps({"url": url, "formats": ["markdown"], "onlyMainContent": True}).encode()
    req = urllib.request.Request("https://api.firecrawl.dev/v1/scrape", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("data") or {}
        return clean(d.get("markdown") or "")
    except Exception:
        return ""


def site(domain):
    urls = [f"https://{domain}{p}" for p in PATHS]
    try:
        texts = asyncio.run(crawl4ai_texts(urls))
        tool = "crawl4ai"
    except ImportError:
        texts, tool = {u: http_text(u) for u in urls}, "http"
    pages = {}
    for p, u in zip(PATHS, urls):
        t, used = texts.get(u, ""), tool
        if len(t) < MIN_CHARS and p in ("", "/pricing"):
            t2 = firecrawl_text(u)
            if len(t2) >= MIN_CHARS:
                t, used = t2, "firecrawl"
        pages[p or "/"] = {"text": t[:MAX_CHARS], "tool": used} if len(t) >= MIN_CHARS else {"text": "could not read", "tool": used}
    return pages


def own_words(domain):
    p = ROOT / "notes" / f"{domain}.md"
    if not p.exists():
        return []
    items = []
    for block in re.split(r"\n\s*\n", p.read_text(encoding="utf-8")):
        head, _, body = block.strip().partition("\n")
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s*\|\s*(.+)", head)
        if m and body.strip():
            items.append({"date": m.group(1), "source": m.group(2).strip(), "text": body.strip()})
    return items


def linkedin_posts(url):
    token = env("APIFY_TOKEN")
    if not token or not url:
        return []
    body = json.dumps({"targetUrls": [url], "maxPosts": 10, "postedLimit": "3months", "includeReposts": False}).encode()
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/harvestapi~linkedin-profile-posts/run-sync-get-dataset-items?token={token}",
        data=body, headers={"Content-Type": "application/json"})
    try:
        items = json.loads(urllib.request.urlopen(req, timeout=300).read())
    except Exception as e:
        print("   apify skipped:", e)
        return []
    out = []
    for it in items:
        date = str(it.get("postedAt", {}).get("date") if isinstance(it.get("postedAt"), dict) else it.get("postedAt") or "")[:10]
        text = (it.get("content") or it.get("text") or "").strip()
        if date and text:
            out.append({"date": date, "source": it.get("linkedinUrl") or "LinkedIn post", "text": text[:1500]})
    return out


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads", default="leads.csv")
    ap.add_argument("--max", type=int, default=20, help="most companies to research this run")
    a = ap.parse_args()
    cfg = config()
    out = run_dir(cfg, "dossiers")
    rows = list(csv.DictReader(open(ROOT / a.leads, encoding="utf-8-sig")))
    by_domain = {}
    for r in rows:
        by_domain.setdefault(r["domain"].strip().lower(), []).append(r)
    done = 0
    for domain, people in by_domain.items():
        f = out / f"{domain}.json"
        if f.exists():
            continue
        if done >= a.max:
            break
        print("researching", domain)
        dossier = {"domain": domain, "company": people[0]["company"], "pulled_at": datetime.date.today().isoformat(),
                   "site": site(domain), "people": []}
        for p in people:
            words = own_words(domain) if p is people[0] else []
            dossier["people"].append({"name": f"{p['first_name']} {p['last_name']}".strip(), "first_name": p["first_name"], "email": p.get("email", ""),
                                      "title": p["title"], "linkedin_url": p.get("linkedin_url", ""),
                                      "own_words": words + linkedin_posts(p.get("linkedin_url", ""))})
        f.write_text(json.dumps(dossier, ensure_ascii=False, indent=1), encoding="utf-8")
        readable = sum(v["text"] != "could not read" for v in dossier["site"].values())
        print(f"   {readable}/{len(PATHS)} pages read, {sum(len(p['own_words']) for p in dossier['people'])} own-word items")
        done += 1
    print(f"{done} new dossiers in {out}")


if __name__ == "__main__":
    main()
