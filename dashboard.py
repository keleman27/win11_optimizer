"""
dashboard.py — Вкладка 1: Главная (Дашборд).
Собирает информацию о системе и отображает её в красивом интерфейсе.
"""

import customtkinter as ctk
import threading
from system_info import collect_all_async, get_battery_info
from state import app_state


# ─────────────────────────────────────────────────────────────────────────────
# Цветовая схема (единый источник)
# ─────────────────────────────────────────────────────────────────────────────
ACCENT      = "#4F8EF7"          # синий акцент
ACCENT_HOV  = "#3A75E0"
SUCCESS     = "#4CAF50"
WARNING     = "#FF9800"
DANGER      = "#F44336"
BG_CARD     = "#1A1A1E"
BG_DARK     = "#111114"
BG_SIDEBAR  = "#0D0D0F"
TEXT_PRIM   = "#EAEEF8"
TEXT_SEC    = "#8B9BB4"
TEXT_MUT    = "#4A5568"
BORDER      = "#28282D"


class DiskBar(ctk.CTkFrame):
    """Мини-виджет: полоса загрузки для носителя."""

    def __init__(self, parent, drive: str, fs: str, total: str,
                 free: str, used_pct: float, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Определяем цвет полосы по заполненности
        if used_pct >= 90:
            bar_color = DANGER
        elif used_pct >= 70:
            bar_color = WARNING
        else:
            bar_color = ACCENT

        # Заголовок строки
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x")

        drive_lbl = ctk.CTkLabel(
            header, text=drive, font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=TEXT_PRIM
        )
        drive_lbl.pack(side="left")

        fs_lbl = ctk.CTkLabel(
            header, text=f"  {fs}", font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_SEC
        )
        fs_lbl.pack(side="left")

        pct_lbl = ctk.CTkLabel(
            header, text=f"{used_pct:.0f}%  •  {free}  •  {total}",
            font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SEC
        )
        pct_lbl.pack(side="right")

        # Прогресс-бар
        bar = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            progress_color=bar_color, fg_color=BORDER
        )
        bar.set(used_pct / 100)
        bar.pack(fill="x", pady=(4, 0))


class SysPassportCard(ctk.CTkFrame):
    """Карточка «Паспорт системы» с анимацией загрузки данных."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            **kwargs
        )
        self._build_skeleton()

    # ── внутренние методы ──────────────────────────────────────────────────

    def _build_skeleton(self):
        """Создаёт структуру карточки с заглушками-скелетонами."""
        # Заголовок карточки
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            title_row, text="🖥  Паспорт системы",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=TEXT_PRIM
        ).pack(side="left")

        self._status_dot = ctk.CTkLabel(
            title_row, text="⏳ Загрузка...",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_SEC
        )
        self._status_dot.pack(side="right")

        # Разделитель
        sep = ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0)
        sep.pack(fill="x", padx=16, pady=(4, 12))

        # Контейнер рядов
        self._rows_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._rows_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Заглушки рядов
        placeholders = ["ОС", "Процессор", "Видеокарта", "Материнская плата", "ОЗУ"]
        self._row_labels: dict[str, ctk.CTkLabel] = {}
        for label in placeholders:
            self._add_row(label, "…")

        # Разделитель перед носителями
        sep2 = ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0)
        sep2.pack(fill="x", padx=16, pady=(4, 10))

        disk_title = ctk.CTkLabel(
            self, text="💾  Носители",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=TEXT_PRIM
        )
        disk_title.pack(anchor="w", padx=20)

        self._disks_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._disks_frame.pack(fill="x", padx=20, pady=(6, 16))

        ctk.CTkLabel(
            self._disks_frame, text="Сканирование носителей…",
            font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SEC
        ).pack(anchor="w")

    def _add_row(self, label: str, value: str):
        """Добавляет строку «Метка : Значение»."""
        row = ctk.CTkFrame(self._rows_frame, fg_color="transparent")
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row, text=f"{label}:", width=150,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_SEC, anchor="w"
        ).pack(side="left")

        val_lbl = ctk.CTkLabel(
            row, text=value,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_PRIM, anchor="w", justify="left"
        )
        val_lbl.pack(side="left", fill="x", expand=True)
        # Dynamically update wraplength on resize safely
        def _resize_val_lbl(e, lbl=val_lbl):
            current = lbl.cget("wraplength")
            new_w = max(100, e.width - 10)
            if current == "" or abs(int(current) - new_w) > 5:
                lbl.configure(wraplength=new_w)
        val_lbl.bind("<Configure>", _resize_val_lbl)
        
        self._row_labels[label] = val_lbl

    def populate(self, data: dict):
        """Заполняет карточку реальными данными (вызывается из main thread)."""
        mapping = {
            "ОС": data.get("os", "—"),
            "Процессор": data.get("cpu", "—"),
            "Видеокарта": data.get("gpu", "—"),
            "Материнская плата": data.get("motherboard", "—"),
            "ОЗУ": data.get("ram", "—"),
        }
        for label, value in mapping.items():
            lbl = self._row_labels.get(label)
            if lbl:
                lbl.configure(text=value)

        # Носители — пересоздаём содержимое
        for child in self._disks_frame.winfo_children():
            child.destroy()

        disks = data.get("disks", [])
        if disks:
            for d in disks:
                bar = DiskBar(
                    self._disks_frame,
                    drive=d["drive"],
                    fs=d["fs"],
                    total=d["total"],
                    free=d["free"],
                    used_pct=d["used_pct"]
                )
                bar.pack(fill="x", pady=(0, 6))
        else:
            ctk.CTkLabel(
                self._disks_frame, text="Носители не найдены",
                font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SEC
            ).pack(anchor="w")

        self._status_dot.configure(text="✅ Актуально", text_color=SUCCESS)


class RestorePointStatus(ctk.CTkFrame):
    """Полоска статуса точки восстановления внизу дашборда."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            **kwargs
        )
        self._icon = ctk.CTkLabel(
            self, text="🛡️", font=ctk.CTkFont("Segoe UI", 13)
        )
        self._icon.pack(side="left", padx=(14, 6), pady=10)

        self._label = ctk.CTkLabel(
            self, text="Точка восстановления: не создана",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_SEC
        )
        self._label.pack(side="left", pady=10)

        self._btn = ctk.CTkButton(
            self, text="Создать сейчас",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOV,
            height=32, corner_radius=8,
            command=self._create_restore_point
        )
        self._btn.pack(side="right", padx=14, pady=8)

    def _create_restore_point(self):
        self._label.configure(text="⏳ Создание точки восстановления…", text_color=WARNING)
        self._btn.configure(state="disabled")

        def _worker():
            import subprocess
            try:
                # 1. Включаем защиту системы для диска C:
                # 2. Сбрасываем лимит на частоту создания точек (24 часа)
                # 3. Создаем точку
                ps_cmd = (
                    'Enable-ComputerRestore -Drive "C:\\"; '
                    'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore" '
                    '-Name "SystemRestorePointCreationFrequency" -Value 0 -Force; '
                    'Checkpoint-Computer -Description "Win11Optimizer Backup" -RestorePointType MODIFY_SETTINGS'
                )
                
                res = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True, text=True, timeout=180
                )
                
                if res.returncode == 0:
                    result = "✅ Точка восстановления успешно создана"
                    color = SUCCESS
                else:
                    # Извлекаем сообщение об ошибке
                    err_msg = res.stderr.strip().split('\n')[0] if res.stderr else "Неизвестная ошибка PS"
                    result = f"❌ Ошибка: {err_msg[:45]}..."
                    color = DANGER

            except Exception as e:
                result = f"❌ Ошибка: {str(e)[:45]}..."
                color = DANGER

            self.after(0, lambda: (
                self._label.configure(text=result, text_color=color),
                self._btn.configure(state="normal", text="Создать ещё")
            ))

        threading.Thread(target=_worker, daemon=True).start()


class DashboardFrame(ctk.CTkScrollableFrame):
    """
    Вкладка 1 — Главная (Дашборд).
    Содержит:
    • Заголовок с названием, версией, типом устройства
    • Карточку «Паспорт системы»
    • Кнопку «Перейти к рекомендуемым настройкам»
    • Полоску статуса точки восстановления
    """

    APP_NAME    = "Win11 Optimizer"
    APP_VERSION = "v1.0.0"

    def __init__(self, parent, switch_tab_callback=None, **kwargs):
        super().__init__(
            parent,
            fg_color=BG_DARK,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT,
            **kwargs
        )
        self._switch_tab = switch_tab_callback
        self._device_type = "…"
        self._build_ui()
        # Асинхронный сбор данных
        collect_all_async(self._on_data_ready)

    # ── построение интерфейса ──────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        # ── Шапка (Hero) ──────────────────────────────────────────────────
        hero = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=16,
                            border_width=1, border_color=BORDER)
        hero.pack(fill="x", padx=24, pady=(24, 12))

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=16)

        # Левый блок: имя программы + версия
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left, text=self.APP_NAME,
            font=ctk.CTkFont("Segoe UI", 28, "bold"),
            text_color=TEXT_PRIM
        ).pack(anchor="w")

        ctk.CTkLabel(
            left, text=self.APP_VERSION,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_SEC
        ).pack(anchor="w")

        # Правый блок: тип устройства (значение заполнится после сбора данных)
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        self._device_badge = ctk.CTkLabel(
            right, text="  ⏳ Определение…  ",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=BG_DARK,
            corner_radius=8,
            text_color=TEXT_SEC,
            padx=12, pady=6
        )
        self._device_badge.pack()

        # Индикатор батареи (показывается только для ноутбуков)
        self._battery_label = ctk.CTkLabel(
            right, text="",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_SEC
        )
        self._battery_label.pack(pady=(4, 0))

        # ── Карточка «Паспорт системы» ─────────────────────────────────────
        self._passport = SysPassportCard(self)
        self._passport.pack(fill="x", padx=24, pady=(0, 12))

        # ── Большая акцентная кнопка ───────────────────────────────────────
        cta_frame = ctk.CTkFrame(self, fg_color="transparent")
        cta_frame.pack(fill="x", padx=24, pady=(0, 12))

        self._cta_btn = ctk.CTkButton(
            cta_frame,
            text="🚀  ПЕРЕЙТИ К РЕКОМЕНДУЕМЫМ НАСТРОЙКАМ",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOV,
            height=52,
            corner_radius=12,
            command=self._on_cta_click
        )
        self._cta_btn.pack(fill="x")

        # ── Статус точки восстановления ────────────────────────────────────
        self._restore_status = RestorePointStatus(self)
        self._restore_status.pack(fill="x", padx=24, pady=(0, 24))

    # ── обработчики ───────────────────────────────────────────────────────

    def _on_data_ready(self, data: dict):
        """Вызывается из фонового потока после сбора данных."""
        # Все изменения GUI — только через after()
        self.after(0, lambda: self._update_ui(data))

    def _update_ui(self, data: dict):
        """Обновляет все виджеты реальными данными (main thread)."""
        dtype = data.get("device_type", "Стационарный ПК")
        self._device_type = dtype
        app_state.set_device_type(dtype)   # публикуем глобально

        icon = "💻" if dtype == "Ноутбук" else "🖥️"
        self._device_badge.configure(
            text=f"  {icon}  {dtype}  ",
            text_color=TEXT_PRIM,
            fg_color=ACCENT
        )

        # Батарея (только ноутбук)
        battery = data.get("battery")
        if battery:
            pct = battery["percent"]
            plugged = battery["plugged"]
            plug_icon = "⚡" if plugged else "🔋"
            bat_color = SUCCESS if pct >= 50 else (WARNING if pct >= 20 else DANGER)
            self._battery_label.configure(
                text=f"{plug_icon} {pct:.0f}%",
                text_color=bat_color
            )

        # Паспорт системы
        self._passport.populate(data)

    def _on_cta_click(self):
        if self._switch_tab:
            self._switch_tab(1)  # индекс вкладки «Рекомендуемые настройки»
