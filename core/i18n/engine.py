import json

class I18n:
    def __init__(self):
        with open("lang.json", "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def t(self, lang, key, **kwargs):
        text = self.data.get(lang, {}).get(key, key)
        return text.format(**kwargs)

i18n = I18n()

