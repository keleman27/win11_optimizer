"""
system_info.py — Модуль сбора информации о системе.
Используется для Вкладки 1 (Дашборд).
"""

import platform
import os
import subprocess
import winreg
import threading
import psutil
import time
import functools
try:
    import wmi
except ImportError:
    wmi = None
try:
    import pythoncom
except ImportError:
    pythoncom = None


# Кэш для WMI данных
_wmi_cache = {}

def _run_powershell_query(command: str) -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _create_wmi_client():
    initialized = False
    if pythoncom:
        try:
            pythoncom.CoInitialize()
            initialized = True
        except Exception:
            pass
    return wmi.WMI(), initialized


def _release_wmi_client(initialized: bool):
    if initialized and pythoncom:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def cache_wmi(seconds=5):
    """Декоратор для кэширования результатов WMI запросов."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{args}_{kwargs}"
            now = time.time()
            
            # Проверяем кэш
            if key in _wmi_cache:
                result, timestamp = _wmi_cache[key]
                if now - timestamp < seconds:
                    return result
            
            # Получаем новые данные
            result = func(*args, **kwargs)
            _wmi_cache[key] = (result, now)
            return result
        return wrapper
    return decorator


def get_device_type() -> str:
    """Определяет тип устройства: Ноутбук или Стационарный ПК."""
    # Первый метод - проверка батареи через psutil
    try:
        if psutil.sensors_battery() is not None:
            return "Ноутбук"
    except Exception:
        pass
    
    # Второй метод - через WMI (SystemEnclosure)
    if wmi:
        try:
            c = wmi.WMI()
            for enclosure in c.Win32_SystemEnclosure():
                if enclosure.ChassisTypes:
                    chassis_type = enclosure.ChassisTypes[0]
                    # 8=Portable,9=Laptop,10=Notebook,11=Hand Held,14=Sub Notebook
                    if chassis_type in [8, 9, 10, 11, 14]:
                        return "Ноутбук"
        except Exception:
            pass
    
    return "Стационарный ПК"


def get_os_info() -> str:
    """Возвращает строку с версией ОС."""
    try:
        ver = platform.version()
        release = platform.release()
        build = platform.win32_ver()[1]
        return f"Windows {release} (Build {build})"
    except Exception:
        return platform.platform()


def get_cpu_info() -> str:
    """Возвращает модель, количество ядер и потоков CPU."""
    try:
        # Имя процессора из реестра
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        cpu_name = cpu_name.strip()
    except Exception:
        cpu_name = platform.processor() or "Неизвестно"

    cores = psutil.cpu_count(logical=False) or "?"
    threads = psutil.cpu_count(logical=True) or "?"
    return f"{cpu_name}\n  Ядра: {cores}  |  Потоки: {threads}"


@cache_wmi(seconds=5)
def get_gpu_info() -> str:
    """Возвращает название GPU и версию драйвера (NVIDIA приоритет)."""
    if wmi:
        initialized = False
        try:
            c, initialized = _create_wmi_client()
            gpus = []
            for gpu in c.Win32_VideoController():
                name = gpu.Name or "Неизвестный GPU"
                driver = gpu.DriverVersion or ""
                if driver:
                    gpus.append(f"{name}  (Драйвер: {driver})")
                else:
                    gpus.append(name)
            if gpus:
                return "\n  ".join(gpus)
        except Exception:
            pass
        finally:
            _release_wmi_client(initialized)

    output = _run_powershell_query(
        "Get-CimInstance Win32_VideoController | "
        "ForEach-Object { if ($_.DriverVersion) { \"$($_.Name)  (Драйвер: $($_.DriverVersion))\" } else { $_.Name } }"
    )
    return output if output else "Неизвестно"


@cache_wmi(seconds=5)
def get_motherboard_info() -> str:
    """Возвращает производителя и модель материнской платы."""
    if wmi:
        initialized = False
        try:
            c, initialized = _create_wmi_client()
            for board in c.Win32_BaseBoard():
                manufacturer = board.Manufacturer or ""
                product = board.Product or ""
                if manufacturer or product:
                    return f"{manufacturer} {product}".strip()
        except Exception:
            pass
        finally:
            _release_wmi_client(initialized)

    output = _run_powershell_query(
        "$b = Get-CimInstance Win32_BaseBoard | Select-Object -First 1; "
        "if ($b) { \"$($b.Manufacturer) $($b.Product)\".Trim() }"
    )
    if output:
        return output
    return "Неизвестно"


def get_ram_info() -> str:
    """Возвращает общий объём ОЗУ и текущую загрузку."""
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    used_gb = mem.used / (1024 ** 3)
    percent = mem.percent
    return f"{total_gb:.1f} ГБ  |  Использовано: {used_gb:.1f} ГБ ({percent}%)"


def get_disks_info() -> list[dict]:
    """Возвращает список носителей с буквой, ФС, объёмом и свободным местом."""
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total_gb = usage.total / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            used_pct = usage.percent
            disks.append({
                "drive": part.device,
                "fs": part.fstype,
                "total": f"{total_gb:.1f} ГБ",
                "free": f"{free_gb:.1f} ГБ свободно",
                "used_pct": used_pct,
            })
        except PermissionError:
            continue
    return disks


def get_battery_info() -> dict | None:
    """Возвращает статус батареи (только для ноутбуков)."""
    try:
        bat = psutil.sensors_battery()
        if bat:
            return {
                "percent": bat.percent,
                "plugged": bat.power_plugged,
            }
    except Exception:
        pass
    return None


def collect_all(callback=None) -> dict:
    """
    Собирает всю системную информацию в словарь.
    Если передан callback — вызывает его с результатом (для async-сбора в потоке).
    """
    data = {
        "device_type": get_device_type(),
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "gpu": get_gpu_info(),
        "motherboard": get_motherboard_info(),
        "ram": get_ram_info(),
        "disks": get_disks_info(),
        "battery": get_battery_info(),
    }
    if callback:
        callback(data)
    return data


def collect_all_async(callback) -> threading.Thread:
    """Запускает collect_all в фоновом потоке и вызывает callback с результатом."""
    def safe_callback(data):
        try:
            callback(data)
        except Exception as e:
            print(f"Error in async callback: {e}")
            import traceback
            traceback.print_exc()
    
    t = threading.Thread(target=collect_all, args=(safe_callback,), daemon=True)
    t.start()
    return t
