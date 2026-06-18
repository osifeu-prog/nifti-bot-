import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the mini_app_root function
old_mini_app = '''@app.get("/mini-app")
async def mini_app_root():
    return HTMLResponse(open("frontend/dist/index.html", encoding="utf-8").read())'''

new_mini_app = '''@app.get("/mini-app")
async def mini_app_root(request: Request):
    user_id = request.query_params.get("user_id", "")
    html = open("frontend/dist/index.html", encoding="utf-8").read()
    if user_id:
        # Inject the user_id before the closing </head> tag
        html = html.replace("</head>", f"<script>window.NIFTI_USER_ID = '{user_id}';</script></head>")
    return HTMLResponse(html)'''

if old_mini_app in content:
    content = content.replace(old_mini_app, new_mini_app)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("mini_app_root updated to inject user_id.")
else:
    print("Pattern not found  may already be updated.")
