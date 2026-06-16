import json
import datetime

def log(event: str, level="INFO", data=None):
    payload = {
        "time": datetime.datetime.utcnow().isoformat(),
        "level": level,
        "event": event,
        "data": data
    }
    print(json.dumps(payload, ensure_ascii=False))

