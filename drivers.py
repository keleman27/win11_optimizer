"""
drivers.py — Вкладка 3: Драйверы и Видеокарта.
Мониторинг GPU, установка драйверов NVIDIA, настройка монитора и LAN.
"""

import customtkinter as ctk
import threading
import webbrowser
import tkinter as tk
import tkinter.messagebox as messagebox
import ctypes
from ctypes import wintypes
from system_info import get_gpu_info
from state import app_state

# ── Windows Display API ──────────────────────────────────────────────────
class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ('dmDeviceName', wintypes.WCHAR * 32),
        ('dmSpecVersion', wintypes.WORD),
        ('dmDriverVersion', wintypes.WORD),
        ('dmSize', wintypes.WORD),
        ('dmDriverExtra', wintypes.WORD),
        ('dmFields', wintypes.DWORD),
        ('dmPositionX', wintypes.LONG),
        ('dmPositionY', wintypes.LONG),
        ('dmDisplayOrientation', wintypes.DWORD),
        ('dmDisplayFixedOutput', wintypes.DWORD),
        ('dmColor', ctypes.c_short),
        ('dmDuplex', ctypes.c_short),
        ('dmYResolution', ctypes.c_short),
        ('dmTTOption', ctypes.c_short),
        ('dmCollate', ctypes.c_short),
        ('dmFormName', wintypes.WCHAR * 32),
        ('dmLogPixels', wintypes.WORD),
        ('dmBitsPerPel', wintypes.DWORD),
        ('dmPelsWidth', wintypes.DWORD),
        ('dmPelsHeight', wintypes.DWORD),
        ('dmDisplayFlags', wintypes.DWORD),
        ('dmDisplayFrequency', wintypes.DWORD),
        ('dmICMMethod', wintypes.DWORD),
        ('dmICMIntent', wintypes.DWORD),
        ('dmMediaType', wintypes.DWORD),
        ('dmDitherType', wintypes.DWORD),
        ('dmReserved1', wintypes.DWORD),
        ('dmReserved2', wintypes.DWORD),
        ('dmPanningWidth', wintypes.DWORD),
        ('dmPanningHeight', wintypes.DWORD)
    ]

ENUM_CURRENT_SETTINGS = -1
CDS_UPDATEREGISTRY = 0x01
DISP_CHANGE_SUCCESSFUL = 0

ACCENT      = "#4F8EF7"
ACCENT_HOV  = "#3A75E0"
SUCCESS     = "#4CAF50"
WARNING     = "#FF9800"
BG_CARD     = "#1E2130"
BG_DARK     = "#161824"
BORDER      = "#2D3354"
TEXT_PRIM   = "#EAEEF8"
TEXT_SEC    = "#8B9BB4"

class DriversFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, switch_tab_callback=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=ACCENT, **kwargs)
        self._switch_tab = switch_tab_callback
        
        # Дефолтные значения для безопасности
        self._native_res = (1920, 1080)
        self._max_hz = 60
        
        self._build_ui()
        self._load_gpu_data()
        self._load_lan_data()
        self._load_monitor_data()

    def _build_ui(self):
        # ── Блок 1: Видеокарта и Драйверы NVIDIA ─────────────────────────────
        gpu_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                                border_width=1, border_color=BORDER)
        gpu_card.pack(fill="x", padx=24, pady=(24, 10))

        # Заголовок
        ctk.CTkLabel(gpu_card, text="🎮  Видеокарта (NVIDIA)",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=TEXT_PRIM).pack(anchor="w", padx=20, pady=(16, 10))

        # Мониторинг
        self._gpu_info_lbl = ctk.CTkLabel(gpu_card, text="⏳ Получение информации о GPU...",
                                          font=ctk.CTkFont("Segoe UI", 13), text_color=SUCCESS,
                                          justify="left", wraplength=500)
        self._gpu_info_lbl.pack(anchor="w", padx=20, pady=(0, 16))

        # Настройки установки
        install_frame = ctk.CTkFrame(gpu_card, fg_color="transparent")
        install_frame.pack(fill="x", padx=20, pady=(0, 10))

        self._install_mode = ctk.StringVar(value="normal")
        
        rb_normal = ctk.CTkRadioButton(install_frame, text="Обычная установка",
                                       variable=self._install_mode, value="normal",
                                       fg_color=ACCENT, hover_color=ACCENT_HOV)
        rb_normal.pack(side="left", padx=(0, 20))

        rb_clean = ctk.CTkRadioButton(install_frame, text="Чистая установка",
                                      variable=self._install_mode, value="clean",
                                      fg_color=ACCENT, hover_color=ACCENT_HOV)
        rb_clean.pack(side="left")

        ctk.CTkLabel(install_frame, text="(Рекомендуется, если вы недавно установили Windows)",
                     font=ctk.CTkFont("Segoe UI", 11, slant="italic"), text_color=TEXT_SEC).pack(side="left", padx=10)

        # Действия NVIDIA
        action_frame = ctk.CTkFrame(gpu_card, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(action_frame, text="Проверить обновления драйвера",
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOV, height=36,
                      command=self._check_nvidia_updates).pack(side="left", padx=(0, 12))

        ctk.CTkButton(action_frame, text="⚙️ Оптимизировать Панель управления",
                      font=ctk.CTkFont("Segoe UI", 12),
                      fg_color="transparent", hover_color="#1A2A1A",
                      border_width=1, border_color=SUCCESS, text_color=SUCCESS, height=36,
                      command=self._optimize_nvidia).pack(side="left")

        # ── Блок 2: Монитор ──────────────────────────────────────────────────
        mon_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                                border_width=1, border_color=BORDER)
        mon_card.pack(fill="x", padx=24, pady=(0, 10))

        ctk.CTkLabel(mon_card, text="🖥️  Монитор",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=TEXT_PRIM).pack(anchor="w", padx=20, pady=(16, 12))

        # Элементы управления
        controls_frame = ctk.CTkFrame(mon_card, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Гц
        hz_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        hz_frame.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(hz_frame, text="Частота (Гц):", font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT_SEC).pack(anchor="w")
        self._hz_menu = ctk.CTkOptionMenu(hz_frame, values=["---"], width=100,
                                          fg_color=BG_DARK, button_color=BORDER, 
                                          button_hover_color=ACCENT, dropdown_fg_color=BG_DARK,
                                          command=self._apply_hz)
        self._hz_menu.pack(pady=(2, 0))

        # Разрешение
        res_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        res_frame.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(res_frame, text="Разрешение:", font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT_SEC).pack(anchor="w")
        self._res_menu = ctk.CTkOptionMenu(res_frame, values=["---"], width=140,
                                           fg_color=BG_DARK, button_color=BORDER, 
                                           button_hover_color=ACCENT, dropdown_fg_color=BG_DARK,
                                           command=self._apply_resolution)
        self._res_menu.pack(pady=(2, 0))

        # Кнопка Оптимально
        ctk.CTkButton(controls_frame, text="✨ Оптимальные параметры", 
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color="#8B5CF6", hover_color="#7C3AED", height=32,
                      command=self._apply_optimal_monitor).pack(side="left", pady=(18, 0))

        mon_desc = ctk.CTkLabel(mon_card, text="Автоматическое определение поддерживаемой частоты и разрешения. Оптимальные параметры устанавливают максимальную герцовку и родное разрешение экрана.",
                                font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SEC, justify="left")
        mon_desc.pack(anchor="w", fill="x", padx=20, pady=(10, 20))
        
        def _resize_mon_desc(e):
            current = mon_desc.cget("wraplength")
            new_w = max(100, e.width - 40)
            if current == "" or abs(int(current) - new_w) > 5:
                mon_desc.configure(wraplength=new_w)

        mon_card.bind("<Configure>", _resize_mon_desc)

        # ── Блок 3: Сетевой адаптер (LAN) ────────────────────────────────────
        lan_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                                border_width=1, border_color=BORDER)
        lan_card.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(lan_card, text="🌐  Сетевой адаптер (LAN)",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=TEXT_PRIM).pack(anchor="w", padx=20, pady=(16, 10))

        self._lan_status_lbl = ctk.CTkLabel(lan_card, text="⏳ Сканирование шины PCI...",
                                            font=ctk.CTkFont("Segoe UI", 12), text_color=SUCCESS)
        self._lan_status_lbl.pack(anchor="w", padx=20, pady=(0, 10))

        lan_action_frame = ctk.CTkFrame(lan_card, fg_color="transparent")
        lan_action_frame.pack(fill="x", padx=20, pady=(0, 20))

        self._realtek_btn = ctk.CTkButton(lan_action_frame, text="Скачать драйвер Realtek",
                      font=ctk.CTkFont("Segoe UI", 12),
                      fg_color="transparent", border_width=1, border_color=BORDER, text_color=TEXT_PRIM,
                      command=self._download_realtek)
        self._realtek_btn.pack(side="left", padx=(0, 4))

        help_lbl = ctk.CTkLabel(lan_action_frame, text=" ❔ ", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=ACCENT, cursor="hand2")
        help_lbl.pack(side="left", padx=(0, 16))

        self._tooltip = None
        def _show_tooltip(e):
            if self._tooltip: return
            x = help_lbl.winfo_rootx() + 25
            y = help_lbl.winfo_rooty() + 25
            self._tooltip = tk.Toplevel(help_lbl)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.wm_geometry(f"+{x}+{y}")
            self._tooltip.attributes("-topmost", True)
            
            lbl = tk.Label(self._tooltip, text="Версия 'Not support Power Saving':\nОтключает режим энергосбережения сетевой карты,\nпозволяя ей работать на полную мощность.\nНе рекомендуется для ноутбуков.",
                           bg="#2D3354", fg="#EAEEF8", font=("Segoe UI", 10), justify="left", padx=10, pady=8)
            lbl.pack()
            
        def _hide_tooltip(e):
            if self._tooltip:
                self._tooltip.destroy()
                self._tooltip = None

        help_lbl.bind("<Enter>", _show_tooltip)
        help_lbl.bind("<Leave>", _hide_tooltip)

        self._intel_btn = ctk.CTkButton(lan_action_frame, text="Скачать драйвер Intel",
                      font=ctk.CTkFont("Segoe UI", 12),
                      fg_color="transparent", border_width=1, border_color=BORDER, text_color=TEXT_PRIM,
                      command=lambda: webbrowser.open("https://www.intel.com/content/www/us/en/download-center/home.html"))
        self._intel_btn.pack(side="left")

    def _download_realtek(self):
        msg = ("Рекомендуется установить версию 'Not support Power Saving' для работы сетевой карты на максимальной мощности.\n\n"
               "ВНИМАНИЕ: Строго не рекомендуется ставить эту версию на ноутбуки (приведет к быстрому разряду батареи).\n\n"
               "Продолжить?")
        if messagebox.askyesno("Драйвер Realtek", msg):
            webbrowser.open("https://www.realtek.com/Download/List?cate_id=584")

    def _load_lan_data(self):
        def _worker():
            import subprocess, json
            try:
                res = subprocess.run(
                    ["powershell", "-Command", "Get-WmiObject Win32_NetworkAdapter -Filter 'PhysicalAdapter=True' | Select-Object Manufacturer, ProductName | ConvertTo-Json"],
                    capture_output=True, timeout=8
                )
                output = res.stdout.decode('cp866', errors='ignore').strip()
                if not output: return
                adapters = json.loads(output)
                if isinstance(adapters, dict): adapters = [adapters]
                
                has_realtek = any("realtek" in str(a.get("Manufacturer", "")).lower() for a in adapters)
                has_intel = any("intel" in str(a.get("Manufacturer", "")).lower() for a in adapters)
                
                self.after(0, lambda: self._update_lan_ui(has_realtek, has_intel))
            except Exception:
                self.after(0, lambda: self._lan_status_lbl.configure(text="Не удалось определить адаптер", text_color=WARNING))
        threading.Thread(target=_worker, daemon=True).start()

    def _update_lan_ui(self, rtk, intel):
        if rtk and not intel:
            self._lan_status_lbl.configure(text="✅ Обнаружена сетевая карта Realtek", text_color=SUCCESS)
            self._realtek_btn.configure(border_color=SUCCESS, text_color=SUCCESS)
        elif intel and not rtk:
            self._lan_status_lbl.configure(text="✅ Обнаружена сетевая карта Intel", text_color=SUCCESS)
            self._intel_btn.configure(border_color=SUCCESS, text_color=SUCCESS)
        elif rtk and intel:
            self._lan_status_lbl.configure(text="✅ Обнаружены карты Realtek и Intel", text_color=SUCCESS)
        else:
            self._lan_status_lbl.configure(text="ℹ️ Сетевая карта не распознана (не Realtek/Intel)", text_color=TEXT_SEC)

    def _load_gpu_data(self):
        def _worker():
            gpu_str = get_gpu_info()
            if "NVIDIA" not in gpu_str.upper() and gpu_str != "Неизвестно":
                gpu_str += "\nВнимание: У вас не NVIDIA. Некоторые оптимизации могут не работать."
            self.after(0, lambda: self._gpu_info_lbl.configure(text=gpu_str))
        threading.Thread(target=_worker, daemon=True).start()

    def _check_nvidia_updates(self):
        webbrowser.open("https://www.nvidia.com/Download/index.aspx")

    def _optimize_nvidia(self):
        # TODO: Реализовать твики реестра для панели NVIDIA
        pass

    def _load_monitor_data(self):
        """Загружает данные о мониторе через Windows API."""
        try:
            current, native_res, supported_hz = self._get_display_info()
            
            # Обновляем Гц
            hz_values = [f"{hz} Гц" for hz in supported_hz]
            self._hz_menu.configure(values=hz_values)
            if current:
                self._hz_menu.set(f"{current[2]} Гц")
            
            # Обновляем Разрешение
            curr_res_str = f"{current[0]}x{current[1]}" if current else "---"
            native_res_str = f"{native_res[0]}x{native_res[1]}"
            
            if curr_res_str == native_res_str:
                self._res_menu.configure(values=[f"{curr_res_str} (Родное)"], state="disabled")
                self._res_menu.set(f"{curr_res_str} (Родное)")
            else:
                self._res_menu.configure(values=[curr_res_str, f"{native_res_str} (Родное)"], state="normal")
                self._res_menu.set(curr_res_str)
                
            self._native_res = native_res
            self._max_hz = max(supported_hz) if supported_hz else 60
        except Exception as e:
            print(f"Error loading monitor data: {e}")

    def _get_display_info(self):
        user32 = ctypes.windll.user32
        devmode = DEVMODEW()
        devmode.dmSize = ctypes.sizeof(DEVMODEW)
        
        current = None
        if user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            current = (devmode.dmPelsWidth, devmode.dmPelsHeight, devmode.dmDisplayFrequency)
        
        modes = []
        i = 0
        while user32.EnumDisplaySettingsW(None, i, ctypes.byref(devmode)):
            modes.append((devmode.dmPelsWidth, devmode.dmPelsHeight, devmode.dmDisplayFrequency))
            i += 1
            
        resolutions = sorted(list(set((m[0], m[1]) for m in modes)), key=lambda x: x[0]*x[1], reverse=True)
        native_res = resolutions[0] if resolutions else (0, 0)
        supported_hz = sorted(list(set(m[2] for m in modes if (m[0], m[1]) == native_res)))
        
        return current, native_res, supported_hz

    def _apply_hz(self, hz_str):
        hz = int(hz_str.split()[0])
        self._change_display(self._native_res[0], self._native_res[1], hz)

    def _apply_resolution(self, res_str):
        if "(Родное)" in res_str:
            self._change_display(self._native_res[0], self._native_res[1], self._max_hz)
        # Если текущее — ничего не делаем

    def _apply_optimal_monitor(self):
        self._change_display(self._native_res[0], self._native_res[1], self._max_hz)
        self._load_monitor_data()

    def _change_display(self, width, height, hz):
        user32 = ctypes.windll.user32
        devmode = DEVMODEW()
        devmode.dmSize = ctypes.sizeof(DEVMODEW)
        
        if not user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            return False
            
        devmode.dmPelsWidth = width
        devmode.dmPelsHeight = height
        devmode.dmDisplayFrequency = hz
        devmode.dmFields = 0x00080000 | 0x00100000 | 0x00400000 # width, height, frequency
        
        result = user32.ChangeDisplaySettingsW(ctypes.byref(devmode), CDS_UPDATEREGISTRY)
        if result == DISP_CHANGE_SUCCESSFUL:
            messagebox.showinfo("Монитор", f"Параметры успешно изменены: {width}x{height} @ {hz}Гц")
            self._load_monitor_data()
        else:
            messagebox.showerror("Ошибка", "Не удалось изменить параметры монитора. Возможно, они не поддерживаются.")
        return result == DISP_CHANGE_SUCCESSFUL

    def _boost_monitor(self):
        # Оставлено для совместимости, если где-то вызывается, но функционал заменен
        self._apply_optimal_monitor()
