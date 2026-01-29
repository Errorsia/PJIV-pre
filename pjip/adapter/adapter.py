# adapter.py
# from threading import Thread

from PySide6.QtCore import QObject, Signal, QTimer, QThread, QRunnable, QThreadPool
from PySide6.QtGui import QGuiApplication

from pjip.config import build_config
from pjip.core.enums import PidStatus

from .polling import MonitorAdapter, SuspendMonitorAdapter, GetStudentmainPasswordAdapter, UpdateAdapter
from .polling_manager import PollingManager


class AdapterManager(QObject):
    ui_change = Signal(str, object)

    def __init__(self, logic, gui, runtime_status):
        super().__init__()
        self.on_demand_objects = {}
        self.logic = logic
        self.gui = gui
        self.runtime_status = runtime_status

        self.polling = PollingManager()

        self.lifelong_adapters = []
        self.lifelong_objects = {}

        self.terminate_pid_adapter = self.terminate_process_adapter = self.start_adapter = None
        self.suspend_studentmain_adapter = self.run_taskmgr_adapter = self.update_adapter = None
        self.clean_ifeo_debuggers_adapter = None

        self.init_threadpools()
        self.init_workers()
        self.connect_signals()
        self.start_all()

    def init_threadpools(self):
        self.terminate_threadpool = QThreadPool()
        self.terminate_threadpool.setMaxThreadCount(2)

    def init_workers(self):
        self.polling.add(MonitorAdapter(self.logic))
        self.polling.add(SuspendMonitorAdapter(self.logic))
        self.polling.add(GetStudentmainPasswordAdapter(self.logic, self.runtime_status))
        # self.lifelong_adapters.append(DatabaseAdapter(logic, 2000))
        # self.lifelong_adapters.append(NetworkAdapter(logic, 5000))

        self.update_adapter = UpdateAdapter(self.logic)
        self.polling.add(self.update_adapter)

        self.terminate_pid_adapter = TerminatePIDAdapter(self.logic, self.runtime_status.pid, self.terminate_threadpool)

        self.terminate_process_adapter = TerminateProcessAdapter(self.logic, self.runtime_status.current_process_name,
                                                                 self.terminate_pid_adapter)

        self.run_taskmgr_adapter = RunTaskmgrAdapter(self.logic)

        self.suspend_studentmain_adapter = SuspendStudentmainAdapter(self.logic)
        self.start_adapter = StartStudentmainAdapter(self.logic)
        self.clean_ifeo_debuggers_adapter = CleanIFEODebuggersAdapter(self.logic)
        self.copy_to_clipboard_adapter = CopyToClipboardAdapter()
        self.terminate_custom_process_adapter = TerminateCustomProcessAdapter(self.logic, self.terminate_pid_adapter,
                                                                              self.terminate_process_adapter)

        self.init_run_taskmgr_adapter()

    def init_run_taskmgr_adapter(self):
        thread = QThread()
        self.run_taskmgr_adapter.moveToThread(thread)

        thread.started.connect(self.run_taskmgr_adapter.start)

        self.run_taskmgr_adapter.change.connect(lambda result, w=self.run_taskmgr_adapter:
                                                self.ui_change.emit(type(w).__name__, result))

        self.lifelong_objects[self.run_taskmgr_adapter] = thread

        thread.start()

    def connect_signals(self):
        for adapter in self.polling.adapters:
            adapter.change.connect(
                lambda result, w=adapter:
                self.ui_change.emit(type(w).__name__, result)
            )

    def start_all(self):
        self.polling.start()

    def stop_all(self):
        """Stop all adapters and safely exit the thread"""
        self.polling.stop()

    def ui_launched(self):
        pass

    def wait_for_pools(self):
        self.terminate_threadpool.waitForDone()

    def quit_all(self):
        self.stop_all()
        self.wait_for_pools()

    def terminate_studentmain(self):
        self.terminate_process_adapter.run_async(build_config.E_CLASSROOM_PROGRAM_NAME)

    def start_studentmain(self):
        self.start_adapter.start()

    def suspend_resume_studentmain(self):
        self.suspend_studentmain_adapter.start()

    def run_taskmgr(self):
        print('Topmost taskmgr triggered')

        if self.run_taskmgr_adapter.is_running():
            print("taskmgr adapter already running")
            return

        self.run_taskmgr_adapter.trigger_run.emit()

        # QMetaObject.invokeMethod(
        #     self.run_taskmgr_adapter,
        #     "run_task",
        #     Qt.QueuedConnection
        # )

    def clean_ifeo_debuggers(self):
        self.clean_ifeo_debuggers_adapter.start()
        print('ifeo cleaned')

    def get_update(self):
        if self.update_adapter.is_running():
            print("update adapter already running")
            return

        self.update_adapter.trigger_run.emit()

    def get_current_version(self):
        return self.logic.get_current_version()

    def terminate_custom_process(self, process_info):
        self.terminate_custom_process_adapter.trigger_run.emit(process_info)

    def copy_studentmain_password_to_clipboard(self):
        self.copy_to_clipboard(self.runtime_status.studentmain_password)

    def copy_to_clipboard(self, content):
        self.copy_to_clipboard_adapter.copy_to_clipboard(content)


class RunTaskmgrAdapter(QObject):
    trigger_run = Signal()
    change = Signal()

    def __init__(self, logic):
        super().__init__()
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

    def is_taskmgr_alive(self):
        self.cnt += 1
        if self.logic.get_process_state('taskmgr.exe'):
            self.logic.top_taskmgr()
            self.stop()
        if self.cnt >= 30:  # 3s time out
            print("Find taskmgr Time out")
            self.stop()

    def stop(self):
        self.running = False
        self.timer.stop()

    def is_running(self):
        return self.running


class TerminateCustomProcessAdapter(QObject):
    change = Signal(object)
    trigger_run = Signal(str)

    MAX_PID = 2_147_483_647

    def __init__(self, logic, terminate_pid_adapter, terminate_process_adapter):
        super().__init__()
        self.logic = logic
        self.terminate_pid_adapter = terminate_pid_adapter
        self.terminate_process_adapter = terminate_process_adapter

        self.start()

    def start(self):
        self.trigger_run.connect(self.run_task)

    def run_task(self, process_info: str):
        if self.is_valid_pid(process_info):
            process_pid = int(process_info)
            if self.pid_exists(process_pid):
                self.terminate_pid(process_pid)
            else:
                process_name = self.handle_process_name(process_info)
                self.terminate_process(process_name)

        else:
            process_name = self.handle_process_name(process_info)
            self.terminate_process(process_name)

    def is_valid_pid(self, s: str) -> bool:
        if not s.isdigit():
            return False
        try:
            pid = int(s)
        except ValueError:
            return False
        return 0 < pid <= self.MAX_PID

    def pid_exists(self, pid: int):
        return self.logic.pid_exists(pid) == PidStatus.EXISTS

    def terminate_pid(self, pid):
        self.terminate_pid_adapter.run_async((pid,))

    def terminate_process(self, process_name: str):
        self.terminate_process_adapter.run_async(process_name)

    @staticmethod
    def handle_process_name(process_name: str) -> str:
        process_name = process_name.strip()
        if not process_name.lower().endswith(".exe"):
            return process_name + ".exe"
        return process_name


# ################

class TerminatePIDTask(QRunnable):
    def __init__(self, logic, pids):
        super().__init__()
        self.logic = logic
        self.pids = pids

    def run(self):
        if not self.pids:
            print("PID not found")
            return
        for pid in self.pids:
            try:
                self.logic.terminate_process(pid)
            except RuntimeError as err:
                print(err)


class TerminatePIDAdapter(QObject):
    change = Signal(str)

    def __init__(self, logic, current_pid, /, pool=None):
        super().__init__()
        self.logic = logic
        self.current_pid = current_pid
        self.pool = pool or QThreadPool.globalInstance()

    def run_async(self, pids):
        other_pids = self.split_current_pid(pids)
        if other_pids:
            task = TerminatePIDTask(self.logic, other_pids)
            self.pool.start(task)

    def run_sync(self, pids):
        other_pids = self.split_current_pid(pids)
        if other_pids:
            TerminatePIDTask(self.logic, other_pids).run()

    @staticmethod
    def format_pids(pids: int | Iterable[int]):
        if isinstance(pids, int):
            return (pids,)
        return tuple(pids)

    def split_current_pid(self, pids):
        """Check if pids contains current_pid and return the rest."""
        if self.current_pid in pids:
            self.change.emit('Cannot terminate the current process(form pid)')
            print('Cannot terminate the current process(form pid)')
        other_pids = [pid for pid in pids if pid != self.current_pid]
        return other_pids


class TerminateProcessAdapter(QObject):
    """Terminate process, rely on PID adapter"""
    change = Signal(str)

    def __init__(self, logic, current_process_name, pid_adapter: TerminatePIDAdapter, /):
        super().__init__()
        self.logic = logic
        self.pid_adapter = pid_adapter
        self.current_process_name = current_process_name

    def run_async(self, process_name):
        if process_name == self.current_process_name:
            self.change.emit('Cannot terminate the current process')
            print('Cannot terminate the current process')
            return

        pids = self.logic.get_pid_from_process_name(process_name)
        if pids:
            self.pid_adapter.run_async(pids)
        else:
            print(f'Invalid pids: {pids}')

    def run_sync(self, process_name):
        if process_name == self.current_process_name:
            self.change.emit('Cannot terminate the current process')
            return

        pids = self.logic.get_pid_from_process_name(process_name)
        self.pid_adapter.run_sync(pids)


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
        pids = self.logic.get_pid_from_process_name(build_config.E_CLASSROOM_PROGRAM_NAME)

        if pids is None:
            print(f'{build_config.E_CLASSROOM_PROGRAM_NAME} not found')

        for pid in pids:
            suspend_state = self.logic.is_suspended(pid)
            if suspend_state:
                self.resume(pid)
            else:
                self.suspend(pid)

    def suspend(self, pid):
        self.logic.suspend_process(pid)

    def resume(self, pid):
        self.logic.resume_process(pid)


class CleanIFEODebuggersAdapter:
    def __init__(self, logic):
        super().__init__()
        self.logic = logic

    def start(self):
        self.logic.clean_ifeo_debuggers()


class CopyToClipboardAdapter:
    def __init__(self):
        self.clipboard = QGuiApplication.clipboard()

    def copy_to_clipboard(self, content: str):
        self.clipboard.setText(content)
