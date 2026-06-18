import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add StaticFiles import if missing
if 'from fastapi.staticfiles import StaticFiles' not in content:
    content = content.replace(
        'from fastapi import FastAPI, Request',
        'from fastapi import FastAPI, Request\nfrom fastapi.staticfiles import StaticFiles'
    )

# 2. Add mount and fallback after the app creation line
app_creation = 'app = FastAPI(lifespan=lifespan)'
mini_app_block = r'''
# Mini App static serving
app.mount("/mini-app/assets", StaticFiles(directory="frontend/dist/assets"), name="mini-app-assets")

@app.get("/mini-app")
async def mini_app_root():
    return HTMLResponse(open("frontend/dist/index.html", encoding="utf-8").read())

@app.get("/mini-app/{full_path:path}")
async def mini_app_fallback(full_path: str):
    return HTMLResponse(open("frontend/dist/index.html", encoding="utf-8").read())
'''
if '/mini-app/assets' not in content:
    content = content.replace(app_creation, app_creation + mini_app_block)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("server.py updated for Mini App static serving.")
