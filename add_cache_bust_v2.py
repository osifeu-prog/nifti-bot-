import re, time

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ensure 'import time' exists
if 'import time' not in content.split('\n')[0:30]:
    content = content.replace('import uvicorn', 'import uvicorn\nimport time')

# Replace the mini_app_root function
old_func = '''async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        # Inject user_id BEFORE the first <script> tag (before React loads)
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    return HTMLResponse(html)'''

new_func = '''async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        # Inject user_id BEFORE the first <script> tag (before React loads)
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    # Cache busting: add timestamp to JS file
    ts = int(time.time())
    html = html.replace('.js"', f'.js?v={ts}"')
    return HTMLResponse(html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Cache busting + headers added to mini_app_root.')
else:
    print('Pattern not found  check indentation.')
