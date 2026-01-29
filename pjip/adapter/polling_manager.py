from PySide6.QtCore import QThread


class PollingManager: # QObject
    def __init__(self):
        # super().__init__()
        self.adapters = []
        self.threads = []

    def add(self, adapter):
        self.adapters.append(adapter)

    def start(self):
        for adapter in self.adapters:
            thread = QThread()
            adapter.moveToThread(thread)

            thread.started.connect(adapter.start)
            self.threads.append((adapter, thread))
            # self.lifelong_objects[adapter] = thread
            # self.threads[adapter] = thread
            thread.start()

    def stop(self):
        for adapter, thread in self.threads:
            adapter.deleteLater()
            adapter.stop()
            thread.quit()
            thread.wait()
            thread.deleteLater()

    def get_adapter(self, cls):
        for a in self.adapters:
            if isinstance(a, cls):
                return a
        return None