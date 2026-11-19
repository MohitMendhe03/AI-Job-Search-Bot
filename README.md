# 🤖 AI Job Search Bot – Automated Job Search & Resume Tailoring

An AI-powered job search automation tool built with Python that helps job seekers discover relevant opportunities, evaluate job matches, tailor ATS-friendly resumes, and prepare job applications.

The goal is simple: **Spend less time searching and customizing applications, and more time preparing for the right opportunities.**

## ✨ Features

- **Automated Job Search:** Search for jobs based on preferred roles, cities, and remote opportunities.
- **AI-Powered Job Matching:** Get a match score from 0–100 with matched and missing skills.
- **Smart Resume Tailoring:** Generate customized, ATS-friendly resumes based on individual job descriptions.
- **Cover Letter Generation:** Create a tailored cover letter for each relevant job.
- **Application Assistance:** Pre-fill supported application forms with a review-before-submit option.
- **Application Tracking:** Store job and application information using SQLite.
- **Daily Reports:** Generate reports locally or through Telegram.
- **Scheduled Search:** Run automated job searches daily between configured times.

## 🛠️ Tech Stack

| Technology | Purpose |
| --- | --- |
| Python | Core application |
| Google Gemini API | AI-powered matching and tailoring |
| Anthropic Claude API | Alternative AI provider |
| SQLite | Job and application tracking |
| Playwright | Browser-based application form automation |
| ReportLab | PDF resume generation |
| YAML | Configuration management |
| APScheduler | Scheduled job searches |

## 📂 Project Structure

```text
AI-Job-Search-Bot/
│
├── main.py                  # Main application and CLI
├── collectors.py            # Job collection from supported sources
├── matcher.py               # AI job matching
├── tailor.py                # Resume and cover letter tailoring
├── applier.py               # Application form automation
├── filters.py               # Job filtering
├── llm.py                   # AI provider integration
├── models.py                # Data models
├── db.py                    # SQLite database management
├── report.py                # Daily reports
│
├── config.yaml              # Job search configuration
├── requirements.txt         # Python dependencies
├── profile.example.json     # Sample candidate profile
├── .env.example              # Sample environment variables
├── .gitignore
├── LICENSE
└── README.md
```

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/MohitMendhe03/AI-Job-Search-Bot.git
cd AI-Job-Search-Bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browser

Required for browser-based application form automation.

```bash
python -m playwright install chromium
```

### 4. Configure API keys

Copy `.env.example` and rename the copy to `.env`.

Add your API credentials:

```ini
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=
JOOBLE_API_KEY=your_jooble_api_key
```

You can use Google Gemini or Anthropic Claude for AI functionality.

- Gemini API: https://aistudio.google.com/api-keys
- Jooble API: https://jooble.org/api/about

### 5. Configure your candidate profile

Copy `profile.example.json` and rename the copy to `profile.json`.

Update it with your actual:

- Name and contact details
- Professional summary
- Skills
- Education
- Work experience
- Certifications
- Projects

Only enter accurate information.

### 6. Customize job search preferences

Edit `config.yaml` to configure:

- Preferred job roles
- Target cities
- Remote job preferences
- Job posting age
- Minimum AI match score
- Application mode
- Daily search schedule

## ▶️ How to Run

### Test using demo mode

```bash
python main.py run --demo
```

Runs an offline test using sample jobs.

### Search and tailor without applying

```bash
python main.py run --dry-run
```

Searches for real jobs, evaluates matches, and generates tailored documents without interacting with application forms.

### Run the complete workflow

```bash
python main.py run
```

Runs the configured workflow with the default review-before-submit mode.

### Approve reviewed applications

```bash
python main.py approve all
```

Submits applications that have been reviewed and approved.

### Schedule daily job searches

```bash
python main.py schedule
```

Uses the configured daily schedule.

### Tailor a resume for a specific job

```bash
python main.py tailor --title "Sales Executive" --company "ABC" --file jd.txt
```

### Search across India

```bash
python main.py run --india-wide
```

### Search using specific roles and locations

```bash
python main.py run --roles "Account Executive" --locations Mumbai Pune
```

## 📊 Output

The generated files are stored locally:

```text
output/
   └── company_job-id/
       ├── resume.pdf
       └── cover_letter.txt

jobs.db
reports/
```

- `resume.pdf` – Tailored resume.
- `cover_letter.txt` – Customized cover letter.
- `jobs.db` – SQLite job and application tracker.
- `reports/` – Generated job search reports.

## 🔐 Privacy & Responsible Use

- API keys and personal profile files should remain local and must never be committed to GitHub.
- The project uses your profile information to tailor application documents.
- AI-generated resumes are checked against your profile to remove unsupported skills, certifications, and numbers.
- LinkedIn, Naukri, and Indeed are not scraped because their terms prohibit bots.
- CAPTCHAs are not bypassed; affected applications are flagged for manual action.
- Always review generated resumes and application details before submitting.

**Important:** AI providers receive the prompts sent to their APIs. Review their data policies before sharing personal information.

## ⚠️ Limitations

- Application form automation is best-effort because company application layouts differ.
- Supported company career boards depend on valid configuration and available sources.
- API usage may be subject to rate limits and provider policies.
- Some applications may require manual completion.

## 🤝 Contributions

Contributions, suggestions, bug reports, and feature improvements are welcome!

If you find an issue or have an idea:

1. Open an issue.
2. Describe the problem or suggested improvement.
3. Submit a pull request if you have a solution.

## 🗺️ Future Improvements

Some areas for further development:

- More job board integrations.
- Improved job recommendation and ranking.
- Enhanced application tracking dashboard.
- Better browser automation support.
- More detailed job search analytics.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

### 👨‍💻 Developed by Mohit Mendhe

**AI Job Search Bot – Making job searching smarter through AI and automation.**

⭐ If you find this project useful, consider giving it a star on GitHub!

[GitHub Repository](https://github.com/MohitMendhe03/AI-Job-Search-Bot)
