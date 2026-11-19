import os, requests, datetime as dt
from models import Job, strip_html

H = {"User-Agent": "Mozilla/5.0 (job-bot personal use)"}

def _get(url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=25, **kw)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ! skipped {url[:70]}... ({type(e).__name__})")
        return None

def greenhouse(slug):
    d = _get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", params={"content": "true"})
    for j in (d or {}).get("jobs", []):
        yield Job("greenhouse", j.get("title", ""), slug, (j.get("location") or {}).get("name", ""),
                  strip_html(j.get("content", "")), j.get("absolute_url", ""), j.get("updated_at", ""), "greenhouse")

def lever(slug):
    d = _get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"})
    for j in d or []:
        ts = j.get("createdAt")
        posted = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).isoformat() if ts else ""
        yield Job("lever", j.get("text", ""), slug, (j.get("categories") or {}).get("location", "") or "",
                  j.get("descriptionPlain", ""), j.get("hostedUrl", ""), posted, "lever")

def ashby(slug):
    d = _get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    for j in (d or {}).get("jobs", []):
        yield Job("ashby", j.get("title", ""), slug, j.get("location", "") or "",
                  j.get("descriptionPlain", "") or strip_html(j.get("descriptionHtml", "")),
                  j.get("jobUrl", ""), j.get("publishedAt", "") or "", "ashby")

def adzuna(roles, places, india_wide, days):
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        print("   (Adzuna skipped: no keys in .env)")
        return
    wheres = [""] if india_wide else places
    for role in roles:
        for where in wheres:
            p = {"app_id": app_id, "app_key": app_key, "what": role, "results_per_page": 50,
                 "max_days_old": max(1, days), "content-type": "application/json"}
            if where:
                p["where"] = where
            d = _get("https://api.adzuna.com/v1/api/jobs/in/search/1", params=p)
            for j in (d or {}).get("results", []):
                yield Job("adzuna", j.get("title", ""), (j.get("company") or {}).get("display_name", ""),
                          (j.get("location") or {}).get("display_name", ""), strip_html(j.get("description", "")),
                          j.get("redirect_url", ""), j.get("created", ""), "")

def jooble(roles, places, india_wide):
    key = os.getenv("JOOBLE_API_KEY")
    if not key:
        print("   (Jooble skipped: no JOOBLE_API_KEY in .env)")
        return
    base = os.getenv("JOOBLE_BASE", "https://jooble.org/api")
    for role in roles:
        for where in ([""] if india_wide else places):
            try:
                r = requests.post(f"{base}/{key}", json={"keywords": role, "location": where or "India", "page": 1},
                                  headers=H, timeout=25)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"   ! jooble '{role}' in '{where}' failed ({type(e).__name__})")
                continue
            for j in data.get("jobs", []):
                yield Job("jooble", j.get("title", ""), j.get("company", ""), j.get("location", ""),
                          strip_html(j.get("snippet", "")), j.get("link", ""), j.get("updated", ""), "")

def remotive():
    d = _get("https://remotive.com/api/remote-jobs", params={"category": "sales"})
    for j in (d or {}).get("jobs", []):
        yield Job("remotive", j.get("title", ""), j.get("company_name", ""),
                  "Remote - " + (j.get("candidate_required_location", "") or ""),
                  strip_html(j.get("description", "")), j.get("url", ""), j.get("publication_date", ""), "")

def collect_all(cfg):
    s, src = cfg["search"], cfg["sources"]
    jobs = []
    def add(label, items):
        items = list(items)
        print(f"   → {label}: {len(items)} jobs")
        return items
    for name, fn in (("greenhouse", greenhouse), ("lever", lever), ("ashby", ashby)):
        for slug in src.get(name) or []:
            print(f" · {name}: {slug}")
            jobs += add(slug, fn(slug))
    if src.get("adzuna"):
        print(" · adzuna (India job boards)")
        jobs += add("adzuna", adzuna(s["roles"], s["locations"], s["india_wide"], max(1, s["posted_within_hours"] // 24)))
    if src.get("jooble"):
        print(" · jooble (aggregates Indian job sites)")
        jobs += add("jooble", jooble(s["roles"], s["locations"], s["india_wide"]))
    if src.get("remotive") and s.get("include_remote"):
        print(" · remotive")
        jobs += add("remotive", remotive())
    return [j for j in jobs if j.url]
