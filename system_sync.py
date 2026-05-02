"""
system_sync.py — Механизм синхронизации UI с системными параметрами.
Реализует аудит системы, маппинг состояний и авто-конфигурацию чекбоксов.
"""

import threading
import time
import winreg
import subprocess
import struct

class SystemSync:
    def __init__(self):
        self._observers = {} # {key: [callback_functions]}
        self._states = {}    # {key: current_value}
        self._running = False
        self._lock = threading.Lock()
        self._dispatcher = None # Callback like root.after
    
    def set_dispatcher(self, dispatcher):
        """Устанавливает функцию для выполнения колбэков в главном потоке (напр. root.after)."""
        self._dispatcher = dispatcher

    def register(self, key, callback):
        """Регистрирует колбэк для обновления UI при изменении параметра."""
        with self._lock:
            if key not in self._observers:
                self._observers[key] = []
            self._observers[key].append(callback)
            
        # Сразу возвращаем текущее состояние, если оно уже известно
        if key in self._states:
            callback(self._states[key])

    def start_monitoring(self):
        """Запускает фоновый поток для опроса параметров."""
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def _monitor_loop(self):
        while self._running:
            new_states = self.audit_all()
            with self._lock:
                for key, val in new_states.items():
                    if key not in self._states or self._states[key] != val:
                        self._states[key] = val
                        self._notify(key, val)
            time.sleep(2) # Интервал опроса

    def _notify(self, key, value):
        if key in self._observers:
            for cb in self._observers[key]:
                try:
                    if self._dispatcher:
                        self._dispatcher(0, lambda c=cb, v=value: c(v))
                    else:
                        cb(value)
                except Exception:
                    pass

    def audit_all(self):
        """Опрашивает все поддерживаемые системные параметры."""
        states = {}
        
        # 1. Dark Mode (Apps)
        states["dark_mode"] = self._read_reg(winreg.HKEY_CURRENT_USER, 
                                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 
                                             "AppsUseLightTheme") == 0
        
        # 2. Game Mode
        states["game_mode"] = self._read_reg(winreg.HKEY_CURRENT_USER, 
                                             r"Software\Microsoft\GameBar", 
                                             "AllowAutoGameMode") == 1
        
        # 3. HAGS (Hardware-accelerated GPU scheduling)
        states["hags"] = self._read_reg(winreg.HKEY_LOCAL_MACHINE, 
                                        r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 
                                        "HwSchMode") == 2
        
        # 4. Clipboard History
        states["clipboard_history"] = self._read_reg(winreg.HKEY_CURRENT_USER, 
                                                     r"Software\Microsoft\Clipboard", 
                                                     "EnableClipboardHistory") == 1
        
        # 5. High Performance Mode (Power Plan)
        states["high_perf"] = self._check_power_plan("8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c") or \
                              self._check_power_plan("e9a42b02-d5df-448d-aa00-03f14749eb61")
        
        # 6. Wi-Fi Status
        states["wifi_enabled"] = self._check_wifi()
        
        # 7. Bluetooth Status
        states["bluetooth_enabled"] = self._check_service("bthserv")

        return states

    def _read_reg(self, hive, key_path, name):
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return val
        except Exception:
            return None

    def _check_power_plan(self, guid_prefix):
        try:
            res = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True)
            output = res.stdout.decode('cp866', errors='ignore')
            return guid_prefix.lower() in output.lower()
        except Exception:
            return False

    def _check_wifi(self):
        try:
            res = subprocess.run(["netsh", "interface", "show", "interface"], capture_output=True)
            output = res.stdout.decode('cp866', errors='ignore')
            # Ищем интерфейс Wi-Fi и его состояние
            return "Wi-Fi" in output and ("Connected" in output or "Enabled" in output)
        except Exception:
            return False

    def _check_service(self, service_name):
        try:
            res = subprocess.run(["sc", "query", service_name], capture_output=True)
            output = res.stdout.decode('cp866', errors='ignore')
            return "RUNNING" in output
        except Exception:
            return False

# Глобальный экземпляр для приложения
sync_engine = SystemSync()
