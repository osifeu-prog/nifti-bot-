import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add UTF-8 charset to all JSON responses (via middleware)
middleware_code = """
@app.middleware("http")
async def add_utf8_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response
"""
if 'add_utf8_header' not in content:
    content = content.replace('app = FastAPI(lifespan=lifespan)', 'app = FastAPI(lifespan=lifespan)\n' + middleware_code)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('UTF-8 middleware added.')
else:
    print('Already present.')
