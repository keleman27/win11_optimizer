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


def get_device_type() -> str:
    """Определяет тип устройства: Ноутбук или Стационарный ПК."""
    try:
        # Проверяем наличие батареи через psutil
        battery = psutil.sensors_battery()
        if battery is not None:
            return "Ноутбук"
    except Exception:
        pass
    # Второй метод — через WMI (SystemEnclosure)
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject -Class Win32_SystemEnclosure | Select-Object -ExpandProperty ChassisTypes"],
            capture_output=True, timeout=5
        )
        chassis = result.stdout.decode('cp866', errors='ignore').strip()
        # 8=Portable,9=Laptop,10=Notebook,11=Hand Held,14=Sub Notebook
        laptop_types = {"8", "9", "10", "11", "14"}
        if any(t in chassis for t in laptop_types):
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


def get_gpu_info() -> str:
    """Возвращает название GPU и версию драйвера (NVIDIA приоритет)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject Win32_VideoController | Select-Object Name,DriverVersion | Format-List"],
            capture_output=True, timeout=6
        )
        output = result.stdout.decode('cp866', errors='ignore')
        lines = output.strip().splitlines()
        gpus = []
        name, drv = "", ""
        for line in lines:
            if ":" in line:
                key, _, val = line.partition(":")
                k = key.strip().lower()
                v = val.strip()
                if k == "name":
                    name = v
                elif k == "driverversion":
                    drv = v
            elif line.strip() == "" and name:
                gpus.append(f"{name}  (Драйвер: {drv})" if drv else name)
                name, drv = "", ""
        if name:
            gpus.append(f"{name}  (Драйвер: {drv})" if drv else name)
        return "\n  ".join(gpus) if gpus else "Неизвестно"
    except Exception:
        return "Неизвестно"


def get_motherboard_info() -> str:
    """Возвращает производителя и модель материнской платы."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject Win32_BaseBoard | Select-Object Manufacturer,Product | Format-List"],
            capture_output=True, timeout=5
        )
        output = result.stdout.decode('cp866', errors='ignore')
        lines = output.strip().splitlines()
        mfr, product = "", ""
        for line in lines:
            if ":" in line:
                key, _, val = line.partition(":")
                k = key.strip().lower()
                v = val.strip()
                if k == "manufacturer":
                    mfr = v
                elif k == "product":
                    product = v
        if mfr or product:
            return f"{mfr} {product}".strip()
    except Exception:
        pass
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
    t = threading.Thread(target=collect_all, args=(callback,), daemon=True)
    t.start()
    return t
