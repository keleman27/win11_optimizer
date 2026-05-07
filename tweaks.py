"""
tweaks.py — Логика оптимизации Windows 11.
Содержит функции для работы с реестром, питанием и визуальными эффектами.
"""

import winreg
import subprocess
import struct
import ctypes
import re
import platform

# ── Константы GUID схем питания ───────────────────────────────────────────
POWER_BALANCED      = "381b4222-f694-41f0-9685-ff5bb260df2e"
POWER_HIGH          = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
POWER_ULTIMATE      = "e9a42b02-d5df-448d-aa00-03f14749eb61"

# Флаг для подавления окон командной строки
CREATE_NO_WINDOW = 0x08000000



def run_cmd_bytes(command: list[str]) -> str:
    """Специальная функция: получаем сырые байты, чтобы избежать проблем с кодировкой (CP866/UTF-8)."""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            creationflags=CREATE_NO_WINDOW,
            timeout=10
        )
        # Пытаемся cp866 (стандарт консоли RU), потом utf-8
        try:
            return result.stdout.decode('cp866', errors='ignore')
        except Exception:
            return result.stdout.decode('utf-8', errors='ignore')
    except Exception:
        return ""


# ── Описание 17 визуальных эффектов Windows 11 ────────────────────────────
VISUAL_EFFECTS: list[dict] = [
    {"label": "Анимированные элементы управления внутри окон",     "fx_key": "ControlAnimations",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects\ControlAnimations",
     "name": "DefaultValue",       "on": 1, "off": 0, "spi_action": 0x1043, "spi_type": "pv", "recommended": False},

    {"label": "Анимация окон при свертывании и развертывании",     "fx_key": "AnimateMinMax",
     "kind": "SZ",    "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Control Panel\Desktop\WindowMetrics",
     "name": "MinAnimate",         "on": "1", "off": "0", 
     "spi_action": 0x0049, "spi_type": "struct_anim", "recommended": False},

    {"label": "Анимация на панели задач",                          "fx_key": "TaskbarAnimations",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "TaskbarAnimations",  "on": 1, "off": 0, "spi_action": None, "recommended": False},

    {"label": "Включение Peek",                                    "fx_key": "DWMAeroPeekEnabled",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "EnableAeroPeek",     "on": 1, "off": 0, "spi_action": None,
     "recommended": False,
     "extra_keys": [
         {"key": r"Software\Microsoft\Windows\DWM", "name": "EnableAeroPeek", "on": 1, "off": 0},
         {"key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "name": "DisablePreviewDesktop", "on": 0, "off": 1}
     ]},

    {"label": "Эффекты затухания или скольжения при обращении к меню", "fx_key": "MenuAnimation",
     "kind": "MASK",  "bit": 0x0002, "spi_action": 0x1003, "spi_type": "pv", "recommended": False},

    {"label": "Эффекты затухания или скольжения при появлении подсказок", "fx_key": "TooltipAnimation",
     "kind": "MASK",  "bit": 0x1800, "spi_action": 0x1011, "spi_type": "pv", "recommended": False},

    {"label": "Затухание меню после вызова команды",               "fx_key": "SelectionFade",
     "kind": "MASK",  "bit": 0x0400, "spi_action": 0x1013, "spi_type": "pv", "recommended": False},

    {"label": "Сохранение вида эскизов панели задач",              "fx_key": "DWMSaveThumbnailEnabled",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects\DWMSaveThumbnailEnabled",
     "name": "DefaultValue",       "on": 1, "off": 0, "spi_action": None,
     "recommended": False,
     "extra_keys": [
         {"key": r"Software\Microsoft\Windows\DWM", "name": "AlwaysHibernateThumbnails", "on": 1, "off": 0}
     ]},

    {"label": "Отображение теней, отбрасываемых окнами",           "fx_key": "Shadow",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects\Shadow",
     "name": "DefaultValue",       "on": 1, "off": 0, "spi_action": None, 
     "bit": 0x00040000, "recommended": False},

    {"label": "Отображение тени под указателем мыши",              "fx_key": "CursorShadow",
     "kind": "MASK",  "bit": 0x2000, "spi_action": 0x101B, "spi_type": "pv", "recommended": False},

    {"label": "Вывод эскизов вместо значков",                      "fx_key": "ThumbnailsOrIcon",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "IconsOnly",          "on": 0, "off": 1, "spi_action": None, "recommended": True},

    {"label": "Отображение прозрачного прямоугольника выделения",  "fx_key": "ListviewAlphaSelect",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "ListviewAlphaSelect","on": 1, "off": 0, "spi_action": None, "recommended": True},

    {"label": "Отображение содержимого окна при перетаскивании",   "fx_key": "DragFullWindows",
     "kind": "SZ",    "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Control Panel\Desktop",
     "name": "DragFullWindows",    "on": "1", "off": "0", "spi_action": 0x0025, "spi_type": "ui", "recommended": True},

    {"label": "Скольжение при раскрытии списков",                  "fx_key": "ComboBoxAnimation",
     "kind": "MASK",  "bit": 0x0004, "spi_action": 0x1005, "spi_type": "pv", "recommended": False},

    {"label": "Сглаживание неровностей экранных шрифтов",          "fx_key": "FontSmoothing",
     "kind": "SZ",    "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Control Panel\Desktop",
     "name": "FontSmoothing",      "on": "2", "off": "0", "spi_action": 0x004B, "spi_type": "ui", "recommended": True},

    {"label": "Гладкое прокручивание списков",                     "fx_key": "ListBoxSmoothScrolling",
     "kind": "MASK",  "bit": 0x0008, "spi_action": 0x1007, "spi_type": "pv", "recommended": False},

    {"label": "Отбрасывание теней значками на рабочем столе",      "fx_key": "ListviewShadow",
     "kind": "DWORD", "hive": winreg.HKEY_CURRENT_USER,
     "key": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
     "name": "ListviewShadow",     "on": 1, "off": 0, "spi_action": None, "recommended": False},
]


# ── Вспомогательные функции реестра ───────────────────────────────────────

class ANIMATIONINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("iMinAnimate", ctypes.c_int)]

def _read_mask() -> bytearray:
    """Читает UserPreferencesMask из реестра как bytearray (8+ байт)."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
        data, _ = winreg.QueryValueEx(key, "UserPreferencesMask")
        winreg.CloseKey(key)
        return bytearray(data)
    except Exception:
        # Стандартная маска (8 байт), если чтение не удалось
        return bytearray(b"\x90\x12\x03\x80\x10\x00\x00\x00")


def _write_mask(mask: bytearray):
    """Записывает UserPreferencesMask в реестр, сохраняя длину."""
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop",
                         0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "UserPreferencesMask", 0, winreg.REG_BINARY, bytes(mask))
    winreg.CloseKey(key)

    # Установка режима "Custom" (3) в VisualFXSetting
    try:
        fx_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects")
        winreg.SetValueEx(fx_key, "VisualFXSetting", 0, winreg.REG_DWORD, 3)
        winreg.CloseKey(fx_key)
    except Exception:
        pass


def _broadcast_setting_change():
    """Рассылает сообщение WM_SETTINGCHANGE всем окнам для обновления Shell."""
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002
    result = ctypes.c_ulong()
    try:
        # Уведомляем о смене окружения (влияет на Peek, DragFullWindows и др.)
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 
            SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
        )
        # Уведомляем о смене темы (влияет на тени окон)
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Themes", 
            SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
        )
    except Exception:
        pass


def _refresh_system_visuals(enabled_indices: list[int]):
    """Точечно уведомляет систему об изменениях через SystemParametersInfoW."""
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02

    # 1. Глобальный переключатель UI-эффектов (SPI_SETUIEFFECTS = 0x103F)
    has_any_fx = len(enabled_indices) > 0
    try:
        ctypes.windll.user32.SystemParametersInfoW(0x103F, 0, ctypes.c_void_p(1 if has_any_fx else 0), SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
    except Exception:
        pass

    # 2. Индивидуальные SPI вызовы
    for i, fx in enumerate(VISUAL_EFFECTS):
        action = fx.get("spi_action")
        if action is None:
            continue
        
        is_on = i in enabled_indices
        try:
            stype = fx.get("spi_type", "pv")
            if stype == "pv":
                pv = ctypes.c_void_p(1 if is_on else 0)
                ctypes.windll.user32.SystemParametersInfoW(action, 0, pv, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
            elif stype == "ui":
                ctypes.windll.user32.SystemParametersInfoW(action, 1 if is_on else 0, None, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
            elif stype == "struct_anim":
                info = ANIMATIONINFO(cbSize=ctypes.sizeof(ANIMATIONINFO), iMinAnimate=1 if is_on else 0)
                ctypes.windll.user32.SystemParametersInfoW(action, ctypes.sizeof(info), ctypes.byref(info), SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
        except Exception:
            pass
    
    # 3. Финальная рассылка сообщения всем окнам
    _broadcast_setting_change()


def _set_reg(hive, key_path: str, name: str, value, kind: str):
    """Универсальная запись значения в реестр."""
    reg_type = winreg.REG_DWORD if kind == "DWORD" else winreg.REG_SZ
    key = winreg.CreateKey(hive, key_path)
    winreg.SetValueEx(key, name, 0, reg_type, value)
    winreg.CloseKey(key)


def _get_reg(hive, key_path: str, name: str):
    """Безопасное чтение значения из реестра."""
    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return None


# ── Применение твиков ──────────────────────────────────────────────────────

def apply_visual_effects(enabled_indices: list[int]):
    """Применяет визуальные эффекты и уведомляет систему."""
    mask = _read_mask()
    fx_base = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
    for i, fx in enumerate(VISUAL_EFFECTS):
        is_on = i in enabled_indices
        
        # 1. Записываем в основной ключ (DWORD/SZ)
        if fx["kind"] != "MASK":
            val = fx["on"] if is_on else fx["off"]
            _set_reg(fx["hive"], fx["key"], fx["name"], val, fx["kind"])
        
        # 2. Обработка битовой маски (если есть bit)
        if "bit" in fx and fx["bit"] is not None:
            bit_val = fx["bit"]
            for b_idx in range(4):
                byte_bit = (bit_val >> (8 * b_idx)) & 0xFF
                if byte_bit == 0: continue
                if is_on:
                    mask[b_idx] |= byte_bit
                else:
                    mask[b_idx] &= ~byte_bit
        
        # 3. Записываем доп. ключи (например DWM или инвертированные)
        if fx.get("extra_keys"):
            for ek in fx["extra_keys"]:
                try:
                    val = ek["on"] if is_on else ek["off"]
                    # По умолчанию HKCU
                    _set_reg(winreg.HKEY_CURRENT_USER, ek["key"], ek["name"], val, "DWORD")
                except Exception:
                    pass

        # 4. Записываем в дублирующий ключ VisualEffects (для синхронизации UI)
        if fx.get("fx_key"):
            try:
                path = f"{fx_base}\\{fx['fx_key']}"
                _set_reg(winreg.HKEY_CURRENT_USER, path, "Applied", 1 if is_on else 0, "DWORD")
            except Exception:
                pass
    
    # 3. Пишем маску и VisualFXSetting = 3
    _write_mask(mask)
    
    # 4. Точечно уведомляем систему через API и рассылаем сообщение
    _refresh_system_visuals(enabled_indices)


def get_visual_effects_state() -> list[int]:
    """Возвращает список индексов включённых эффектов с учетом VisualFXSetting."""
    # Проверяем глобальный режим
    try:
        fx_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects")
        fx_setting, _ = winreg.QueryValueEx(fx_key, "VisualFXSetting")
        winreg.CloseKey(fx_key)
        
        if fx_setting == 1: # Best appearance
            return list(range(len(VISUAL_EFFECTS)))
        if fx_setting == 2: # Best performance
            return []
    except Exception:
        pass

    # Если Custom (3) или не задано, читаем по битам/ключам
    mask = _read_mask()
    fx_base = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
    enabled = []
    
    for i, fx in enumerate(VISUAL_EFFECTS):
        # 1. Сначала пробуем прочитать из VisualEffects (самый точный способ для синхронизации)
        if fx.get("fx_key"):
            try:
                path = f"{fx_base}\\{fx['fx_key']}"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(key, "Applied")
                winreg.CloseKey(key)
                if val == 1:
                    enabled.append(i)
                continue
            except Exception:
                pass

        # 2. Иначе читаем из маски ИЛИ стандартного ключа
        is_fx_on = False
        
        # Проверка по маске
        if "bit" in fx and fx["bit"] is not None:
            bit_val = fx["bit"]
            bit_match = True
            found_any = False
            for b_idx in range(4):
                byte_bit = (bit_val >> (8 * b_idx)) & 0xFF
                if byte_bit == 0: continue
                found_any = True
                if not (mask[b_idx] & byte_bit):
                    bit_match = False
                    break
            if found_any and bit_match:
                is_fx_on = True

        # Проверка по ключу (если маска не сработала или её нет)
        if not is_fx_on and fx["kind"] != "MASK":
            try:
                key = winreg.OpenKey(fx["hive"], fx["key"], 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(key, fx["name"])
                winreg.CloseKey(key)
                if str(val) == str(fx["on"]):
                    is_fx_on = True
            except Exception:
                pass
        
        if is_fx_on:
            enabled.append(i)
    return enabled


def get_current_power_scheme_guid() -> str:
    """Возвращает GUID текущей схемы питания."""
    output = run_cmd_bytes(["powercfg", "/getactivescheme"])
    # Ищем GUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", output, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return ""


def is_recommended_power_plan_active(is_laptop: bool) -> bool:
    """Проверяет, активирована ли рекомендованная схема питания (по GUID или имени)."""
    output = run_cmd_bytes(["powercfg", "/getactivescheme"])
    output_lower = output.lower()

    if is_laptop:
        # Для ноутбука ожидаем Balanced
        if POWER_BALANCED in output_lower:
            return True
        if "balanced" in output_lower or "сбалансированная" in output_lower:
            return True
    else:
        # Для ПК ожидаем Ultimate или High
        if POWER_ULTIMATE in output_lower or POWER_HIGH in output_lower:
            return True
        # Проверяем по имени (поддерживаем дубликаты и локализованные названия)
        keywords = ["ultimate", "максимальная", "high performance", "высокая производительность"]
        if any(kw in output_lower for kw in keywords):
            return True
    
    return False


def apply_power_plan(is_laptop: bool, force_performance: bool = False):
    """Устанавливает схему питания с защитой от дубликатов и без мелькания окон."""
    if force_performance or not is_laptop:
        # 1. Ищем существующую "Максимальную производительность" (Ultimate Performance)
        output = run_cmd_bytes(["powercfg", "/list"])
        target_guid = None

        for line in output.splitlines():
            line_lower = line.lower()
            # Проверяем ключевые слова (максимальная или ultimate)
            if "ultimate" in line_lower or "максимальная" in line_lower:
                match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", line, re.IGNORECASE)
                if match:
                    target_guid = match.group(1)
                    break
        
        if target_guid:
            guid = target_guid
        else:
            # 2. Если нет — создаем и сразу вытягиваем её новый GUID из ответа
            output_dup = run_cmd_bytes(["powercfg", "-duplicatescheme", POWER_ULTIMATE])
            match_new = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", output_dup, re.IGNORECASE)
            if match_new:
                guid = match_new.group(1)
            else:
                # Fallback на Высокую производительность
                guid = POWER_HIGH
    else:
        # Для ноутбука: Сбалансированная
        guid = POWER_BALANCED
    
    # Активируем выбранную схему
    if guid:
        subprocess.run(["powercfg", "/setactive", guid], capture_output=True, 
                       creationflags=CREATE_NO_WINDOW, timeout=10)


def set_power_scheme(guid: str):
    """Активирует схему питания по GUID."""
    if not guid:
        return
    subprocess.run(["powercfg", "/setactive", guid], capture_output=True, 
                   creationflags=CREATE_NO_WINDOW, timeout=10)



def apply_explorer_settings(open_to_this_pc: bool, recycle_in_nav: bool, 
                            hide_recycle_desktop: bool, enable_end_task: bool):
    """Применяет настройки Проводника."""
    print(f"[DEBUG] apply_explorer_settings: recycle_in_nav={recycle_in_nav}, enable_end_task={enable_end_task}")
    adv_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    _set_reg(winreg.HKEY_CURRENT_USER, adv_key, "LaunchTo", 1 if open_to_this_pc else 2, "DWORD")

    clsid_root = r"Software\Classes\CLSID\{645FF040-5081-101B-9F08-00AA002F954E}"
    # Windows 11: System.IsPinnedToNameSpaceTree в корне CLSID
    key_root = winreg.CreateKey(winreg.HKEY_CURRENT_USER, clsid_root)
    winreg.SetValueEx(key_root, "System.IsPinnedToNameSpaceTree", 0, winreg.REG_DWORD, 1 if recycle_in_nav else 0)
    winreg.CloseKey(key_root)
    print(f"[DEBUG] Wrote System.IsPinnedToNameSpaceTree={1 if recycle_in_nav else 0} to CLSID root")

    # Attributes оставляем в ShellFolder для совместимости
    shell_folder = clsid_root + r"\ShellFolder"
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, shell_folder)
    # 0xF0400174 – отображать; 0x40010020 – скрывать из панели навигации
    attr_value = 0xF0400174 if recycle_in_nav else 0x40010020
    winreg.SetValueEx(key, "Attributes", 0, winreg.REG_DWORD, attr_value)
    winreg.CloseKey(key)
    print(f"[DEBUG] Wrote Attributes={hex(attr_value)} to ShellFolder")

    hide_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel"
    rb_guid = "{645FF040-5081-101B-9F08-00AA002F954E}"
    hide_key_handle = winreg.CreateKey(winreg.HKEY_CURRENT_USER, hide_key)
    winreg.SetValueEx(hide_key_handle, rb_guid, 0, winreg.REG_DWORD, 1 if hide_recycle_desktop else 0)
    winreg.CloseKey(hide_key_handle)

    taskbar_dev_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\TaskbarDeveloperSettings"
    _set_reg(winreg.HKEY_CURRENT_USER, taskbar_dev_key, "TaskbarEndTask", 1 if enable_end_task else 0, "DWORD")
    print(f"[DEBUG] Wrote TaskbarEndTask={1 if enable_end_task else 0} to TaskbarDeveloperSettings")


def is_end_task_supported() -> bool:
    """Проверяет, поддерживает ли текущая сборка Windows функцию «Завершить задачу» (TaskbarEndTask).
    Доступна начиная с Windows 11 22H2 Moment 4 (Build 22621) и 23H2 (Build 22631)."""
    try:
        # platform.win32_ver()[1] возвращает строку вида "10.0.22631"
        ver_str = platform.win32_ver()[1]
        if not ver_str:
            return False
        build = int(ver_str.split('.')[-1])
        return build >= 22621
    except Exception:
        return False


def is_end_task_enabled() -> bool:
    """Проверяет функцию завершения задачи."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\TaskbarDeveloperSettings",
                             0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "TaskbarEndTask")
        winreg.CloseKey(key)
        result = val == 1
        print(f"[DEBUG] is_end_task_enabled: val={val}, result={result}")
        return result
    except Exception as e:
        print(f"[DEBUG] is_end_task_enabled: key not found ({e})")
        return False


def is_launch_to_this_pc() -> bool:
    """Возвращает True, если Проводник открывается на «Этот компьютер» (LaunchTo = 1)."""
    val = _get_reg(winreg.HKEY_CURRENT_USER,
                   r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                   "LaunchTo")
    return val == 1


def is_recycle_bin_in_nav() -> bool:
    """Проверяет наличие Корзины в боковой панели Проводника (Windows 11+)."""
    clsid_root = r"Software\Classes\CLSID\{645FF040-5081-101B-9F08-00AA002F954E}"
    # Windows 11: System.IsPinnedToNameSpaceTree лежит в корне CLSID
    pinned = _get_reg(winreg.HKEY_CURRENT_USER, clsid_root, "System.IsPinnedToNameSpaceTree")
    print(f"[DEBUG] is_recycle_bin_in_nav: CLSID root pinned={pinned}")
    if pinned is not None:
        return pinned == 1

    # Fallback: старые версии / другие конфигурации — читаем Attributes из ShellFolder
    shell_folder = clsid_root + r"\ShellFolder"
    val = _get_reg(winreg.HKEY_CURRENT_USER, shell_folder, "Attributes")
    print(f"[DEBUG] is_recycle_bin_in_nav: ShellFolder Attributes={val}")
    if val is None:
        return False
    return val == 0xF0400174


def is_recycle_bin_hidden_on_desktop() -> bool:
    """Проверяет, скрыта ли Корзина с рабочего стола."""
    val = _get_reg(winreg.HKEY_CURRENT_USER,
                   r"Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
                   "{645FF040-5081-101B-9F08-00AA002F954E}")
    return val == 1


def apply_sleep_timeouts(disable: bool):
    """Отключает сон и выключение экрана."""
    timeout = 0 if disable else 30
    # Настройки для 'Никогда' (0) или стандартные (30 мин для AC, меньше для DC)
    cmds = [
        ["powercfg", "/x", "-monitor-timeout-ac", str(timeout)],
        ["powercfg", "/x", "-standby-timeout-ac", str(timeout)],
        ["powercfg", "/x", "-hibernate-timeout-ac", str(timeout)],
        ["powercfg", "/x", "-disk-timeout-ac", str(timeout)],
        
        ["powercfg", "/x", "-monitor-timeout-dc", str(timeout if disable else 10)],
        ["powercfg", "/x", "-standby-timeout-dc", str(timeout if disable else 15)],
        ["powercfg", "/x", "-hibernate-timeout-dc", str(timeout if disable else 20)],
        ["powercfg", "/x", "-disk-timeout-dc", str(timeout if disable else 10)]
    ]
    for cmd in cmds:
        subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW)


def get_sleep_disabled_state() -> bool:
    """Проверяет, установлен ли режим 'Никогда' для сна и монитора (AC/DC)."""
    # Проверяем основные параметры: сон (STANDBYIDLE), монитор (VIDEOIDLE), гибернация (HIBERNATEIDLE)
    queries = [
        ["powercfg", "/q", "SCHEME_CURRENT", "SUB_SLEEP", "STANDBYIDLE"],
        ["powercfg", "/q", "SCHEME_CURRENT", "SUB_VIDEO", "VIDEOIDLE"],
        ["powercfg", "/q", "SCHEME_CURRENT", "SUB_SLEEP", "HIBERNATEIDLE"]
    ]
    
    for cmd in queries:
        output = run_cmd_bytes(cmd)
        if not output:
            continue
            
        # Ищем индексы текущих настроек (Current Setting Index / Текущий индекс)
        # В выводе powercfg /q для конкретного параметра последние два 0x... — это AC и DC индексы.
        matches = re.findall(r":\s+(0x[0-9a-f]+)", output, re.IGNORECASE)
        
        # Если параметров меньше 2, значит что-то пошло не так
        if len(matches) < 2:
            continue
            
        # Нас интересуют только последние два значения (AC и DC текущие индексы)
        current_indices = matches[-2:]
        for m in current_indices:
            try:
                if int(m, 16) != 0:
                    return False
            except ValueError:
                continue
                
    return True


def apply_dark_mode(enabled: bool):
    """Включает или выключает темную тему для системы и приложений."""
    path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    val = 0 if enabled else 1 # AppsUseLightTheme: 0 = Dark, 1 = Light
    try:
        _set_reg(winreg.HKEY_CURRENT_USER, path, "AppsUseLightTheme", val, "DWORD")
        _set_reg(winreg.HKEY_CURRENT_USER, path, "SystemUsesLightTheme", val, "DWORD")
        _broadcast_setting_change()
    except Exception:
        pass


def restart_pc():
    """Перезагружает ПК."""
    subprocess.run(["shutdown", "/r", "/t", "10"], 
                   capture_output=True, creationflags=CREATE_NO_WINDOW)


def get_game_mode_state() -> bool:
    """Проверяет, включён ли Игровой режим (Game Mode)."""
    try:
        key1 = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\GameBar", 0, winreg.KEY_READ)
        val1, _ = winreg.QueryValueEx(key1, "AllowAutoGameMode")
        winreg.CloseKey(key1)
        key2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\GameBar", 0, winreg.KEY_READ)
        val2, _ = winreg.QueryValueEx(key2, "AutoGameModeEnabled")
        winreg.CloseKey(key2)
        return val1 == 1 and val2 == 1
    except Exception:
        return False


def apply_game_mode(enabled: bool):
    """Включает или выключает Игровой режим (Game Mode)."""
    val = 1 if enabled else 0
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\GameBar")
        winreg.SetValueEx(key, "AllowAutoGameMode", 0, winreg.REG_DWORD, val)
        winreg.SetValueEx(key, "AutoGameModeEnabled", 0, winreg.REG_DWORD, val)
        winreg.CloseKey(key)
    except Exception:
        pass


def get_dark_mode_state() -> bool:
    """Проверяет, включена ли темная тема."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 
                             0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return val == 0
    except Exception:
        return False


def restart_explorer():
    """Перезапускает explorer.exe."""
    print("[DEBUG] restart_explorer: killing explorer.exe...")
    result = subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], 
                   capture_output=True, creationflags=CREATE_NO_WINDOW)
    print(f"[DEBUG] restart_explorer: taskkill stdout={result.stdout}, stderr={result.stderr}")
    import time
    time.sleep(1)  # Даём процессу explorer.exe завершиться
    print("[DEBUG] restart_explorer: starting explorer.exe...")
    subprocess.Popen(["explorer.exe"])  # Без CREATE_NO_WINDOW — explorer нужен как shell
    print("[DEBUG] restart_explorer: done")


def restart_pc():
    """Перезагружает ПК."""
    subprocess.run(["shutdown", "/r", "/t", "10"], 
                   capture_output=True, creationflags=CREATE_NO_WINDOW)


def apply_wifi_adapter(enable: bool):
    """Включает или отключает Wi-Fi адаптер."""
    try:
        if enable:
            # Включаем Wi-Fi адаптер
            subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "enabled"], 
                          capture_output=True, creationflags=CREATE_NO_WINDOW)
        else:
            # Отключаем Wi-Fi адаптер
            subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "disabled"], 
                          capture_output=True, creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass


def apply_bluetooth_service(enable: bool):
    """Включает или отключает службу Bluetooth."""
    try:
        if enable:
            # Включаем службу Bluetooth
            subprocess.run(["sc", "start", "bthserv"], 
                          capture_output=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["sc", "config", "bthserv", "start=auto"], 
                          capture_output=True, creationflags=CREATE_NO_WINDOW)
        else:
            # Отключаем службу Bluetooth
            subprocess.run(["sc", "stop", "bthserv"], 
                          capture_output=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["sc", "config", "bthserv", "start=disabled"], 
                          capture_output=True, creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass
