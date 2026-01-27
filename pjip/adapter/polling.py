from PySide6.QtCore import QObject, Signal, QTimer

from pjip.config import build_config
from pjip.core.enums import SuspendState


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


class GetStudentmainPasswordAdapter(QObject, BaseAdapterInterface):
    change = Signal(SuspendState)

    def __init__(self, logic, runtime_status):
        super().__init__()
        self.logic = logic
        self.timer = QTimer(self)
        self.timer.setInterval(30000)
        self.timer.timeout.connect(self.run_task)
        self.last_result = None
        self.runtime_status = runtime_status

    def start(self):
        self.timer.start()
        QTimer.singleShot(0, self.run_task)

    def stop(self):
        self.timer.stop()

    def run_task(self):
        state = self.get_studentmain_password()
        if state != self.last_result:
            self.last_result = state
            self.runtime_status.update_studentmain_password(state)
            self.change.emit(state)

    def get_studentmain_password(self):
        """
        :return: Studentmain password
        """
        return self.logic.decode_studentmain_password()


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
