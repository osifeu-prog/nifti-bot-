import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ???? ?????? no-cache ????????? mini_app_root ?-mini_app_fallback
# 1. mini_app_root
old_root = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    return HTMLResponse(html)'''

new_root = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})'''

# 2. mini_app_fallback
old_fallback = '''@app.get("/mini-app/{full_path:path}")
async def mini_app_fallback(full_path: str):
    return HTMLResponse(open("frontend/dist/index.html", encoding="utf-8").read())'''

new_fallback = '''@app.get("/mini-app/{full_path:path}")
async def mini_app_fallback(full_path: str):
    return HTMLResponse(open("frontend/dist/index.html", encoding="utf-8").read(), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})'''

if old_root in content:
    content = content.replace(old_root, new_root)
if old_fallback in content:
    content = content.replace(old_fallback, new_fallback)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("No-cache headers added to mini-app routes.")
