"""
tweaks.py — Определения твиков и функции их применения.
"""

import winreg
import subprocess
import struct

# ── Константы GUID схем питания ───────────────────────────────────────────
POWER_BALANCED      = "381b4222-f694-41f0-9685-ff5bb260df2e"
POWER_HIGH          = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
POWER_ULTIMATE      = "e9a42b02-d5df-448d-aa00-03f14749eb61"


# ── Описание 17 визуальных эффектов ───────────────────────────────────────
# kind: "DWORD" | "SZ" | "MASK"
# Для MASK: бит в UserPreferencesMask (HKCU\Control Panel\Desktop)
# Для DWORD/SZ: прямая запись в реестр

VISUAL_EFFECTS: list[dict] = [
    {"label": "Анимация на панели задач",                          "recommended": False,
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "TaskbarAnimations",  "on": 1, "off": 0},

    {"label": "Анимация окон при свертывании и развертывании",     "recommended": False,
     "kind": "SZ",    "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Control Panel\Desktop\WindowMetrics",
     "name": "MinAnimate",         "on": "1", "off": "0"},

    {"label": "Анимированные элементы управления внутри окон",     "recommended": False,
     "kind": "MASK",  "bit": 0x8000},

    {"label": "Включение Peek",                                    "recommended": False,
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "EnableAeroPeek",     "on": 1, "off": 0},

    {"label": "Вывод эскизов вместо значков",                      "recommended": True,
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "IconsOnly",          "on": 0, "off": 1},  # 0=эскизы (включено)

    {"label": "Гладкое прокручивание списков",                     "recommended": False,
     "kind": "MASK",  "bit": 0x0001},

    {"label": "Затухание меню после вызова команды",               "recommended": False,
     "kind": "MASK",  "bit": 0x0200},

    {"label": "Отбрасывание теней значками на рабочем столе",      "recommended": False,
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "ListviewShadow",     "on": 1, "off": 0},

    {"label": "Отображение прозрачного прямоугольника выделения",  "recommended": True,
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "ListviewAlphaSelect","on": 1, "off": 0},

    {"label": "Отображение содержимого окна при перетаскивании",   "recommended": True,
     "kind": "SZ",    "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Control Panel\Desktop",
     "name": "DragFullWindows",    "on": "1", "off": "0"},

    {"label": "Отображение теней, отбрасываемых окнами",           "recommended": False,
     "kind": "MASK",  "bit": 0x0020},

    {"label": "Отображение тени под указателем мыши",              "recommended": False,
     "kind": "MASK",  "bit": 0x0010},

    {"label": "Сглаживание неровностей экранных шрифтов",          "recommended": True,
     "kind": "SZ",    "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Control Panel\Desktop",
     "name": "FontSmoothing",      "on": "2", "off": "0"},

    {"label": "Скольжение при раскрытии списков",                  "recommended": False,
     "kind": "MASK",  "bit": 0x0004},

    {"label": "Сохранение вида эскизов панели задач",              "recommended": False,
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "TaskbarAnimations",  "on": 1, "off": 0},

    {"label": "Эффекты затухания/скольжения при обращении к меню", "recommended": False,
     "kind": "MASK",  "bit": 0x0002},

    {"label": "Эффекты затухания/скольжения при появлении подсказок", "recommended": False,
     "kind": "MASK",  "bit": 0x0100},
]


# ── Вспомогательные функции реестра ───────────────────────────────────────

def _read_mask() -> int:
    """Читает UserPreferencesMask из реестра как int."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
        data, _ = winreg.QueryValueEx(key, "UserPreferencesMask")
        winreg.CloseKey(key)
        # data — bytes (REG_BINARY), берём первые 4 байта как little-endian uint32
        return struct.unpack_from("<I", bytes(data))[0]
    except Exception:
        return 0x80031290  # default Windows value


def _write_mask(mask: int):
    """Записывает UserPreferencesMask в реестр."""
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop",
                         0, winreg.KEY_SET_VALUE)
    # Сохраняем как 8 байт (полная длина маски)
    data = struct.pack("<I", mask) + b"\x00\x00\x00\x00"
    winreg.SetValueEx(key, "UserPreferencesMask", 0, winreg.REG_BINARY, data)
    winreg.CloseKey(key)


def _set_reg(hive, key_path: str, name: str, value, kind: str):
    """Универсальная запись значения в реестр."""
    reg_type = winreg.REG_DWORD if kind == "DWORD" else winreg.REG_SZ
    key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, name, 0, reg_type, value)
    winreg.CloseKey(key)


# ── Применение твиков ──────────────────────────────────────────────────────

def apply_visual_effects(enabled_indices: list[int]):
    """
    Применяет визуальные эффекты.
    enabled_indices — список индексов включённых эффектов из VISUAL_EFFECTS.
    """
    mask = _read_mask()
    for i, fx in enumerate(VISUAL_EFFECTS):
        is_on = i in enabled_indices
        if fx["kind"] == "MASK":
            if is_on:
                mask |= fx["bit"]
            else:
                mask &= ~fx["bit"]
        else:
            val = fx["on"] if is_on else fx["off"]
            _set_reg(fx["hive"], fx["key"], fx["name"], val, fx["kind"])
    _write_mask(mask)


def get_visual_effects_state() -> list[int]:
    """Возвращает список индексов включённых эффектов."""
    mask = _read_mask()
    enabled = []
    for i, fx in enumerate(VISUAL_EFFECTS):
        if fx["kind"] == "MASK":
            if mask & fx["bit"]:
                enabled.append(i)
        else:
            try:
                key = winreg.OpenKey(fx["hive"], fx["key"], 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(key, fx["name"])
                winreg.CloseKey(key)
                if val == fx["on"]:
                    enabled.append(i)
            except Exception:
                pass
    return enabled


def apply_power_plan(is_laptop: bool, force_performance: bool = False):
    """Устанавливает схему питания."""
    if force_performance or not is_laptop:
        guid = POWER_ULTIMATE
    else:
        guid = POWER_BALANCED
    # Пробуем Ultimate, при ошибке — High Performance
    result = subprocess.run(
        ["powercfg", "/setactive", guid],
        capture_output=True, timeout=10
    )
    if result.returncode != 0 and guid == POWER_ULTIMATE:
        subprocess.run(["powercfg", "/setactive", POWER_HIGH],
                       capture_output=True, timeout=10)


def apply_copilot_disable():
    """Скрывает кнопку Copilot с панели задач."""
    _set_reg(winreg.HKEY_CURRENT_USER,
             r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
             "ShowCopilotButton", 0, "DWORD")


def is_copilot_disabled() -> bool:
    """Проверяет, скрыт ли Copilot."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                             0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "ShowCopilotButton")
        winreg.CloseKey(key)
        return val == 0
    except Exception:
        return False


def apply_explorer_settings(open_to_this_pc: bool, recycle_in_nav: bool, hide_recycle_desktop: bool):
    """Применяет настройки Проводника."""
    adv_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

    # Открывать «Этот компьютер»: LaunchTo=1
    if open_to_this_pc:
        _set_reg(winreg.HKEY_CURRENT_USER, adv_key, "LaunchTo", 1, "DWORD")

    # Корзина в боковой панели (через ShellFolder Attributes)
    if recycle_in_nav:
        try:
            rb_clsid = r"Software\Classes\CLSID\{645FF040-5081-101B-9F08-00AA002F954E}\ShellFolder"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, rb_clsid,
                                 0, winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY)
            winreg.SetValueEx(key, "Attributes", 0, winreg.REG_DWORD, 0xF0400174)
            winreg.CloseKey(key)
        except Exception:
            pass

    # Скрыть/показать корзину на рабочем столе
    try:
        hide_key = (r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                    r"\HideDesktopIcons\NewStartPanel")
        rb_guid = "{645FF040-5081-101B-9F08-00AA002F954E}"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hide_key,
                             0, winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY)
        winreg.SetValueEx(key, rb_guid, 0, winreg.REG_DWORD, 1 if hide_recycle_desktop else 0)
        winreg.CloseKey(key)
    except Exception:
        pass


def restart_explorer():
    """Перезапускает explorer.exe."""
    subprocess.run(["taskkill", "/f", "/im", "explorer.exe"],
                   capture_output=True)
    subprocess.Popen(["explorer.exe"])


def restart_pc():
    """Перезагружает ПК через shutdown."""
    subprocess.run(["shutdown", "/r", "/t", "10",
                    "/c", "Win11 Optimizer: перезагрузка для применения настроек"],
                   capture_output=True)
