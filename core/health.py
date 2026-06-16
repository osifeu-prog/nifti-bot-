from core.db.engine import engine

def health_check():
    try:
        engine.execute("SELECT 1")
        return {"status": "OK"}
    except:
        return {"status": "FAIL"}
