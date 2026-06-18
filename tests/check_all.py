import requests, sys

BASE = "https://bot-production-c2a5.up.railway.app"

def test_card():
    r = requests.get(f"{BASE}/api/card/224223270")
    if r.status_code == 200 and r.json().get("card_name") == "OsifTest":
        print("? /api/card OK")
    else:
        print(f"? /api/card FAILED: {r.status_code} {r.text}")

def test_qr():
    r = requests.get(f"{BASE}/api/qr/224223270")
    if r.status_code == 200 and "qr_url" in r.json():
        print("? /api/qr OK")
    else:
        print(f"? /api/qr FAILED: {r.status_code} {r.text}")

def test_dump():
    r = requests.get(f"{BASE}/api/dump/users")
    if r.status_code == 200:
        print("? /api/dump/users OK")
        users = r.json()
        target = next((u for u in users if u['user_id'] == 224223270), None)
        if target:
            print(f"   User fields: {list(target.keys())}")
            print(f"   card_name = {target.get('card_name')}")
        else:
            print("   User 224223270 not found in dump")
    else:
        print(f"? /api/dump/users FAILED: {r.status_code}")

if __name__ == "__main__":
    test_card()
    test_qr()
    test_dump()
