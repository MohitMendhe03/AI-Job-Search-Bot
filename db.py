import sqlite3, datetime as dt

def conn():
    c = sqlite3.connect("jobs.db")
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS jobs(
        id TEXT PRIMARY KEY, source TEXT, title TEXT, company TEXT, location TEXT, url TEXT,
        ats TEXT, score INTEGER, status TEXT, resume_path TEXT, notes TEXT, updated TEXT)""")
    return c

def seen(c, job_id):
    return c.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone() is not None

def upsert(c, job, status, score=None, resume_path="", notes=""):
    now = dt.datetime.now().isoformat(timespec="seconds")
    c.execute("""INSERT INTO jobs(id,source,title,company,location,url,ats,score,status,resume_path,notes,updated)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                 ON CONFLICT(id) DO UPDATE SET status=excluded.status, score=COALESCE(excluded.score,score),
                 resume_path=CASE WHEN excluded.resume_path!='' THEN excluded.resume_path ELSE resume_path END,
                 notes=excluded.notes, updated=excluded.updated""",
              (job.id, job.source, job.title, job.company, job.location, job.url, job.ats, score, status, resume_path, notes, now))
    c.commit()

def by_status(c, status):
    return c.execute("SELECT * FROM jobs WHERE status=? ORDER BY score DESC", (status,)).fetchall()

def applied_today(c):
    d = dt.date.today().isoformat()
    return c.execute("SELECT COUNT(*) FROM jobs WHERE status='applied' AND updated LIKE ?", (d + "%",)).fetchone()[0]
