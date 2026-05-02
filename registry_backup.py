"""
registry_backup.py — Создание .reg-бэкапов перед изменением реестра.
Использует `reg export` через subprocess.
"""

import subprocess
import os
from datetime import datetime
from pathlib import Path

# Папка для хранения бэкапов (рядом со скриптом)
BACKUP_DIR = Path(__file__).parent / "backups"


def _ensure_backup_dir():
    BACKUP_DIR.mkdir(exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_key(hive_and_path: str, tag: str = "") -> Path | None:
    """
    Экспортирует один раздел реестра в .reg файл.
    hive_and_path: напр. "HKCU\\\\Control Panel\\\\Desktop"
    Возвращает путь к файлу или None при ошибке.
    """
    _ensure_backup_dir()
    safe_name = tag or hive_and_path.replace("\\", "_").replace(":", "")
    filename = BACKUP_DIR / f"{_timestamp()}_{safe_name[:60]}.reg"
    try:
        result = subprocess.run(
            ["reg", "export", hive_and_path, str(filename), "/y"],
            capture_output=True, timeout=15
        )
        if result.returncode == 0:
            return filename
    except Exception:
        pass
    return None


# Все разделы реестра, затрагиваемые твиками приложения
REGISTRY_KEYS_TO_BACKUP = [
    (r"HKCU\Control Panel\Desktop",                       "Desktop"),
    (r"HKCU\Control Panel\Desktop\WindowMetrics",         "WindowMetrics"),
    (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ExplorerAdvanced"),
    (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel", "HideDesktopIcons"),
]


def backup_all_tweak_keys() -> list[Path]:
    """Создаёт бэкапы всех разделов, используемых твиками. Возвращает список файлов."""
    results = []
    for path, tag in REGISTRY_KEYS_TO_BACKUP:
        f = backup_key(path, tag)
        if f:
            results.append(f)
    return results
