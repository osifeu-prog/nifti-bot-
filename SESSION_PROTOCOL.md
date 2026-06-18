# 🔒 NIFTI Session Protocol
**Version:** 1.0
**Last Updated:** 2026-06-18

---

## 🟢 תחילת סשן
1. `cd D:\NIFTI`
2. `.\.venv\Scripts\Activate.ps1`
3. `git pull origin main`
4. `python -c "import server; print('OK')"`
5. `railway logs --service bot --tail 5`
6. `Get-Content open_tasks.txt`

---

## 🟡 במהלך הסשן
### לפני כל שינוי
- `python -c "import server; print('OK')"`
- `git status`

### אחרי כל שינוי
- `python -c "import server; print('OK')"`
- `git add -A`
- `git commit -m "תיאור ברור"`
- `git push origin main`
- `railway logs --service bot --tail 5`

### כלל ברזל
**כל פקודה מתבצעת דרך PowerShell.**
**אין עריכה ידנית של קבצים.**
**בודקים `import server` אחרי כל שינוי.**

---

## 🔴 סיום סשן
1. `python -c "import server; print('OK')"`
2. `python backup_db.py`
3. `git add -A`
4. `git commit -m "Session end  stable"`
5. `git push origin main`
6. `railway logs --service bot --tail 5`
7. עדכון `open_tasks.txt` ו-`STATUS_OVERVIEW.md`

---

## 🆘 חירום
### הבוט לא מגיב
1. `railway logs --service bot --tail 20`
2. `curl "https://api.telegram.org/bot7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0/getWebhookInfo"`
3. `git checkout a2c0148 -- server.py`  (גרסה יציבה אחרונה)
4. `railway redeploy --service bot`

### Railway קורס שוב ושוב
1. בדוק `railway logs`  חפש `RuntimeError` או `SyntaxError`
2. אם `frontend/dist/assets`  הרץ `$lines = Get-Content server.py | Where-Object { $_ -notmatch 'app\.mount' }; $lines | Set-Content server.py -Encoding UTF8`
3. `git push origin main`

---

## 📌 נהלי DB
- **כל ALTER/ADD COLUMN**  מוודאים שקיים גם ב-Railway (Console).
- **גיבוי**  `python backup_db.py` בסוף כל סשן.
- **מבנה**  מתועד ב-`full_schema.txt` (נוצר על ידי `dump_schema.py`).

---

## 🔑 מיקומים
- **DB מקומי:** `postgresql://postgres:slh_secure_2026@localhost:5432/slh_main`
- **DB Railway:** `DATABASE_URL` (מוגדר אוטומטית)
- **Webhook:** `https://bot-production-c2a5.up.railway.app/webhook`
- **Admin Panel:** `http://127.0.0.1:8002`
- **SAAS API:** `http://127.0.0.1:8001`
