import argparse, datetime as dt, random, time, os
from zoneinfo import ZoneInfo
import db, report
from models import Job, load_config, load_profile, load_env
from collectors import collect_all
from filters import location_ok, role_ok, fresh_ok
from matcher import score_job
from tailor import tailor, render_pdf
import applier

DEMO = [
    Job("demo", "SaaS Account Executive", "DemoCloud", "Vadodara, Gujarat", "B2B SaaS sales, cold calling, CRM HubSpot, product demos, negotiation, pipeline management. 2+ years.", "https://example.com/j/1", "", "lever"),
    Job("demo", "Business Development Executive", "AcmeSoft", "Indore, India", "Lead generation, Salesforce, LinkedIn Sales Navigator, B2B SaaS. HubSpot certification a plus.", "https://example.com/j/2", "", "greenhouse"),
    Job("demo", "Senior Software Engineer", "CodeCo", "Ahmedabad", "Python, Go.", "https://example.com/j/3", "", ""),
    Job("demo", "VP Sales", "BigCo", "Mumbai", "Lead the sales org.", "https://example.com/j/4", "", ""),
    Job("demo", "Inside Sales Executive", "FarAway Inc", "London, UK", "SaaS inside sales.", "https://example.com/j/5", "", ""),
]

def apply_overrides(cfg, a):
    s = cfg["search"]
    if a.roles: s["roles"] = a.roles; s["title_keywords"] = list({*s["title_keywords"], *[r.lower() for r in a.roles]})
    if a.locations: s["locations"] = a.locations; s["india_wide"] = False
    if a.india_wide: s["india_wide"] = True
    if a.mode: cfg["apply"]["mode"] = a.mode

def in_window(cfg):
    tz = ZoneInfo(cfg["schedule"]["timezone"])
    now = dt.datetime.now(tz).time()
    h = lambda x: dt.time(*map(int, x.split(":")))
    return now <= h(cfg["schedule"]["end"])

def run(cfg, a):
    profile, c = load_profile(), db.conn()
    dry = a.dry_run or a.demo
    st = dict(collected=0, new=0, candidates=0, tailored=0, applied=0, review=0, manual=0)
    print(f"Searching: roles={cfg['search']['roles']} | " + ("ALL INDIA" if cfg["search"]["india_wide"] else f"locations={cfg['search']['locations']}"))
    jobs = DEMO if a.demo else collect_all(cfg)
    st["collected"] = len(jobs)
    cands = []
    why = {"wrong location": 0, "title not a sales role": 0, "too old": 0}
    samples = []
    for j in jobs:
        if db.seen(c, j.id):
            continue
        st["new"] += 1
        lo, ro, fo = location_ok(j.location, cfg), role_ok(j.title, cfg), fresh_ok(j.posted, cfg["search"]["posted_within_hours"])
        if lo and ro and fo:
            cands.append(j)
        else:
            why["wrong location" if not lo else "title not a sales role" if not ro else "too old"] += 1
            if len(samples) < 12:
                samples.append(f"   - {j.title} | {j.location} | posted {j.posted[:10] or '?'}")
            db.upsert(c, j, "filtered")
    if st["new"] and not cands:
        print("Why jobs were filtered out:", why)
        print("Examples of rejected jobs:"); print("\n".join(samples))
    st["candidates"] = len(cands)
    print(f"{st['new']} new jobs, {len(cands)} pass location/role filters")
    touched = []
    for j in cands:
        if not a.ignore_window and not a.demo and not in_window(cfg):
            print("Past end of time window - stopping. Remaining jobs stay unprocessed for tomorrow.")
            break
        print(f"→ {j.title} @ {j.company} ({j.location})")
        m = score_job(j, profile, cfg)
        sc = int(m.get("score", 0))
        if sc < cfg["matching"]["min_score_to_tailor"]:
            db.upsert(c, j, "low_match", sc, notes=m.get("reason", ""))
            print(f"   skipped, score {sc}")
            continue
        t = tailor(j, profile, m, cfg)
        pdf = render_pdf(t, profile, f"output/{j.company}_{j.id}/resume.pdf".replace(" ", "_"))
        open(os.path.join(os.path.dirname(pdf), "cover_letter.txt"), "w", encoding="utf-8").write(t["cover_letter"])
        st["tailored"] += 1
        status, note = "tailored", m.get("reason", "")
        mode = cfg["apply"]["mode"]
        if not dry and mode != "off" and db.applied_today(c) < cfg["apply"]["max_per_day"]:
            submit = mode == "auto" and sc >= cfg["matching"]["min_score_auto_submit"]
            status, note = applier.apply(j, pdf, t["cover_letter"], profile, cfg, submit)
            time.sleep(random.uniform(*cfg["apply"]["delay_seconds"]))
        st["applied"] += status == "applied"; st["review"] += status == "ready_for_review"
        st["manual"] += status in ("manual", "captcha", "failed")
        db.upsert(c, j, status, sc, pdf, note)
        touched.append(c.execute("SELECT * FROM jobs WHERE id=?", (j.id,)).fetchone())
        print(f"   score {sc} → {status}")
    txt = report.build(touched, st)
    print("\n" + txt + f"\n\nSaved: {report.deliver(txt)}")

def approve(cfg, target):
    profile, c = load_profile(), db.conn()
    for r in db.by_status(c, "ready_for_review"):
        if target not in ("all", r["id"]):
            continue
        j = Job(r["source"], r["title"], r["company"], r["location"], "", r["url"], "", r["ats"])
        cover = open(os.path.join(os.path.dirname(r["resume_path"]), "cover_letter.txt"), encoding="utf-8").read()
        status, note = applier.apply(j, r["resume_path"], cover, profile, cfg, submit=True)
        db.upsert(c, j, status, r["score"], notes=note)
        print(r["id"], r["title"], "→", status, note)

def listing():
    for r in db.conn().execute("SELECT * FROM jobs WHERE status NOT IN ('filtered','low_match') ORDER BY updated DESC LIMIT 50"):
        print(f"{r['id']} [{r['score']}] {r['status']:17} {r['title']} @ {r['company']}  {r['url']}")

def tailor_one(cfg, a):
    """Free manual mode: you found a job anywhere (Naukri, LinkedIn...), paste its description in a .txt file."""
    profile = load_profile()
    desc = open(a.file, encoding="utf-8").read()
    j = Job("manual", a.title or "Role", a.company or "Company", "", desc, "manual:" + (a.title or "") + (a.company or ""))
    m = score_job(j, profile, cfg)
    t = tailor(j, profile, m, cfg)
    pdf = render_pdf(t, profile, f"output/{(j.company).replace(' ', '_')}_{j.id}/resume.pdf")
    open(os.path.join(os.path.dirname(pdf), "cover_letter.txt"), "w", encoding="utf-8").write(t["cover_letter"])
    print(f"Match score: {m.get('score')} | missing skills: {m.get('missing_skills')}\nSaved: {pdf}")

def schedule(cfg, a):
    from apscheduler.schedulers.blocking import BlockingScheduler
    h, m = cfg["schedule"]["start"].split(":")
    s = BlockingScheduler(timezone=cfg["schedule"]["timezone"])
    s.add_job(lambda: run(cfg, a), "cron", hour=int(h), minute=int(m))
    print(f"Scheduler running: every day at {cfg['schedule']['start']} {cfg['schedule']['timezone']}. Keep this window/process alive.")
    s.start()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Job search & apply bot")
    p.add_argument("command", choices=["run", "schedule", "approve", "list", "tailor"])
    p.add_argument("target", nargs="?", default="all", help="for approve: job id or 'all'")
    p.add_argument("--roles", nargs="+"); p.add_argument("--locations", nargs="+")
    p.add_argument("--india-wide", action="store_true"); p.add_argument("--mode", choices=["off", "review", "auto"])
    p.add_argument("--dry-run", action="store_true", help="find + score + tailor, never touch application forms")
    p.add_argument("--title"); p.add_argument("--company"); p.add_argument("--file", help="text file containing the job description")
    p.add_argument("--demo", action="store_true", help="offline test with sample jobs")
    p.add_argument("--ignore-window", action="store_true")
    a = p.parse_args()
    load_env(); cfg = load_config(); apply_overrides(cfg, a)
    {"run": lambda: run(cfg, a), "schedule": lambda: schedule(cfg, a), "approve": lambda: approve(cfg, a.target), "list": listing, "tailor": lambda: tailor_one(cfg, a)}[a.command]()
