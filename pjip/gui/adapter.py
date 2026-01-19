# adapter.py
# from threading import Thread

from PySide6.QtCore import QObject, Signal, QTimer, QThread, QRunnable, QThreadPool

from pjip.config import build_config
from pjip.core.enums import SuspendState, PidStatus


class AdapterManager(QObject):
    ui_change = Signal(str, object)

    def __init__(self, logic, gui, runtime_status):
        super().__init__()
        self.on_demand_objects = {}
        self.logic = logic
        self.gui = gui
        self.runtime_status = runtime_status

        self.lifelong_adapters = []
        self.lifelong_objects = {}

        self.terminate_pid_adapter = self.terminate_process_adapter = self.start_adapter = None
        self.suspend_studentmain_adapter = self.run_taskmgr_adapter = self.update_adapter = None
        self.clean_ifeo_debuggers_adapter = None

        self.init_threadpools()
        self.init_workers()
        self.start_all()

    def init_threadpools(self):
        self.terminate_threadpool = QThreadPool()
        self.terminate_threadpool.setMaxThreadCount(2)

    def init_workers(self):
        self.lifelong_adapters.append(MonitorAdapter(self.logic))
        self.lifelong_adapters.append(SuspendMonitorAdapter(self.logic))
        # self.lifelong_adapters.append(DatabaseAdapter(logic, 2000))
        # self.lifelong_adapters.append(NetworkAdapter(logic, 5000))

        self.update_adapter = UpdateAdapter(self.logic)
        self.lifelong_adapters.append(self.update_adapter)

        self.terminate_pid_adapter = TerminatePIDAdapter(self.logic, self.runtime_status.pid, self.terminate_threadpool)
        # self.lifelong_adapters.append(self.terminate_pid_adapter)

        self.terminate_process_adapter = TerminateProcessAdapter(self.logic, self.runtime_status.current_process_name,
                                                                 self.terminate_pid_adapter)
        # self.lifelong_adapters.append(self.terminate_process_adapter)

        self.run_taskmgr_adapter = RunTaskmgrAdapter(self.logic)

        self.suspend_studentmain_adapter = SuspendStudentmainAdapter(self.logic)
        self.start_adapter = StartStudentmainAdapter(self.logic)
        self.clean_ifeo_debuggers_adapter = CleanIFEODebuggersAdapter(self.logic)
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

    def start_all(self):
        for adapter in self.lifelong_adapters:
            thread = QThread()
            adapter.moveToThread(thread)

            thread.started.connect(adapter.start)
            # Wrap with lambda and send the adapter class name and result together
            adapter.change.connect(lambda result, w=adapter:
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

    def get_studentmain_password(self):
        pass


class BaseAdapterInterface:
    def start(self):
        raise NotImplementedError("Subclasses must implement start()")

    def stop(self):
        raise NotImplementedError("Subclasses must implement stop()")

    def run_task(self):
        raise NotImplementedError("Subclasses must implement run_task()")


class MonitorAdapter(QObject, BaseAdapterInterface):
    change = Signal(bool)

    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.timer = QTimer(self)
        self.timer.setInterval(500)
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
            self.change.emit(state)

    def check_state(self):
        return self.logic.get_process_state(build_config.E_CLASSROOM_PROGRAM_NAME)


class SuspendMonitorAdapter(QObject, BaseAdapterInterface):
    change = Signal(SuspendState)

    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.timer = QTimer(self)
        self.timer.setInterval(500)
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
            self.change.emit(state)

    def check_state(self):
        """
        :return: Studentmain suspend state
        """
        pids = self.logic.get_pid_from_process_name(build_config.E_CLASSROOM_PROGRAM_NAME)
        if pids is None:
            return SuspendState.NOT_FOUND
        # Same logic as the earlier method, may cause bug
        # If a process's name is studentmain, but it's not the real one, this can suspend the wrong process
        pid = pids[0]
        if self.logic.is_suspended(pid):
            return SuspendState.SUSPENDED
        else:
            return SuspendState.RUNNING


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


class UpdateAdapter(QObject, BaseAdapterInterface):
    change = Signal(object)
    trigger_run = Signal()

    def __init__(self, logic):
        super().__init__()
        self.running = None
        self.logic = logic

    def start(self):
        self.running = False
        self.trigger_run.connect(self.run_task)

        self.run_task()

    def stop(self):
        self.running = False

    def run_task(self):
        if self.is_running():
            print('another getting update is running, exit')
            return
        self.running = True
        state, content = self.logic.check_update()

        self.change.emit((state, content))
        self.stop()

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
            self.logic.terminate_process(pid)


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
        self.pid_adapter.run_async(pids)

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


class GetStudentmainPasswordAdapter:
    def __init__(self, logic):
        super().__init__()
        self.logic = logic

    def start(self):
        self.logic.decode_studentmain_password()
