"""
cleanup.py — Вкладка 4: Очистка и Приложения (Debloat).
"""

import customtkinter as ctk
import tkinter as tk
import winreg
import getpass
import os
import shutil
import subprocess
import threading
from datetime import datetime

ACCENT      = "#4F8EF7"
ACCENT_HOV  = "#3A75E0"
SUCCESS     = "#4CAF50"
WARNING     = "#FF9800"
DANGER      = "#F44336"
BG_CARD     = "#1A1A1E"
BG_DARK     = "#111114"
BORDER      = "#28282D"
TEXT_PRIM   = "#EAEEF8"
TEXT_SEC    = "#8B9BB4"

class TweakRow(ctk.CTkFrame):
    """Строка настройки в стиле Zapret 2: Иконка + (Заголовок/Описание) + Переключатель."""
    def __init__(self, parent, icon: str, title: str, description: str = "", default: bool = False, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._var = ctk.BooleanVar(value=default)
        
        # Левая часть: Иконка
        self._icon_lbl = ctk.CTkLabel(self, text=icon, font=ctk.CTkFont("Segoe UI", 16), text_color=ACCENT, width=30)
        self._icon_lbl.pack(side="left", padx=(0, 15))
        
        # Центр: Текст
        self._text_container = ctk.CTkFrame(self, fg_color="transparent")
        self._text_container.pack(side="left", fill="both", expand=True)
        
        self._title_lbl = ctk.CTkLabel(self._text_container, text=title, font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=TEXT_PRIM, anchor="w")
        self._title_lbl.pack(fill="x")
        
        if description:
            self._desc_lbl = ctk.CTkLabel(self._text_container, text=description, font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SEC, anchor="w", justify="left")
            self._desc_lbl.pack(fill="x")
        
        # Правая часть: Переключатель
        self._sw = ctk.CTkSwitch(self, text="", variable=self._var, progress_color=ACCENT, width=45)
        self._sw.pack(side="right", padx=(10, 0))

    def get(self): return self._var.get()
    def set(self, val): self._var.set(val)


def add_tooltip(widget, text):
    tooltip = [None]
    def _show(event):
        if tooltip[0]: return
        x = widget.winfo_rootx() + 25
        y = widget.winfo_rooty() + 25
        tooltip[0] = tk.Toplevel(widget)
        tooltip[0].wm_overrideredirect(True)
        tooltip[0].wm_geometry(f"+{x}+{y}")
        tooltip[0].attributes("-topmost", True)
        lbl = tk.Label(tooltip[0], text=text, bg="#2D3354", fg="#EAEEF8",
                       font=("Segoe UI", 10), justify="left", padx=10, pady=8)
        lbl.pack()
    def _hide(event):
        if tooltip[0]:
            tooltip[0].destroy()
            tooltip[0] = None
    widget.bind("<Enter>", _show)
    widget.bind("<Leave>", _hide)


class CleanupFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, switch_tab_callback=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=ACCENT, **kwargs)
        self._switch_tab = switch_tab_callback
        self._build_ui()

    def _build_ui(self):
        # ── Блок 1: Удаление встроенного ПО ──────────────────────────────────
        apps_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                                 border_width=1, border_color=BORDER)
        apps_card.pack(fill="x", padx=24, pady=(24, 10))

        ctk.CTkLabel(apps_card, text="🗑️  Удаление встроенных приложений",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=TEXT_PRIM).pack(anchor="w", padx=20, pady=(16, 4))
        
        ctk.CTkLabel(apps_card, text="Выберите приложения и компоненты для удаления (Debloat).",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT_SEC).pack(anchor="w", padx=20, pady=(0, 16))

        # Безопасное
        safe_frame = ctk.CTkFrame(apps_card, fg_color="transparent")
        safe_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(safe_frame, text="✅ Безопасно удалять:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=SUCCESS).pack(anchor="w", pady=(0, 4))
        
        safe_apps = [
            ("Camera", "Удаляет стандартное приложение Камера."),
            ("Центр отзывов", "Удаляет Feedback Hub."),
            ("Погода", "Удаляет виджет Погоды."),
            ("Карты", "Удаляет Windows Maps."),
            ("Связь с телефоном", "Удаляет Phone Link.")
        ]
        self._safe_cbs = []
        for app, desc in safe_apps:
            cb = TweakRow(safe_frame, "📦", app, desc, default=True)
            cb.pack(fill="x", pady=5)
            self._safe_cbs.append(cb)

        # Осторожно
        warn_frame = ctk.CTkFrame(apps_card, fg_color="transparent")
        warn_frame.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(warn_frame, text="⚠️ Осторожно (может повлиять на функции):", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=WARNING).pack(anchor="w", pady=(0, 4))

        warn_apps = [
            ("Microsoft 365 (Office)", "Удаление отвяжет интеграцию Office от системы. Устанавливайте только если используете сторонние офисные пакеты."),
            ("Xbox", "Удаление сломает интеграцию с Xbox Game Bar и Game Pass. Удаляйте, только если вообще не играете в игры от Microsoft."),
            ("Copilot", "Полное удаление ИИ-помощника от Microsoft. Может затронуть некоторые функции поиска.")
        ]
        self._warn_cbs = []
        for app, tooltip_text in warn_apps:
            row = ctk.CTkFrame(warn_frame, fg_color="transparent")
            row.pack(fill="x", padx=10)
            cb = TweakCheckbox(row, app, default=False)
            cb.pack(side="left")
            self._warn_cbs.append(cb)

            help_lbl = ctk.CTkLabel(row, text=" ❔ ", font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=ACCENT, cursor="hand2")
            help_lbl.pack(side="left", padx=4)
            add_tooltip(help_lbl, tooltip_text)

        # Компоненты Windows
        comp_frame = ctk.CTkFrame(apps_card, fg_color="transparent")
        comp_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(comp_frame, text="⚙️ Компоненты Windows:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=TEXT_PRIM).pack(anchor="w", pady=(0, 4))
        
        comps = [
            ("Internet Explorer", "Старый браузер (уже не поддерживается)."),
            ("Windows Hello", "Распознавание лиц и биометрия."),
            ("Математический ввод", "Панель ввода математических символов.")
        ]
        self._comp_cbs = []
        for comp, desc in comps:
            cb = TweakRow(comp_frame, "⚙️", comp, desc, default=True)
            cb.pack(fill="x", pady=5)
            self._comp_cbs.append(cb)

        # ── Блок 2: Менеджер автозагрузки ────────────────────────────────────
        autorun_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        autorun_card.pack(fill="x", padx=24, pady=(0, 10))

        autorun_header = ctk.CTkFrame(autorun_card, fg_color="transparent")
        autorun_header.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(autorun_header, text="🚀  Менеджер Автозагрузки", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=TEXT_PRIM).pack(side="left")
        ctk.CTkButton(autorun_header, text="Оставить только основные", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=WARNING, hover_color="#D97706", height=32, command=self._disable_third_party_autorun).pack(side="right")

        self._autorun_list = ctk.CTkScrollableFrame(autorun_card, fg_color=BG_DARK, height=180, border_width=1, border_color=BORDER)
        self._autorun_list.pack(fill="x", padx=20, pady=(0, 20))

        # Привязка прокрутки для списка автозагрузки
        self._autorun_list.bind("<MouseWheel>", self._on_autorun_scroll)
        self._autorun_list._parent_canvas.bind("<MouseWheel>", self._on_autorun_scroll)
        
        self._load_autoruns()

        # ── Блок 3: Системная очистка ────────────────────────────────────────
        clean_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        clean_card.pack(fill="x", padx=24, pady=(0, 10))

        ctk.CTkLabel(clean_card, text="🧹  Системная очистка", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=TEXT_PRIM).pack(anchor="w", padx=20, pady=(16, 12))

        clean_tasks = [
            ("Временные файлы (Temp)", "🗑️", "Очистка системных и пользовательских временных папок."),
            ("Кэш обновлений", "🔄", "Очистка папки SoftwareDistribution\\Download."),
            ("Кэш DirectX", "🎮", "Очистка шейдеров (Shader Cache) в AppData.")
        ]
        self._clean_cbs = []
        for item, icon, desc in clean_tasks:
            cb = TweakRow(clean_card, icon, item, desc, default=True)
            cb.pack(fill="x", pady=5, padx=20)
            self._clean_cbs.append(cb)

        ctk.CTkButton(clean_card, text="Запустить очистку", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOV, height=36, command=self._run_cleanup).pack(anchor="w", padx=20, pady=16)

        # ── Блок 4: Буфер обмена ─────────────────────────────────────────────
        clip_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        clip_card.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(clip_card, text="📋  Буфер обмена", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=TEXT_PRIM).pack(anchor="w", padx=20, pady=(16, 10))
        self._clipboard_cb = TweakRow(clip_card, "📋", "Журнал буфера обмена", "Позволяет использовать Win + V для истории копирования.", default=True)
        self._clipboard_cb.pack(fill="x", pady=15, padx=20)

        # ── Блок 5: Логи очистки ──────────────────────────────────────────────
        log_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER)
        log_card.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(log_card, text="📜  Лог операций", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=TEXT_PRIM).pack(anchor="w", padx=20, pady=(12, 8))

        self._log_box = ctk.CTkTextbox(log_card, height=150, fg_color=BG_DARK, border_color=BORDER, border_width=1,
                                       font=ctk.CTkFont("Consolas", 12), text_color=TEXT_SEC)
        self._log_box.pack(fill="x", padx=20, pady=(0, 20))
        self._log_box.configure(state="disabled")

        # Блокировка прокрутки родительского фрейма при наведении на лог
        self._log_box.bind("<MouseWheel>", self._on_log_scroll)

    def _on_log_scroll(self, event):
        """Обработка прокрутки внутри лог-бокса без прокрутки всей вкладки."""
        self._log_box.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _on_autorun_scroll(self, event):
        """Прокрутка списка автозагрузки без движения всей страницы."""
        self._autorun_list._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _log(self, text: str, level: str = "INFO"):
        """Потокобезопасное добавление записи в лог-бокс."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}] "
        
        def update():
            self._log_box.configure(state="normal")
            self._log_box.insert("end", f"{prefix}{text}\n")
            self._log_box.see("end")
            self._log_box.configure(state="disabled")
            
        self.after(0, update)

    def _load_autoruns(self):
        """Парсит автозагрузку из реестра."""
        # Для безопасности системные процессы мокаем или определяем по пути
        system_apps = ["SecurityHealth", "OneDrive", "ctfmon", "RtkAudUService"]
        
        entries = []
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
            for i in range(1024):
                try:
                    name, val, _ = winreg.EnumValue(key, i)
                    entries.append({"name": name, "path": val, "hive": "HKCU"})
                except OSError: break
            winreg.CloseKey(key)
        except Exception: pass
        
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
            for i in range(1024):
                try:
                    name, val, _ = winreg.EnumValue(key, i)
                    entries.append({"name": name, "path": val, "hive": "HKLM"})
                except OSError: break
            winreg.CloseKey(key)
        except Exception: pass

        if not entries:
            ctk.CTkLabel(self._autorun_list, text="Программы в автозагрузке не найдены", text_color=TEXT_SEC).pack(pady=10)
            return

        self._autorun_switches = []
        for app in entries:
            row = ctk.CTkFrame(self._autorun_list, fg_color="transparent")
            row.pack(fill="x", pady=4)
            
            is_system = any(s.lower() in app["name"].lower() or s.lower() in app["path"].lower() for s in system_apps)
            
            name_text = app["name"]
            if is_system:
                name_text += " (системные)"
                
            lbl = ctk.CTkLabel(row, text=name_text, font=ctk.CTkFont("Segoe UI", 12, "bold" if is_system else "normal"),
                               text_color=TEXT_PRIM if not is_system else SUCCESS)
            lbl.pack(side="left", padx=10)
            
            sw = ctk.CTkSwitch(row, text="", progress_color=ACCENT, width=40)
            sw.select()
            sw.pack(side="right", padx=10)
            
            if is_system:
                sw.configure(state="disabled")
            else:
                self._autorun_switches.append(sw)

    def _disable_third_party_autorun(self):
        for sw in self._autorun_switches:
            sw.deselect()

    def _run_cleanup(self):
        """Запускает процесс очистки выбранных категорий."""
        selected_tasks = []
        for cb in self._clean_cbs:
            if cb.get():
                selected_tasks.append(cb._cb.cget("text"))

        if not selected_tasks:
            return

        # Запуск в отдельном потоке, чтобы не вешать UI
        threading.Thread(target=self._cleanup_worker, args=(selected_tasks,), daemon=True).start()

    def _cleanup_worker(self, tasks):
        self._log("Инициализация процесса очистки...", "SYSTEM")
        self._log(f"Выбранные задачи: {', '.join(tasks)}")
        
        if "Временные файлы (Temp)" in tasks:
            self._clean_temp_files()
        
        if "Кэш обновлений (SoftwareDistribution)" in tasks:
            self._clean_update_cache()
            
        if "Кэш DirectX (Shader Cache)" in tasks:
            self._clean_directx_cache()

        self._log("Все операции по очистке успешно завершены.", "SUCCESS")

    def _clean_temp_files(self):
        self._log("Очистка временных файлов (Temp)...")
        paths = [
            os.environ.get('TEMP'),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')
        ]
        for path in paths:
            if path and os.path.exists(path):
                self._log(f"Обработка: {path}")
                self._delete_folder_contents(path)
        self._log("Временные файлы очищены.", "DONE")

    def _clean_update_cache(self):
        self._log("Очистка кэша обновлений Windows...", "WAIT")
        try:
            self._log("Остановка службы wuauserv...")
            subprocess.run(["net", "stop", "wuauserv"], capture_output=True, check=False)
            path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'SoftwareDistribution\\Download')
            if os.path.exists(path):
                self._log(f"Удаление загрузок: {path}")
                self._delete_folder_contents(path)
            self._log("Запуск службы wuauserv...")
            subprocess.run(["net", "start", "wuauserv"], capture_output=True, check=False)
            self._log("Кэш обновлений очищен.", "DONE")
        except Exception as e:
            self._log(f"Ошибка при очистке кэша обновлений: {e}", "ERROR")

    def _clean_directx_cache(self):
        self._log("Очистка кэша DirectX Shader...")
        user_profile = os.environ.get('USERPROFILE')
        if user_profile:
            path = os.path.join(user_profile, 'AppData\\Local\\D3DSCache')
            if os.path.exists(path):
                self._log(f"Удаление кэша в: {path}")
                self._delete_folder_contents(path)
        self._log("Кэш DirectX очищен.", "DONE")

    def _delete_folder_contents(self, folder_path):
        """Вспомогательный метод для удаления содержимого папки без удаления самой папки."""
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.is_dir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                # Файлы в использовании — нормальное явление для Temp
                pass
