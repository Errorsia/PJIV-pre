

class PollingManager:
    def __init__(self, /):
        self.adapters = []

    def add(self, adapter):
        self.adapters.append(adapter)

    def start(self):
        for a in self.adapters:
            a.start()

    def stop(self):
        for a in self.adapters:
            a.stop()