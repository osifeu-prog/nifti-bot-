import datetime

def log(msg):
    print(f"[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}")

