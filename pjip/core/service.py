import threading
from abc import ABC, abstractmethod

import pywintypes


class ServiceManager:
    def __init__(self, logic, runtime_status):
        super().__init__()
        self.logic = logic
        self.runtime_status = runtime_status
        self.services = []

        self.threads = {}
        self.hwnd = None

        self.init_hwnd()

        self.init_services()
        self.start_all()

    def init_hwnd(self):
        self.hwnd = int(self.runtime_status.window_handle)
        print(f'Hwnd: {self.hwnd}')

    def init_services(self):
        self.services.append(TopMostService(50, self.logic, self.hwnd))
        self.services.append(HideService(500, self.logic, self.hwnd))

    def start_all(self):
        for service in self.services:
            thread = threading.Thread(target=service.start, daemon=True)
            self.threads[service] = thread
            thread.start()

    def stop_all(self):
        """Stop services and quit"""
        for service, thread in self.threads.items():
            service.stop()


class BaseServiceInterface(ABC):
    @abstractmethod
    def start(self):
        raise NotImplementedError("Subclasses must implement start()")

    @abstractmethod
    def stop(self):
        raise NotImplementedError("Subclasses must implement stop()")

    @abstractmethod
    def run_task(self):
        raise NotImplementedError("Subclasses must implement run_task()")


class TopMostService(BaseServiceInterface):
    def __init__(self, interval, logic, hwnd):
        """
        :param interval: millisecond
        :param logic: logic module
        :param hwnd: hwnd of top window
        """
        super().__init__()

        self.stop_flag = threading.Event()
        self.interval = interval / 1000
        self.logic = logic

        self.run = True
        self.hwnd = hwnd

    def start(self):
        self.run_task()

    def stop(self):
        self.stop_flag.set()

    def run_task(self):
        while not self.stop_flag.is_set():
            try:
                self.logic.set_window_top_most(self.hwnd)
            except pywintypes.error as err:  # type: ignore
                print('pywintypes.error')
                print(err)
            except Exception as err:
                print(err)
            if self.stop_flag.wait(self.interval):
                break


class HideService(BaseServiceInterface):
    def __init__(self, interval, logic, hwnd):
        """
        :param interval: run interval (millisecond)
        :param logic: logic module
        :param hwnd: hwnd of top window
        """
        super().__init__()

        self.stop_flag = threading.Event()
        self.interval = interval / 1000
        self.logic = logic

        self.run = True
        self.hwnd = hwnd

    def start(self):
        self.run_task()

    def stop(self):
        self.stop_flag.set()

    def run_task(self):
        while not self.stop_flag.is_set():
            self.logic.set_window_display_affinity(self.hwnd)
            if self.stop_flag.wait(self.interval):
                break
