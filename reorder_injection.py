import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the mini_app_root function and reorder the head scripts
old_head = '</head>'
new_head = '<script>window.NIFTI_USER_ID = \'{user_id}\';</script></head>'

# The replacement is already done; we just need to move the script before the module script.
# Let's find the exact block where we inject and adjust it.
old_inject = '<script>window.NIFTI_USER_ID = \'{user_id}\';</script></head>'
# We will now insert the script BEFORE the first <script type="module" ...> tag.
# So we modify the injection logic in the mini_app_root function.

# Replace the current injection method with one that inserts before the first script.
old_func = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        # Inject the user_id before the closing </head> tag
        html = html.replace("</head>", f"<script>window.NIFTI_USER_ID = '{user_id}';</script></head>")
    return HTMLResponse(html)'''

new_func = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        # Inject the user_id BEFORE the first <script> tag (before React loads)
        html = html.replace("<script", f"<script>window.NIFTI_USER_ID = '{user_id}';</script><script", 1)
    return HTMLResponse(html)'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated injection to place script before module script.')
else:
    print('Old function not found  maybe already updated?')
