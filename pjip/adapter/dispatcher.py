from PySide6.QtCore import QObject, QThreadPool, Signal


class TaskDispatcher(QObject):
    task_error = Signal(Exception)
    task_finished = Signal(object)
    task_return = Signal(object)
    task_middle = Signal(object)
    task_external_action = Signal(object)

    def __init__(self, max_threads=4):
        super().__init__()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(max_threads)

        self.daemon_pool = QThreadPool()
        self.daemon_pool.setMaxThreadCount(max_threads)

    def submit(self, runnable, priority=0, daemon=False):
        """
        runnable: QRunnable
        priority: int (higher = more important)
        """
        if daemon:
            self.daemon_pool.start(runnable, priority)
        else:
            self.pool.start(runnable, priority)

    def injected_submit(self, runnable, priority=0, daemon=False):
        pool = self.daemon_pool if daemon else self.pool
        runnable.finished_callback = lambda v: self.task_finished.emit(v)
        runnable.error_callback = lambda e: self.task_error.emit(e)

        if hasattr(runnable, "callback"):
            runnable.callback = lambda v: self.task_return.emit(v)

        if hasattr(runnable, "middle_callback"):
            runnable.middle_callback = lambda v: self.task_middle.emit(v)

        if hasattr(runnable, "external_callback"):
            runnable.external_callback = lambda v: self.task_external_action.emit(v)

        pool.start(runnable, priority)

    def wait(self):
        self.pool.waitForDone()
