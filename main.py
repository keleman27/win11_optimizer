"""
main.py — Точка входа. Main GUI на CustomTkinter.
Боковое меню (Sidebar) + переключение фреймов-вкладок.
"""

import customtkinter as ctk
import sys
import ctypes
from dashboard import DashboardFrame
from recommended import RecommendedFrame
from drivers import DriversFrame
from cleanup import CleanupFrame
from gaming import GamingFrame
from security import SecurityFrame
from system_sync import sync_engine

# ── Настройки темы ─────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Цветовая схема (дублируется из dashboard для sidebar) ─────────────────
ACCENT      = "#4F8EF7"
ACCENT_HOV  = "#3A75E0"
BG_CARD     = "#1A1A1E"          # Чуть светлее для карточек
BG_DARK     = "#111114"          # Глубокий темный фон
BG_SIDEBAR  = "#0D0D0F"          # Почти черный для сайдбара
TEXT_PRIM   = "#EAEEF8"
TEXT_SEC    = "#8B9BB4"
BORDER      = "#28282D"
NAV_ACTIVE  = "#1E1E24"


# ── Вкладки (tabs) по категориям ───────────────────────────────────────────
TABS_CATEGORIES = {
    "ОБЩЕЕ": [
        ("🏠", "Главная", 0),
    ],
    "ОПТИМИЗАЦИЯ": [
        ("⚡", "Рекомендуемые", 1),
        ("🧹", "Очистка", 3),
    ],
    "СИСТЕМА": [
        ("🎮", "Драйверы", 2),
        ("🕹️", "Игровые", 4),
        ("🔒", "Безопасность", 5),
    ]
}

# Общее количество вкладок для инициализации
TOTAL_TABS_COUNT = 6


class PlaceholderFrame(ctk.CTkFrame):
    """Временная заглушка для вкладок, которые ещё не реализованы."""

    def __init__(self, parent, tab_name: str, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        ctk.CTkLabel(
            self,
            text=f"🚧  Вкладка «{tab_name}» в разработке",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=TEXT_SEC
        ).place(relx=0.5, rely=0.5, anchor="center")


class SidebarButton(ctk.CTkFrame):
    """Кастомная кнопка бокового меню с иконкой + текстом + hover/active состоянием."""

    def __init__(self, parent, icon: str, label: str,
                 command=None, active: bool = False, **kwargs):
        super().__init__(
            parent,
            fg_color=NAV_ACTIVE if active else "transparent",
            corner_radius=10,
            cursor="hand2",
            **kwargs
        )
        self._command = command
        self._active = active

        # Иконка
        self._icon_lbl = ctk.CTkLabel(
            self, text=icon,
            font=ctk.CTkFont("Segoe UI", 18),
            width=32, text_color=TEXT_PRIM if active else TEXT_SEC
        )
        self._icon_lbl.pack(side="left", padx=(12, 2), pady=10)

        # Текст
        self._text_lbl = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont("Segoe UI", 13, "bold" if active else "normal"),
            text_color=TEXT_PRIM if active else TEXT_SEC,
            anchor="w"
        )
        self._text_lbl.pack(side="left", fill="x", expand=True, padx=(2, 12))

        # Привязка кликов ко всем дочерним элементам
        for widget in (self, self._icon_lbl, self._text_lbl, self._stripe):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, _event=None):
        if self._command:
            self._command()

    def _on_enter(self, _event=None):
        if not self._active:
            self.configure(fg_color="#18181D")

    def _on_leave(self, _event=None):
        if not self._active:
            self.configure(fg_color="transparent")

    def set_active(self, active: bool):
        self._active = active
        self.configure(fg_color=NAV_ACTIVE if active else "transparent")
        self._icon_lbl.configure(text_color=TEXT_PRIM if active else TEXT_SEC)
        self._text_lbl.configure(
            font=ctk.CTkFont("Segoe UI", 13, "bold" if active else "normal"),
            text_color=TEXT_PRIM if active else TEXT_SEC
        )


class App(ctk.CTk):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.title("Win11 Optimizer")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=BG_DARK)

        # Иконка окна (если есть)
        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass

        self._current_tab = 0
        self._tab_frames: list[ctk.CTkFrame | None] = [None] * TOTAL_TABS_COUNT

        # Запуск фоновой синхронизации системных параметров
        sync_engine.set_dispatcher(self.after)
        sync_engine.start_monitoring()

        self._build_layout()
        self._show_tab(0)

    # ── Построение макета ─────────────────────────────────────────────────

    def _build_layout(self):
        # Основная сетка: sidebar | divider | content
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=0)  # divider
        self.grid_columnconfigure(2, weight=1)  # content
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        # Логотип / заголовок сайдбара
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 16))

        ctk.CTkLabel(
            logo_frame, text="Win11",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=ACCENT
        ).pack(side="left")
        ctk.CTkLabel(
            logo_frame, text=" Optimizer",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=TEXT_PRIM
        ).pack(side="left")

        # Тонкий разделитель
        ctk.CTkFrame(sidebar, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", padx=12, pady=(0, 12)
        )

        # Кнопки навигации по категориям
        nav_container = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent",
            scrollbar_button_color=BG_SIDEBAR,
            scrollbar_button_hover_color=BORDER,
            corner_radius=0, border_width=0
        )
        nav_container.pack(fill="both", expand=True, padx=4)

        self._nav_buttons: dict[int, SidebarButton] = {}
        
        for category, items in TABS_CATEGORIES.items():
            # Заголовок категории (как на скриншоте)
            cat_lbl = ctk.CTkLabel(
                nav_container, text=category,
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
                text_color="#4A4A4F", anchor="w"
            )
            cat_lbl.pack(fill="x", padx=16, pady=(12, 4))
            
            for icon, label, idx in items:
                btn = SidebarButton(
                    nav_container, icon=icon, label=label,
                    command=lambda i=idx: self._show_tab(i),
                    active=(idx == 0)
                )
                btn.pack(fill="x", pady=1, padx=4)
                self._nav_buttons[idx] = btn

        # Нижний блок сайдбара — версия
        ctk.CTkLabel(
            sidebar, text="v1.0.0  |  Python + CTk",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=TEXT_SEC
        ).pack(side="bottom", pady=12)

        # ── Разделитель ───────────────────────────────────────────────────
        divider = ctk.CTkFrame(self, width=1, fg_color=BORDER, corner_radius=0)
        divider.grid(row=0, column=1, sticky="nsew")

        # ── Контентная зона ───────────────────────────────────────────────
        self._content_area = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._content_area.grid(row=0, column=2, sticky="nsew")
        self._content_area.grid_rowconfigure(0, weight=1)
        self._content_area.grid_columnconfigure(0, weight=1)

    # ── Навигация ─────────────────────────────────────────────────────────

    def _show_tab(self, index: int):
        """Переключает вкладку по индексу."""
        if index == self._current_tab and self._tab_frames[index] is not None:
            return

        # Деактивируем старую кнопку
        self._nav_buttons[self._current_tab].set_active(False)

        self._current_tab = index
        self._nav_buttons[index].set_active(True)

        # Создаём фрейм вкладки при первом открытии (lazy init)
        if self._tab_frames[index] is None:
            self._tab_frames[index] = self._create_tab_frame(index)
            self._tab_frames[index].grid(row=0, column=0, sticky="nsew")

        # Плавно поднимаем новый фрейм наверх (без артефактов grid_forget)
        self._tab_frames[index].lift()

    def _create_tab_frame(self, index: int) -> ctk.CTkFrame:
        """Фабрика вкладок — создаёт нужный фрейм по индексу."""
        parent = self._content_area
        match index:
            case 0:
                return DashboardFrame(parent, switch_tab_callback=self._show_tab)
            case 1:
                return RecommendedFrame(parent, switch_tab_callback=self._show_tab)
            case 2:
                return DriversFrame(parent, switch_tab_callback=self._show_tab)
            case 3:
                return CleanupFrame(parent, switch_tab_callback=self._show_tab)
            case 4:
                return GamingFrame(parent, switch_tab_callback=self._show_tab)
            case 5:
                return SecurityFrame(parent, switch_tab_callback=self._show_tab)
            case _:
                return PlaceholderFrame(parent, tab_name="Unknown")


# ── Запуск ─────────────────────────────────────────────────────────────────

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ── Запуск ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not is_admin():
        # Перезапуск с правами администратора
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    app = App()
    app.mainloop()
