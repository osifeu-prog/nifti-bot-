# NIFTI Workflow Rules
**Last Updated:** 2026-06-18
**Version:** 1.0

## 🔒 Core Principles
1. **PowerShell Only**  All development, testing, and deployment is done via PowerShell commands.
2. **SSoT (Single Source of Truth)**  The codebase + STATUS_OVERVIEW.md + open_tasks.txt are always up-to-date.
3. **No manual edits**  Every change is applied through a script or a documented command block.
4. **Test after every change**  `python -c "import server; print('OK')"` is mandatory.
5. **Backup before risky changes**  Run `backup_db.py` or create a Git commit.
6. **Git hygiene**  Commit often, push to `main` after every stable change.
7. **Virtual environment**  Always work inside `venv`.
8. **Logs**  Use `railway logs --service bot --tail` to verify deployments.

## 📋 Task Management
- All tasks are tracked in `open_tasks.txt`.
- Completed tasks are moved to `## ✅ Completed` with `[x]`.
- Use `edit-tasks` to open the task file.
- Timer-based tracking is shown in the prompt.

## 🧪 Testing
- Local import test: `python -c "import server; print('OK')"`
- Railway logs: `railway logs --service bot --tail 15`
- Webhook check: `curl .../getWebhookInfo`

## 🚀 Deployment
- `git add -A; git commit -m "..."; git push origin main`
- Railway deploys automatically.
- Verify with `railway logs`.

## 🔄 Adding New Features
1. Write the Python code.
2. Test locally.
3. Add task to `open_tasks.txt`.
4. Commit & push.
5. Monitor logs.
