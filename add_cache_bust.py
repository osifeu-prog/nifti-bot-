import re, time

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the mini_app_root function and add version to script src
old = '''html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})'''

new = '''html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    ts = int(time.time())
    html = html.replace('.js"', f'.js?v={ts}"')
    return HTMLResponse(html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})'''

if old in content:
    content = content.replace(old, new)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Cache busting added.')
else:
    print('Pattern not found  may already have cache buster.')
