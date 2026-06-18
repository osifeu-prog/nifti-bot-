import re, time
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the mini_app_root function to append ?t=<timestamp> to the script src
old_root = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})'''

new_root = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    # Add cache-busting timestamp to the module script
    ts = int(time.time())
    html = html.replace(".js\"", f".js?t={ts}\"")
    return HTMLResponse(html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})'''

if old_root in content:
    content = content.replace(old_root, new_root)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Cache-busting timestamp added to script src.")
else:
    print("Old root function not found  maybe already updated?")
