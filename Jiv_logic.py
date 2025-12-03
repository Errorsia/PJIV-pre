import ctypes
# import ctypes.wintypes as wintypes
import subprocess

import psutil
import win32gui, win32con, win32api


class JIVLogic:
    def __init__(self):
        pass

    @staticmethod
    def is_admin():
        """Checking whether programme has administrator privilege"""

        authority = ctypes.windll.shell32.IsUserAnAdmin()
        return bool(authority)

    @staticmethod
    def get_studentmain_state():
        state = subprocess.run("tasklist|find /i \"studentmain.exe\"", shell=True).returncode
        return not state

    @staticmethod
    def set_window_top_most(hwnd):
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST,
                              0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    @staticmethod
    def taskkill(process_name):
        state = subprocess.run(['TASKKILL', '-F', '-IM', process_name, '-T']).returncode

        if state == 0:
            return True
            # self.logger.info(f'The process ({process_name}) has been terminated (Return code {state})')

        elif state == 128:
            return False
            # self.logger.warning(f'The process ({process_name}) not found (Return code {state})')

        elif state == 1:
            return False
            # self.logger.warning(
                # f'The process ({process_name}) could not be terminated (Return code {state})')

        else:
            return False
            # self.logger.warning(f'Unknown Error (Return code {state})')

    @staticmethod
    def get_pid_form_process_name():
        pid = None
        pids = psutil.process_iter()
        for p in pids:
            if p.name().lower() == "studentmain.exe":
                pid = psutil.Process(p.pid)
                break

        return pid

    @staticmethod
    def terminate_process(pid):

        # noinspection PyUnresolvedReferences
        h_process = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
        if not h_process:
            # noinspection PyUnresolvedReferences
            raise Exception(f"OpenProcess failed, error={win32api.GetLastError()}")

        # noinspection PyUnresolvedReferences
        success = win32api.TerminateProcess(h_process, 1) # return code 1
        if not success:
            # noinspection PyUnresolvedReferences
            raise Exception(f"TerminateProcess failed, error={win32api.GetLastError()}")

        # h_process = win32api.OpenProcess(win32con.PROCESS_TERMINATE | win32con.SYNCHRONIZE, False, pid)
        # if not h_process:
        #     raise Exception(f"OpenProcess failed, error={win32api.GetLastError()}")
        #
        # success = win32api.TerminateProcess(h_process, 1)
        # if not success:
        #     raise Exception(f"TerminateProcess failed, error={win32api.GetLastError()}")
        #
        # result = win32event.WaitForSingleObject(h_process, 5000)
        # if result == win32event.WAIT_OBJECT_0:
        #     exit_code = win32process.GetExitCodeProcess(h_process)
        #     print(f"Process terminated with exit code {exit_code}")
        # else:
        #     print("Timeout waiting for process to terminate")


# # load kernel32.dll
# kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
#
# # Define Function Prototype
# TerminateThread = kernel32.TerminateThread
# TerminateThread.argtypes = [wintypes.HANDLE, wintypes.DWORD]
# TerminateThread.restype = wintypes.BOOL
#
# TerminateProcess = kernel32.TerminateProcess
# TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
# TerminateProcess.restype = wintypes.BOOL
#
# PROCESS_TERMINATE = 0x0001
# OpenProcess = kernel32.OpenProcess
# OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
# OpenProcess.restype = wintypes.HANDLE
#
# pid = 1234
# hProcess = OpenProcess(PROCESS_TERMINATE, False, pid)
#
# if hProcess:
#     result = TerminateProcess(hProcess, 1)  # return code 1
#     print("TerminateProcess result:", result)
# else:
#     print("Failed to open process")

# # load ntdll.dll
# ntdll = ctypes.WinDLL("ntdll")
#
# # Define NtTerminateProcess function Prototype
# NtTerminateProcess = ntdll.NtTerminateProcess
# NtTerminateProcess.argtypes = [wintypes.HANDLE, wintypes.NTSTATUS]
# NtTerminateProcess.restype = wintypes.NTSTATUS
#
# # load kernel32.dll to open process
# kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
#
# OpenProcess = kernel32.OpenProcess
# OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
# OpenProcess.restype = wintypes.HANDLE
#
# CloseHandle = kernel32.CloseHandle
# CloseHandle.argtypes = [wintypes.HANDLE]
# CloseHandle.restype = wintypes.BOOL
#
# # Define constant
# PROCESS_TERMINATE = 0x0001
#
# pid = 1234
# hProcess = OpenProcess(PROCESS_TERMINATE, False, pid)
#
# if hProcess:
#     status = NtTerminateProcess(hProcess, 1)  # Exit code 1
#     print(f"NtTerminateProcess returns NTSTATUS: 0x{status:08X}")
#     CloseHandle(hProcess)
# else:
#     print("cannot open process")


