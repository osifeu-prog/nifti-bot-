# NIFTI SAAS - Core Architecture Log
Last Updated: 2026-06-18 14:05

## 1. המטרה: הפרדה מה-Bot
- ניתוק הלוגיקה מהבוט ל-Microservices עצמאיים.
- מעבר ל-DB שאינו משותף (Isolation).

## 2. משימות פיתוח SAAS
- [ ] תכנון מודל ה-Multi-tenancy (כל לקוח SAAS בנפרד).
- [ ] יצירת API Gateway עצמאי.
- [ ] הגדרת מנגנון אימות (Auth) נפרד מה-Telegram ID.

## 3. הערות למעבר
- לא להשתמש ב-server.py של הבוט.
- בנייה מ-Scratch בתוך תיקייה נפרדת (/saas_core).
