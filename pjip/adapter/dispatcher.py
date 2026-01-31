from PySide6.QtCore import QObject, QThreadPool, QRunnable, Signal

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

    def submit(self, runnable, priority=0, daemon = False):
        """
        runnable: QRunnable
        priority: int (higher = more important)
        """
        if daemon:
            self.daemon_pool.start(runnable, priority)
        else:
            self.pool.start(runnable, priority)

    def injected_submit(self, runnable, priority=0, daemon = False):
        pool = self.daemon_pool if daemon else self.pool
        runnable.callback = lambda v: self.task_return.emit(v)
        runnable.error_callback = lambda e: self.task_error.emit(e)

        if hasattr(runnable, "middle_callback"):
            runnable.middle_callback = lambda v: self.task_middle.emit(v)

        if hasattr(runnable, "external_callback"):
            runnable.external_callback = lambda v: self.task_external_action.emit(v)

        pool.start(runnable, priority)

    def submit_daemon(self, runnable, priority=0):
        """
        runnable: QRunnable
        priority: int (higher = more important)
        """
        self.daemon_pool.start(runnable, priority)

    def wait(self):
        self.pool.waitForDone()


class BaseRunnable(QRunnable):
    def __init__(self, fn, *args, callback=None, error_callback=None):
        super().__init__()
        self.fn = fn
        self.args = args
        self.callback = callback
        self.error_callback = error_callback

    def run(self):
        try:
            result = self.fn(*self.args)
            if self.callback:
                self.callback(result)
        except Exception as e:
            if self.error_callback:
                self.error_callback(e)


class AdvanceRunnable(QRunnable):
    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args

        self.callback = None
        self.error_callback = None
        self.middle_callback = None
        self.external_callback = None
        self.finished_callback = None

    def run(self):
        try:
            result = self.fn(*self.args)
            if self.callback:
                self.callback(result)
        except Exception as err:
            if self.error_callback:
                self.error_callback(err)
        finally:
            if self.finished_callback:
                self.finished_callback(None)

# task = BaseRunnable(
#     self.logic.terminate_process,
#     pid,
#     callback=lambda r: print("done"),
#     error_callback=lambda e: print("error:", e)
# )
#
# self.dispatcher.submit(task, priority=10)
