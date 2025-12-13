# adapter.py
# from threading import Thread

from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QApplication

from Jiv_enmus import SuspendState


class AdapterManager(QObject):
    ui_change = Signal(str, object)

    def __init__(self, logic, gui):
        super().__init__()
        self.on_demand_objects = {}
        self.logic = logic
        self.gui = gui

        self.lifelong_adapters = []
        self.lifelong_objects = {}

        self.terminate_adapter = self.start_adapter = self.suspend_studentmain_adapter = self.run_taskmgr_adapter = None

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
        self.run_taskmgr_adapter = RunTaskmgrAdapter(self.logic)

        self.init_run_taskmgr_adapter()

    def init_run_taskmgr_adapter(self):
        thread = QThread()
        self.run_taskmgr_adapter.moveToThread(thread)

        thread.started.connect(self.run_taskmgr_adapter.start)

        self.run_taskmgr_adapter.changed.connect(lambda result, w=self.run_taskmgr_adapter:
                                                 self.ui_change.emit(type(w).__name__, result))
        self.run_taskmgr_adapter.request_top.connect(self.logic.top_taskmgr)
        self.run_taskmgr_adapter.request_top.connect(lambda: print('request_top received'))

        self.lifelong_objects[self.run_taskmgr_adapter] = thread
        self.on_demand_objects[self.run_taskmgr_adapter] = thread

        thread.start()

    def start_all(self):
        for adapter in self.lifelong_adapters:
            thread = QThread()
            adapter.moveToThread(thread)

            thread.started.connect(adapter.start)
            # Wrap with lambda and send the adapter class name and result together
            adapter.changed.connect(lambda result, w=adapter:
                                    self.ui_change.emit(type(w).__name__, result))

            self.lifelong_objects[adapter] = thread
            thread.start()

    def stop_all(self):
        """Stop all adapters and safely exit the thread"""
        for adapter, thread in self.lifelong_objects.items():
            adapter.stop()
            thread.quit()
            thread.wait()
            adapter.deleteLater()
            thread.deleteLater()

    def pop_ondemand_object(self, adapter):
        if adapter in self.on_demand_objects:
            return self.on_demand_objects.pop(adapter, None)
        # if thread in self.on_demand_objects:
        #     self.on_demand_objects.pop(thread)
        # adapter.deleteLater() and thread.deleteLater()

    def cleanup_on_demand(self, adapter, thread):
        self.pop_ondemand_object(adapter)
        adapter.moveToThread(QApplication.instance().thread())
        # adapter.deleteLater()
        # thread.deleteLater()

    def terminate_studentmain(self):
        self.terminate_adapter.start()

    def start_studentmain(self):
        self.start_adapter.start()

    def suspend_resume_studentmain(self):
        self.suspend_studentmain_adapter.start()

    # def run_taskmgr(self):
    #     thread = QThread()
    #     self.run_taskmgr_adapter.moveToThread(thread)
    #
    #     thread.started.connect(self.run_taskmgr_adapter.start)
    #     # Wrap with lambda and send the adapter class name and result together
    #     self.run_taskmgr_adapter.changed.connect(lambda result, w=self.run_taskmgr_adapter:
    #                             self.ui_change.emit(type(w).__name__, result))
    #
    #     self.run_taskmgr_adapter.finished.connect(self.run_taskmgr_adapter.stop)
    #     self.run_taskmgr_adapter.finished.connect(thread.quit)
    #     self.run_taskmgr_adapter.finished.connect(
    #         self.run_taskmgr_adapter.moveToThread(QApplication.instance().thread()))
    #     thread.finished.connect(thread.deleteLater)
    #
    #     thread.start()

    def run_taskmgr(self):
        print('Topmost taskmgr triggered')

        if self.run_taskmgr_adapter.is_running():
            print("taskmgr adapter already running")
            return

        # call in different threads, causes issue in slot connection in qtimer
        # self.run_taskmgr_adapter.run_task()

        self.run_taskmgr_adapter.trigger_run.emit()

        # QMetaObject.invokeMethod(
        #     self.run_taskmgr_adapter,
        #     "run_task",
        #     Qt.QueuedConnection
        # )


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
        return self.logic.get_process_state('studentmain.exe')


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
        return self.logic.get_process_state('studentmain.exe')


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


class RunTaskmgrAdapter(QObject):
    trigger_run = Signal()
    changed = Signal()
    request_top = Signal()
    finished = Signal()

    def __init__(self, logic):
        super().__init__()
        # self.running = False
        # self.cnt = 0
        self.running = None
        self.cnt = None
        self.timer = None
        self.logic = logic

    def start(self):
        self.running = False
        self.cnt = 0
        self.timer = QTimer(self)

        self.timer.setInterval(100)
        self.timer.timeout.connect(self.is_taskmgr_alive)

        self.trigger_run.connect(self.run_task)

    def run_task(self):
        self.cnt = 0
        self.running = True
        self.logic.start_file("taskmgr")
        print("adapter.start called")
        self.timer.start()
        print('timer started')

    def is_taskmgr_alive(self):
        print(f'cnt: {self.cnt}')
        self.cnt += 1
        if self.logic.get_process_state('taskmgr.exe'):
            self.request_top.emit()
            self.stop()
        if self.cnt >= 30: # 3s time out
            print("Find taskmgr Time out")
            self.stop()

    def stop(self):
        self.running = False
        self.timer.stop()

    def is_running(self):
        return self.running
