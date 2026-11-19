# Job Bot - automated job search & resume tailoring

Finds new jobs every morning, scores them against **your** profile, writes a tailored ATS-friendly resume + cover letter
for each good match, and (optionally) pre-fills the application form for your approval.

Works with a **free Google Gemini key** or an Anthropic Claude key. Runs on your own computer - your data never leaves it
except for the AI calls.

## Features
- Searches by **roles** and **cities** (or all of India) - change them in `config.yaml` or per run
- Sources: company career boards (Greenhouse / Lever / Ashby), Jooble (free key), Adzuna (optional), Remotive (remote)
- AI match score (0-100) with matched / missing skills
- **Truthful tailoring**: skills, certifications and numbers are checked in code against your `profile.json`; anything
  not in your profile is removed
- ATS-friendly single-column PDF resume + cover letter per job
- Form filler for Greenhouse / Lever / Ashby with a **review-before-submit** mode (default)
- SQLite tracker, daily report (file / Telegram), 9-11 AM scheduler

## Quick start
```
git clone https://github.com/<your-username>/job-bot.git
cd job-bot
pip install -r requirements.txt
python -m playwright install chromium      # only needed for auto-fill
```
1. Copy `.env.example` to `.env` and add a key: **free Gemini key** from https://aistudio.google.com/api-keys
   (or an Anthropic key). Optional: `JOOBLE_API_KEY` from https://jooble.org/api/about
2. Copy `profile.example.json` to `profile.json` and fill in YOUR real details (only true facts).
3. Edit `config.yaml`: roles, cities, thresholds.
4. Test, then run:
```
python main.py run --demo                  # offline test with sample jobs
python main.py run --dry-run               # real search + score + tailor, applies to nothing
python main.py run                         # fills forms and waits for your approval
python main.py approve all                 # submit the ones you reviewed
python main.py schedule                    # every day at 09:00, stops at 11:00
python main.py tailor --title "Sales Executive" --company "ABC" --file jd.txt   # manual, any job you find
python main.py run --india-wide            # override: whole India
python main.py run --roles "Account Executive" --locations Mumbai Pune
```
Outputs: `output/<company>_<id>/resume.pdf` and `cover_letter.txt`, tracker `jobs.db`, `reports/`.

## Windows tips
- Install Python from python.org (tick "Add to PATH"). The Microsoft Store Python can fail on long paths.
- Run commands in Command Prompt, not inside the Python `>>>` prompt.
- If pip fails with a "long path" error, enable long paths (PowerShell as admin):
  `New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force`, then restart.

## Responsible use
- LinkedIn, Naukri and Indeed forbid bots; this project does **not** scrape them.
- CAPTCHAs are never bypassed; those jobs are flagged for manual apply.
- Always review resumes before applying. You are responsible for what is submitted in your name.
- Never commit `.env` or `profile.json` (they are in `.gitignore`).
- Free Gemini tier may use your prompts to improve Google's products - avoid it if that matters to you.

## Limitations
Form layouts differ per company, so auto-fill is best-effort. Company board slugs in `config.yaml` must be real
(wrong ones are skipped). Free API limits apply.

## Contributing
Issues and pull requests welcome - new job sources and form-filler fixes especially.

License: MIT
