import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

api_card_route = '''
@app.get("/api/card/{user_id}")
async def get_card(user_id: int):
    # TODO: fetch real data from DB
    return {
        "card_name": "NIFTI User",
        "card_prof": "Explorer",
        "wallet": "EQD__________________",
        "user_id": user_id
    }
'''

if '/api/card/' not in content:
    content += '\n' + api_card_route
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('API card route added.')
else:
    print('Route already exists.')
