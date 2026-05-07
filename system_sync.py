"""
system_sync.py — Механизм синхронизации UI с системными параметрами.
Реализует аудит системы, маппинг состояний и авто-конфигурацию чекбоксов.
"""

import threading
import time
import winreg
import subprocess
import struct
from tweaks import (
    run_cmd_bytes,
    is_launch_to_this_pc, is_recycle_bin_in_nav,
    is_recycle_bin_hidden_on_desktop, is_end_task_enabled,
)
from system_info import get_ram_info

def _safe_widget_call(widget, method_name, *args, **kwargs):
    """Safely calls a method on a widget only if it still exists."""
    try:
        if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
            method = getattr(widget, method_name)
            method(*args, **kwargs)
            return True
    except Exception as e:
        print(f"Widget call failed: {e}")
    return False


class SystemSync:
    def __init__(self):
        self._observers = {} # {key: [callback_functions]}
        self._states = {}    # {key: current_value}
        self._running = False
        self._lock = threading.Lock()
        self._dispatcher = None # Callback like root.after
        
        # Кэширование и планирование
        self._cache = {} 
        self._cache_time = {}
        self._cycle_count = 0

    def set_dispatcher(self, dispatcher):
        """Устанавливает функцию для выполнения колбэков в главном потоке (напр. root.after)."""
        self._dispatcher = dispatcher

    def register(self, key, callback):
        """Регистрирует колбэк для обновления UI при изменении параметра."""
        with self._lock:
            if key not in self._observers:
                self._observers[key] = []
            self._observers[key].append(callback)
            
        # Сразу возвращаем текущее состояние через dispatcher, если оно уже известно
        # и dispatcher готов (главный поток запущен)
        if key in self._states and self._dispatcher:
            try:
                self._dispatcher(0, lambda c=callback, v=self._states[key]: c(v))
            except Exception as e:
                print(f"Error during initial callback dispatch for {key}: {e}")

    def start_monitoring(self):
        """Запускает фоновый поток для опроса параметров."""
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def _monitor_loop(self):
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self._running:
            try:
                # Разделяем быстрые и медленные задачи
                new_states = self._fast_audit()
                
                # Медленные задачи раз в 10 циклов (~30 секунд)
                if self._cycle_count % 10 == 0:
                    new_states.update(self._slow_audit())
                
                with self._lock:
                    for key, val in new_states.items():
                        # Специальная проверка для ОЗУ, чтобы не спамить
                        if key == "ram_info":
                            old_val = self._states.get(key, "")
                            if self._is_ram_change_significant(old_val, val):
                                self._states[key] = val
                                self._notify(key, val)
                            continue

                        if key not in self._states or self._states[key] != val:
                            self._states[key] = val
                            self._notify(key, val)
                
                self._cycle_count += 1
                consecutive_errors = 0  # Reset error counter on success
                time.sleep(10)
                
            except Exception as e:
                consecutive_errors += 1
                print(f"Monitor loop error {consecutive_errors}/{max_consecutive_errors}: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print("Too many consecutive errors, stopping monitoring")
                    self._running = False
                    break
                
                # Wait longer after errors to prevent rapid error loops
                time.sleep(10) 

    def _is_ram_change_significant(self, old_str: str, new_val: str) -> bool:
        """Возвращает True, если процент использования ОЗУ изменился более чем на 1.5%."""
        if not old_str: return True
        try:
            import re
            def get_pct(s):
                m = re.search(r"\((\d+\.?\d*)%\)", s)
                return float(m.group(1)) if m else 0
            return abs(get_pct(old_str) - get_pct(new_val)) >= 1.5
        except Exception:
            return True

    def _notify(self, key, value):
        if key not in self._observers:
            return
            
        # Create a copy of the list to avoid modification during iteration
        callbacks = self._observers[key].copy()
        for cb in callbacks:
            try:
                # Pre-check: if callback is bound to a widget, verify widget exists
                widget = None
                if hasattr(cb, '__self__') and hasattr(cb.__self__, 'winfo_exists'):
                    widget = cb.__self__
                    if not widget.winfo_exists():
                        # Widget destroyed, remove callback
                        with self._lock:
                            if key in self._observers and cb in self._observers[key]:
                                self._observers[key].remove(cb)
                        continue
                
                if self._dispatcher:
                    # Wrap callback with comprehensive exception handling
                    def safe_callback(c=cb, v=value, w=widget, k=key):
                        try:
                            # Double-check widget existence right before execution
                            if w and not w.winfo_exists():
                                return
                            c(v)
                        except Exception as e:
                            print(f"Callback execution failed for {k}: {e}")
                            # Remove the problematic callback to prevent repeated exceptions
                            try:
                                with self._lock:
                                    if k in self._observers and c in self._observers[k]:
                                        self._observers[k].remove(c)
                            except Exception:
                                pass  # Ignore cleanup errors
                    
                    try:
                        # Use try/except around dispatcher call to catch main thread errors
                        self._dispatcher(0, safe_callback)
                    except Exception as e:
                        print(f"Dispatcher error for {key}: {e}")
                        # This typically means main thread is not ready - wait and retry once
                        import time
                        time.sleep(0.1)
                        try:
                            self._dispatcher(0, safe_callback)
                        except Exception as e2:
                            print(f"Dispatcher retry failed for {key}: {e2}")
                            # Remove callback that's causing persistent dispatcher issues
                            with self._lock:
                                if key in self._observers and cb in self._observers[key]:
                                    self._observers[key].remove(cb)
                else:
                    # Direct call if no dispatcher - this should be avoided but handled safely
                    try:
                        # Check if we're in main thread before direct GUI updates
                        import threading
                        if threading.current_thread() is threading.main_thread():
                            cb(value)
                        else:
                            print(f"Warning: Attempting direct GUI update from background thread for {key}")
                    except Exception as e:
                        print(f"Direct callback error for {key}: {e}")
                        with self._lock:
                            if key in self._observers and cb in self._observers[key]:
                                self._observers[key].remove(cb)
                        
            except Exception as e:
                # Remove the problematic callback to prevent repeated exceptions
                print(f"Callback setup error for {key}: {e}")
                try:
                    with self._lock:
                        if key in self._observers and cb in self._observers[key]:
                            self._observers[key].remove(cb)
                except Exception:
                    pass  # Ignore cleanup errors
                continue

    def _fast_audit(self) -> dict:
        """Реестровые и легкие проверки (выполняются каждые 10 сек)."""
        states = {}
        # 1. Dark Mode
        states["dark_mode"] = self._read_reg(winreg.HKEY_CURRENT_USER, 
                                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 
                                             "AppsUseLightTheme") == 0
        # 2. Game Mode
        states["game_mode"] = (
            self._read_reg(winreg.HKEY_CURRENT_USER, 
                          r"Software\Microsoft\GameBar", 
                          "AllowAutoGameMode") == 1 and
            self._read_reg(winreg.HKEY_CURRENT_USER, 
                          r"Software\Microsoft\GameBar", 
                          "AutoGameModeEnabled") == 1
        )
        # 3. HAGS
        states["hags"] = self._read_reg(winreg.HKEY_LOCAL_MACHINE, 
                                        r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 
                                        "HwSchMode") == 2
        # 4. Explorer defaults
        states["explorer_launch_this_pc"] = is_launch_to_this_pc()
        states["recycle_in_nav"] = is_recycle_bin_in_nav()
        states["recycle_hidden_desktop"] = is_recycle_bin_hidden_on_desktop()
        
        # 6. End Task
        states["end_task_enabled"] = is_end_task_enabled()
        # 7. Bluetooth Service
        states["bluetooth_enabled"] = self._check_service("bthserv")
        
        # 8. RAM Info
        states["ram_info"] = get_ram_info()
        
        return states

    def _slow_audit(self) -> dict:
        """Тяжелые проверки (выполняются раз в 30 сек)."""
        states = {}
        # 1. Power Plan
        from tweaks import is_recommended_power_plan_active
        from system_info import get_device_type
        laptop = get_device_type() == "Ноутбук"
        states["recommended_power"] = is_recommended_power_plan_active(laptop)
        
        # 2. Sleep Settings
        states["sleep_disabled"] = False # Placeholder, function does not exist
        
        # 3. Wi-Fi Status
        states["wifi_enabled"] = self._check_wifi()
        
        return states

    def audit_all(self):
        """Полный аудит (для ручного вызова)."""
        res = self._fast_audit()
        res.update(self._slow_audit())
        return res

    def _read_reg(self, hive, key_path, name):
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
            return val
        except Exception:
            return None

    def _check_power_plan(self, guid_prefix):
        # Оставляем метод для обратной совместимости, но используем новую логику
        current_guid = get_current_power_scheme_guid()
        return guid_prefix.lower() in current_guid.lower()

    def _check_wifi(self):
        try:
            output = run_cmd_bytes(["netsh", "interface", "show", "interface"])
            # Ищем интерфейс Wi-Fi и проверяем состояние (Connected/Подключено/Enabled/Разрешено)
            # В RU Windows: 'Подключено', 'Разрешено'
            # В EN Windows: 'Connected', 'Enabled'
            lower_out = output.lower()
            wifi_keywords = ["wi-fi", "беспроводная"]
            has_wifi = any(kw in lower_out for kw in wifi_keywords)
            
            if not has_wifi: return False
            
            # Если нашли Wi-Fi, проверяем статус
            status_keywords = ["connected", "enabled", "подключено", "разрешено"]
            return any(skw in lower_out for skw in status_keywords)
        except Exception:
            return False

    def _check_service(self, service_name):
        try:
            res = subprocess.run(["sc", "query", service_name], capture_output=True)
            output = res.stdout.decode('cp866', errors='ignore')
            return "RUNNING" in output
        except Exception:
            return False

    def unregister_all(self, frame_instance=None):
        """Unregister all callbacks or callbacks for a specific frame instance.
        
        Args:
            frame_instance: If provided, only callbacks bound to this frame instance will be removed.
        """
        with self._lock:
            if frame_instance is None:
                # Clear all callbacks
                self._observers.clear()
            else:
                # Remove callbacks bound to specific frame instance
                for key in list(self._observers.keys()):
                    remaining_callbacks = []
                    for cb in self._observers[key]:
                        if hasattr(cb, '__self__') and cb.__self__ is frame_instance:
                            # Skip callbacks bound to this frame
                            continue
                        remaining_callbacks.append(cb)
                    
                    if remaining_callbacks:
                        self._observers[key] = remaining_callbacks
                    else:
                        # No callbacks left for this key, remove the key
                        del self._observers[key]

# Глобальный экземпляр для приложения
sync_engine = SystemSync()
