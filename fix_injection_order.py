import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ensure we inject BEFORE the first <script tag (the module script)
old_pattern = r"(@app\.get\(\"/mini-app\"\)\s*async def mini_app_root\(request: Request\):\s*user_id = request\.query_params\.get\(\"user_id\", \"\"\)\s*html = open\(\"frontend/dist/index\.html\", encoding=\"utf-8\"\)\.read\(\)\s*if user_id:\s*# Inject the user_id.*?html = html\.replace\(\"</head>\", f\"<script>window\.NIFTI_USER_ID = '{user_id}';</script></head>\"\)\s*return HTMLResponse\(html\))"
new_function = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        # Inject user_id BEFORE the first <script> tag (before React loads)
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    return HTMLResponse(html)'''

if re.search(old_pattern, content, re.DOTALL):
    content = re.sub(old_pattern, new_function, content, flags=re.DOTALL)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('? Injection fixed: script placed before module script')
else:
    # Alternative: if the old pattern not found, maybe already correct?
    # Let's force the correct version by locating the function and replacing it entirely.
    start_marker = '@app.get("/mini-app")'
    end_marker = 'return HTMLResponse(html)'
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker, start_idx)
    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + new_function + content[end_idx+len(end_marker):]
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('? Injection fixed (fallback method)')
    else:
        print('? Could not locate mini_app_root function')
