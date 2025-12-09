# adapter.py
# from threading import Thread

from PySide6.QtCore import QObject, Signal, QTimer, QThread
from Jiv_enmus import SuspendState


class AdapterManager(QObject):
    ui_change = Signal(str, object)

    def __init__(self, logic, gui):
        super().__init__()
        self.on_demand_adapters = {}
        self.logic = logic
        self.gui = gui

        self.lifelong_adapters = []
        self.lifelong_threads = {}

        self.terminate_adapter = self.start_adapter = self.suspend_studentmain_adapter = None

        self.init_workers()
        self.start_all()

    def init_workers(self):
        self.lifelong_adapters.append(MonitorAdapter(self.logic))
        self.lifelong_adapters.append(SuspendMonitorAdapter(self.logic))
        # self.lifelong_adapters.append(DatabaseAdapter(logic, 2000))
        # self.lifelong_adapters.append(NetworkAdapter(logic, 5000))

        self.terminate_adapter = TerminateAdapter(self.logic)
        self.suspend_studentmain_adapter = SuspendStudentmainAdapter(self.logic)
        self.start_adapter = StartStudentmainAdapter(self.logic)

    def start_all(self):
        for adapter in self.lifelong_adapters:
            thread = QThread()
            adapter.moveToThread(thread)

            thread.started.connect(adapter.start)
            # Wrap with lambda and send the adapter class name and result together
            adapter.changed.connect(lambda result, w=adapter:
                                    self.ui_change.emit(type(w).__name__, result))

            self.lifelong_threads[adapter] = thread
            thread.start()

    def stop_all(self):
        """Stop all adapters and safely exit the thread"""
        for adapter, thread in self.lifelong_threads.items():
            adapter.stop()
            thread.quit()
            thread.wait()

    def terminate_studentmain(self):
        self.terminate_adapter.start()

    def start_studentmain(self):
        self.start_adapter.start()

    def suspend_resume_studentmain(self):
        self.suspend_studentmain_adapter.start()


class BaseAdapterInterface:
    def start(self):
        raise NotImplementedError("Subclasses must implement start()")

    def stop(self):
        raise NotImplementedError("Subclasses must implement stop()")

    def run_task(self):
        raise NotImplementedError("Subclasses must implement run_task()")


# class BaseAdapterInterface(ABC):
#     @abstractmethod
#     def start(self):
#         raise NotImplementedError("Subclasses must implement start()")
#
#     @abstractmethod
#     def stop(self):
#         raise NotImplementedError("Subclasses must implement stop()")
#
#     @abstractmethod
#     def run_task(self):
#         raise NotImplementedError("Subclasses must implement run_task()")


class MonitorAdapter(QObject, BaseAdapterInterface):
    changed = Signal(bool)

    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.timer = QTimer(self)
        self.timer.setInterval(600)
        self.timer.timeout.connect(self.run_task)
        self.last_result = None

    def start(self):
        self.timer.start()
        # QTimer.singleShot(0, self.check_state)

    def stop(self):
        self.timer.stop()

    def run_task(self):
        state = self.check_state()
        if state is not self.last_result:
            self.last_result = state
            self.changed.emit(state)

    def check_state(self):
        return self.logic.get_studentmain_state()


class SuspendMonitorAdapter(QObject, BaseAdapterInterface):
    changed = Signal(SuspendState)

    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.timer = QTimer(self)
        self.timer.setInterval(600)
        self.timer.timeout.connect(self.run_task)
        self.last_result = None

    def start(self):
        self.timer.start()
        # QTimer.singleShot(0, self.check_state)

    def stop(self):
        self.timer.stop()

    def run_task(self):
        state = self.check_state()
        if state is not self.last_result:
            self.last_result = state
            self.changed.emit(state)

    def check_state(self):
        """
        :return: Studentmain suspend state
        """
        pid = self.logic.get_pid_form_process_name('studentmain.exe')
        if pid is None:
            return SuspendState.NOT_FOUND
        if self.logic.is_suspended(pid):
            return SuspendState.SUSPENDED
        else:
            return SuspendState.RUNNING


# class UpdateAdapter(QObject, BaseAdapterInterface):
#     changed = Signal(str)
#
#     def __init__(self):
#         super().__init__()
#
#     def start(self):
#         pass
#
#     def stop(self):
#         pass
#
#     def run_task(self):
#         pass

class TerminateAdapter:
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.last_result = None

    def start(self):
        self.run_task()

    def run_task(self):
        pid = self.logic.get_pid_form_process_name('studentmain.exe')
        if pid is None:
            print('studentmain not found')
            return
        self.logic.terminate_process(pid)

    def check_state(self):
        return self.logic.get_studentmain_state()


class StartStudentmainAdapter:
    def __init__(self, logic):
        super().__init__()
        self.logic = logic

    def start(self):
        return self.logic.start_studentmain()


class SuspendStudentmainAdapter:
    def __init__(self, logic):
        super().__init__()
        self.logic = logic

    def start(self):
        pid = self.logic.get_pid_form_process_name('studentmain.exe')

        if pid is None:
            print('studentmain not found')
            return

        suspend_state = self.logic.is_suspended(pid)
        if suspend_state:
            self.resume(pid)
        else:
            self.suspend(pid)

    def suspend(self, pid):
        self.logic.suspend_process(pid)

    def resume(self, pid):
        self.logic.resume_process(pid)
