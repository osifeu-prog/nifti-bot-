import time
from app.core.logging.logger import log

def run_jobs():
    log("JOB SYSTEM STARTED")

    while True:
        try:
            # placeholder for TON scanner / referrals / payouts
            log("heartbeat - jobs running")
            time.sleep(10)

        except Exception as e:
            log(f"JOB ERROR: {e}", "ERROR")
            time.sleep(5)

