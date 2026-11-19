import os, requests, datetime as dt

def build(rows, stats):
    d = dt.date.today().strftime("%d %b %Y")
    L = [f"Job Bot morning report - {d}",
         f"Collected {stats['collected']} | new {stats['new']} | matched filters {stats['candidates']} | tailored {stats['tailored']} | "
         f"applied {stats['applied']} | awaiting approval {stats['review']} | manual/captcha {stats['manual']}", ""]
    for r in sorted(rows, key=lambda r: -(r["score"] or 0)):
        L.append(f"[{r['score']}] {r['title']} - {r['company']} ({r['location']}) -> {r['status']}\n    {r['url']}\n    {r['notes']}")
    if stats["review"]:
        L.append("\nApprove pending applications:  python main.py approve all")
    return "\n".join(L)

def deliver(text):
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{dt.date.today().isoformat()}.txt"
    open(path, "w", encoding="utf-8").write(text)
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if tok and chat:
        try:
            for i in range(0, len(text), 3900):
                requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": text[i:i+3900]}, timeout=20)
        except Exception as e:
            print("Telegram failed:", e)
    return path
