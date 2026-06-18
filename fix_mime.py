import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()
middleware = '''
@app.middleware("http")
async def add_js_mime(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith(".js"):
        response.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return response
'''
if 'add_js_mime' not in content:
    content = content.replace('app = FastAPI(lifespan=lifespan)', 'app = FastAPI(lifespan=lifespan)' + middleware)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('MIME middleware added.')
else:
    print('Already present.')
