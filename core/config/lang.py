import json
import os

LANG_PATH = os.path.join(os.path.dirname(__file__), "../../lang.json")

with open(LANG_PATH, "r", encoding="utf-8") as f:
    LANGS = json.load(f)

def t(lang: str, key: str):
    try:
        return LANGS.get(lang, LANGS["en"]).get(key, key)
    except:
        return key

