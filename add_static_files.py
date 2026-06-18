# add_static_files.py
server_path = r"D:\NIFTI\server.py"
with open(server_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. ודא שיש import ל-StaticFiles
if "from fastapi.staticfiles import StaticFiles" not in content:
    content = content.replace(
        "from fastapi import FastAPI, Request",
        "from fastapi import FastAPI, Request\nfrom fastapi.staticfiles import StaticFiles"
    )

# 2. הוסף mount של static files אחרי app = FastAPI(...)
if 'app.mount("/assets"' not in content:
    content = content.replace(
        'app = FastAPI(lifespan=lifespan)',
        'app = FastAPI(lifespan=lifespan)\napp.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")'
    )

# 3. הוסף route ל- / שמגיש את index.html (יחליף את ה-index הקיים)
old_index = '''@app.get('/')
async def index():
    return {'status': 'NIFTI API running'}'''
new_index = '''@app.get('/api/status')
async def api_status():
    return {'status': 'NIFTI API running'}

@app.get('/')
async def serve_mini_app():
    from fastapi.responses import FileResponse
    import os
    path = os.path.join("frontend", "dist", "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return HTMLResponse("<h1>Mini App not built</h1>")'''
content = content.replace(old_index, new_index)

with open(server_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Static files + Mini App route added")
