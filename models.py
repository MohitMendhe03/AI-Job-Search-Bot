import hashlib, json, os, re, html
from dataclasses import dataclass
import yaml

@dataclass
class Job:
    source: str
    title: str
    company: str
    location: str
    description: str
    url: str
    posted: str = ""      # ISO string if known
    ats: str = ""         # greenhouse | lever | ashby | "" (manual)

    @property
    def id(self):
        return hashlib.sha1(self.url.encode()).hexdigest()[:12]

def load_config(path="config.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_profile(path="profile.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def strip_html(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()
