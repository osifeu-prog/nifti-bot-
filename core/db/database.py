from core.db.engine import engine

def execute(q, params=None):
    return engine.execute(q, params)

