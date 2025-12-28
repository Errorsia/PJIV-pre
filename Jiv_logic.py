import ctypes
import os
import platform
import re
# import ctypes.wintypes as wintypes
import subprocess
import sys
import time
import winreg

import psutil
import pywintypes
import requests
import win32api
import win32com.client
import win32con
import win32gui
import win32gui_struct
import win32process
from packaging import version

from Jiv_enmus import UpdateState


class JIVLogic:
    def __init__(self, config):
        self.authority_admin = None
        self.system_info = None
        self.studentmain_directory = None
        self.studentmain_path = None
        self.config = config

        self.preparation()

    def preparation(self):
        self.check_operate_system()
        self.authority_admin = self.is_admin()
        if not self.authority_admin:
            if self.privilege_escalation():
                time.sleep(3)
                sys.exit()
            else:
                print("Run without admin")
        else:
            print('Run as admin')

        self.system_info = self.get_system_info()
        key_path = r"SOFTWARE\TopDomain\e-Learning Class Standard\1.00"
        value_name = "TargetDirectory"
        self.studentmain_directory = self.read_registry_value(key_path, value_name)
        self.studentmain_path = os.path.join(self.studentmain_directory, "studentmain.exe")
        print(self.studentmain_path)

    @staticmethod
    def check_operate_system():
        """Check whether OS is Windows nt"""
        if os.name != 'nt':
            sys.exit('UNSUPPORTED SYSTEMS')

    @staticmethod
    def is_admin():
        """Checking whether programme has administrator privilege"""

        authority = ctypes.windll.shell32.IsUserAnAdmin()
        return bool(authority)

    @staticmethod
    def privilege_escalation():
        """
        Try to rerun script as admin
        Uses ShellExecuteW with "runas"
        :return: True if elevation succeeded, False otherwise
        """
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 'runas', sys.executable, ' '.join(sys.argv), None, 1
        )
        return result > 32

    def get_system_info(self):
        """
        Collect system information in a dictionary.

        system: OS name (Windows)
        release: OS release
        version: OS build version
        major: major version number
        minor: minor version number
        build: build number
        platform: platform ID
        service_pack: installed service pack
        architecture: system architecture (64bit, 32bit)
        hotfixes: list of installed hotfixes
        :return: dictionary with system details
        """

        win_ver = sys.getwindowsversion()
        system_info = {
            "system": platform.system(),  # Windows
            "release": platform.release(),  # Major (e.g. 10, 11)
            "version": platform.version(),  # build version
            "major": win_ver.major,  # major version
            "minor": win_ver.minor,  # minor version
            "build": win_ver.build,  # build version
            "platform": win_ver.platform,  # platform ID
            "service_pack": win_ver.service_pack,
            "architecture": platform.architecture(),  # (64bit, 32bit)
            "hotfixes": self.get_hotfixes_winapi()
        }
        return system_info

    @staticmethod
    def get_hotfixes_winapi():
        """
        Retrieve installed Windows hotfixes using the Update API.

        Searches update history, extracts KB identifiers, install dates, and result codes.
        :return: list of dictionaries with hotfix details
        """
        update_session = win32com.client.Dispatch("Microsoft.Update.Session")
        update_searcher = update_session.CreateUpdateSearcher()
        history_count = update_searcher.GetTotalHistoryCount()
        history = update_searcher.QueryHistory(0, history_count)

        hotfixes = []
        for entry in history:
            match = re.search(r"(KB\d+)", entry.Title)
            if match:
                hotfixes.append({
                    "kb": match.group(1),
                    "date": entry.Date,
                    "result": entry.ResultCode
                })
        return hotfixes

    @staticmethod
    def get_hotfixes_powershell():
        cmd = 'powershell "Get-HotFix | Select-Object -Property HotFixID, InstalledOn"'
        output = subprocess.check_output(cmd, shell=True).decode(errors="ignore")
        hotfixes = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("kb"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    hotfixes.append({
                        "KB": parts[0],
                        "InstalledOn": parts[1]
                    })
        return hotfixes

    @staticmethod
    def read_registry_value(key_path, value_name):
        """
        Read a registry value from HKEY_LOCAL_MACHINE.

        Tries both 32-bit and 64-bit views.
        :return: value if found, otherwise None
        """
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
                return winreg.QueryValueEx(key, value_name)[0]
        except FileNotFoundError:
            pass

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                return winreg.QueryValueEx(key, value_name)[0]
        except FileNotFoundError:
            pass

        return None

    def after_ui_launched(self, hwnd):
        pass
        # self.set_window_display_affinity(hwnd)

    def set_window_display_affinity(self, hwnd):
        if self.system_info["major"] >= 10 and self.system_info["build"] >= 19041:
            ctypes.windll.user32.SetWindowDisplayAffinity(int(hwnd), 0x11)
        else:
            ctypes.windll.user32.SetWindowDisplayAffinity(int(hwnd), 0)

    @staticmethod
    def get_process_state(process_name='studentmain.exe'):
        if not process_name.lower().endswith(".exe"):
            process_name += ".exe"

        # for proc in psutil.process_iter(['name']):
        #     if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
        #         return True

        process_iter = psutil.process_iter()
        for proc in process_iter:
            try:
                if proc.name().lower() == process_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return False

    @staticmethod
    def set_window_top_most(hwnd):
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST,
                              0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def start_studentmain(self):
        if os.path.exists(self.studentmain_path):
            try:
                os.startfile(self.studentmain_path)
                return True
            except PermissionError as err:
                print(f"permission error: {err}")
            except Exception as err:
                print(f"error: {err}")
        return False

    @staticmethod
    def taskkill(process_name):
        state = subprocess.run(['TASKKILL', '-F', '-IM', process_name, '-T']).returncode

        if state == 0:
            return True
            # self.logger.info(f'The process ({process_name}) has been terminated (Return code {state})')

        elif state == 128:
            return False

        elif state == 1:
            return False

        else:
            return False

    # WILL BE DELETED IN NEXT VERSION
    # @staticmethod
    # def get_pid_form_process_name(process_name):
    #     """
    #     Get the PID of a process by name.
    #
    #     Iterates through running processes and compares names.
    #     :return: PID if found, otherwise None
    #     """
    #     pid_list = []
    #
    #     if not process_name.lower().endswith(".exe"):
    #         process_name += ".exe"
    #     process_iter = psutil.process_iter()
    #     for proc in process_iter:
    #         try:
    #             if proc.name().lower() == process_name.lower():
    #                 pid_list.append(proc.pid)
    #         except (psutil.NoSuchProcess, psutil.AccessDenied):
    #             continue
    #
    #     if pid_list:
    #         return tuple(pid_list)
    #     else:
    #         return None

    @staticmethod
    def get_pid_from_process_name(process_name):
        """
        Get the PID(s) of a process by name.
        Returns a tuple of PIDs, or None if not found.
        """
        if not process_name.lower().endswith(".exe"):
            process_name += ".exe"

        target = process_name.lower()
        pid_list = []

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == target:
                    pid_list.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return tuple(pid_list) or None

    @staticmethod
    def get_pid_by_name(process_name):
        pids = win32process.EnumProcesses()
        for pid in pids:
            try:
                # noinspection PyUnresolvedReferences
                h_process = win32api.OpenProcess(0x0400 | 0x0010, False, pid)  # QUERY_INFORMATION | VM_READ
                exe_name = win32process.GetModuleFileNameEx(h_process, 0)
                if exe_name.lower().endswith(process_name.lower()):
                    return pid
            except pywintypes.error as err:  # type: ignore
                # Insufficient permissions, permission denied or the process has exited
                print(f"pywintypes.error for PID {pid}: {err}")
                continue
            except OSError as err:
                print(f"OSError for PID {pid}: {err}")
                continue
            except Exception as err:
                print(f"Unexpected error for PID {pid}: {err}")
                continue
            return None

    @staticmethod
    def get_pids_by_path(target_path):
        """
        Return all PIDs whose executable path matches target_path.
        Returns a tuple of PIDs, or None if no match.
        """
        target_path = os.path.abspath(target_path).lower()
        pid_list = []

        for proc in psutil.process_iter(['pid', 'exe']):
            try:
                exe_path = proc.info['exe']
                if exe_path and exe_path.lower() == target_path:
                    pid_list.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return tuple(pid_list) or None

    @staticmethod
    def terminate_process(pid):
        # noinspection PyUnresolvedReferences
        h_process = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
        if not h_process:
            # noinspection PyUnresolvedReferences
            raise Exception(f"OpenProcess failed, error={win32api.GetLastError()}")

        # noinspection PyUnresolvedReferences
        win32api.TerminateProcess(h_process, 1)  # return code 1
        # if not success:
        # noinspection PyUnresolvedReferences
        # raise Exception(f"TerminateProcess failed, error={win32api.GetLastError()}")

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

    @staticmethod
    def is_suspended(pid):
        """
        whether the certain programme is suspended
        :param pid: pid of programme
        :return: whether the certain programme is suspended
        """
        try:
            p = psutil.Process(pid)
            return p.status() == psutil.STATUS_STOPPED
        except psutil.NoSuchProcess:
            return False

    @staticmethod
    def suspend_process(pid):
        try:
            p = psutil.Process(pid)
            p.suspend()
            return True
        except psutil.NoSuchProcess:
            print("Process not found")
            return False
        except PermissionError:
            print('Permission Error in suspending')
            return False

    @staticmethod
    def resume_process(pid):
        try:
            p = psutil.Process(pid)
            p.resume()
            return True
        except psutil.NoSuchProcess:
            print("Process not found")
            return False
        except PermissionError:
            print('Permission Error in resuming')
            return False

    def get_current_version(self) -> str:
        """get current version in config"""
        return self.config.VERSION

    def get_latest_version(self):
        response = requests.get(self.config.UPDATE_URL)
        if response.status_code == 200:
            data = response.json()
            tag = data.get("tag_name")  # Avoiding KeyError
            if tag:
                return tag.lstrip("v")
            else:
                return None

        else:
            raise RuntimeError("Unable to obtain the latest version information")

    def check_update(self):
        """
        whether the latest version

        :return: Latest version string if update is available, else None.
        """
        current_version = self.get_current_version()
        try:
            latest_version = self.get_latest_version()
        except RuntimeError as err:
            print(err)
            return UpdateState.ERROR, str(err)
        except requests.exceptions.SSLError:
            print('requests.exceptions.SSLError')
            return UpdateState.ERROR, 'requests.exceptions.SSLError'
        except Exception as err:
            print(f'An error occurred: {err}')
            return UpdateState.ERROR, str(err)

        if not latest_version:
            return UpdateState.NOT_FOUND, None

        current = version.parse(current_version)
        latest = version.parse(latest_version)

        print(f'latest version: {latest_version}')

        if latest > current:
            return UpdateState.FIND_LATEST, latest_version
        else:
            return UpdateState.IS_LATEST, current_version

    def top_taskmgr(self):
        taskmgr_name_chs = {
            "class_name": "TaskManagerWindow",
            "window_name": "任务管理器",
        }
        taskmgr_name_list = [taskmgr_name_chs]

        hwnd = None

        for taskmgr_name in taskmgr_name_list:
            try:
                hwnd = self.find_window(taskmgr_name.get("class_name"),
                                        taskmgr_name.get("window_name")
                                        )
                if hwnd: break
            except RuntimeError:
                continue

        if hwnd is None:
            raise ValueError('taskmgr not start')

        if self.system_info.get("major") == 10:
            try:
                hm = win32gui.GetMenu(hwnd)
                mii, _ = win32gui_struct.EmptyMENUITEMINFO()
                win32gui.GetMenuItemInfo(hm, 0x7704, False, mii)
                if list(win32gui_struct.UnpackMENUITEMINFO(mii))[1] == 0:
                    win32gui.PostMessage(hwnd, win32con.WM_COMMAND, 0x7704, 0)
            except PermissionError as err:
                print('An error occurred:', err)
            except pywintypes.error as err:  # type: ignore
                print('An error occurred:', err)
                self.set_window_top_most(hwnd)

        else:
            self.set_window_top_most(hwnd)

    @staticmethod
    def find_window(class_name=None, window_name=None):
        if not class_name and not window_name:
            raise ValueError("Must provide class_name or window_name")
        hwnd = win32gui.FindWindow(class_name, window_name)
        if hwnd == 0:
            raise RuntimeError("Window not found")
        return hwnd

    @staticmethod
    def start_file(file_name):
        os.startfile(file_name)

    @staticmethod
    def clean_ifeo_debuggers():
        success_flag = True
        base_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"

        try:
            base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path, 0, winreg.KEY_ALL_ACCESS)
        except PermissionError:
            print("Permission denied")
            return
        except Exception as err:
            print(f"Cannot open IFEO key: {err}")
            return

        try:
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(base_key, index)
                    index += 1
                except OSError:
                    break  # No subkey

                subkey_path = base_path + "\\" + subkey_name

                try:
                    subkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path, 0, winreg.KEY_ALL_ACCESS)
                except PermissionError:
                    continue
                except FileNotFoundError:
                    continue

                try:
                    winreg.QueryValueEx(subkey, "debugger")
                except FileNotFoundError:
                    winreg.CloseKey(subkey)
                    continue
                else:
                    # Find debugger, delete subkey
                    winreg.CloseKey(subkey)
                    try:
                        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, subkey_path)
                        print(f"{subkey_name} has been deleted")
                    except Exception as err:
                        success_flag = False
                        print(f"{subkey_name} cannot be deleted: {err}")

        finally:
            winreg.CloseKey(base_key)

        return success_flag

# self.floatwin.setText(
#     f"窗口标题：{GetWindowText(hwnd)}\n窗口类名：{GetClassName(hwnd)}\n窗口位置：{str(GetWindowRect(hwnd))}\n窗口句柄：{int(hwnd)}\n窗口进程：{procname}")
