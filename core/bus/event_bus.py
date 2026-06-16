class EventBus:
    def __init__(self):
        self.handlers = {}

    def on(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)

    def emit(self, event, data=None):
        for h in self.handlers.get(event, []):
            try:
                h(data)
            except Exception as e:
                print("[EVENT ERROR]", e)

bus = EventBus()

