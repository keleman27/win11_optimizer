"""
gaming.py — Вкладка 5: Игровой режим и Периферия.
Оптимизация графики, мыши, звука и игровых функций Windows.
"""

import customtkinter as ctk
import tkinter as tk

ACCENT      = "#4F8EF7"
ACCENT_HOV  = "#3A75E0"
SUCCESS     = "#4CAF50"
WARNING     = "#FF9800"
BG_CARD     = "#1A1A1E"
BG_DARK     = "#111114"
BORDER      = "#28282D"
TEXT_PRIM   = "#EAEEF8"
TEXT_SEC    = "#8B9BB4"

class SectionCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, icon: str = "", **kwargs):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER, **kwargs)
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))
        
        icon_lbl = ctk.CTkLabel(header, text=icon, font=ctk.CTkFont("Segoe UI", 18))
        icon_lbl.pack(side="left", padx=(0, 10))
        
        title_lbl = ctk.CTkLabel(header, text=title, font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=TEXT_PRIM)
        title_lbl.pack(side="left")
        
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x", padx=20, pady=(0, 20))

class TweakRow(ctk.CTkFrame):
    """Строка настройки: Иконка + (Заголовок/Описание) + Переключатель."""
    def __init__(self, parent, icon: str, title: str, description: str = "", default: bool = False, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._var = ctk.BooleanVar(value=default)
        
        self._icon_lbl = ctk.CTkLabel(self, text=icon, font=ctk.CTkFont("Segoe UI", 16), text_color=ACCENT, width=30)
        self._icon_lbl.pack(side="left", padx=(0, 15))
        
        self._text_container = ctk.CTkFrame(self, fg_color="transparent")
        self._text_container.pack(side="left", fill="both", expand=True)
        
        self._title_lbl = ctk.CTkLabel(self._text_container, text=title, font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=TEXT_PRIM, anchor="w")
        self._title_lbl.pack(fill="x")
        
        if description:
            self._desc_lbl = ctk.CTkLabel(self._text_container, text=description, font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SEC, anchor="w", justify="left")
            self._desc_lbl.pack(fill="x")
        
        self._sw = ctk.CTkSwitch(self, text="", variable=self._var, progress_color=ACCENT, width=45)
        self._sw.pack(side="right", padx=(10, 0))

    def get(self): return self._var.get()
    def set(self, val): self._var.set(val)

class GamingFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, switch_tab_callback=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=ACCENT, **kwargs)
        self._switch_tab = switch_tab_callback
        self._build_ui()

    def _build_ui(self):
        # ── Блок 1: Графика и Игровой режим ──────────────────────────────────
        gfx_card = SectionCard(self, "Графика и Игровой режим", "🕹️")
        gfx_card.pack(fill="x", padx=24, pady=(24, 10))

        self._game_mode = TweakRow(gfx_card.body, "🎮", "Режим игры (Game Mode)", 
                                  "Приоритезирует ресурсы ПК для игр.", default=True)
        self._game_mode.pack(fill="x", pady=5)

        self._hags = TweakRow(gfx_card.body, "🚀", "Планирование GPU (HAGS)", 
                             "Уменьшает задержку за счет видеопамяти.", default=True)
        self._hags.pack(fill="x", pady=5)

        self._vrr = TweakRow(gfx_card.body, "🖥️", "Переменная частота (VRR)", 
                            "Устраняет разрывы экрана в играх.", default=True)
        self._vrr.pack(fill="x", pady=5)

        # ── Блок 2: Мышь и Ввод ──────────────────────────────────────────────
        mouse_card = SectionCard(self, "Периферия: Мышь и Ввод", "🖱️")
        mouse_card.pack(fill="x", padx=24, pady=(0, 10))

        self._mouse_accel = TweakRow(mouse_card.body, "🎯", "Отключить акселерацию", 
                                    "Raw Input для точного прицеливания.", default=True)
        self._mouse_accel.pack(fill="x", pady=5)

        self._sticky_keys = TweakRow(mouse_card.body, "⌨️", "Отключить залипание", 
                                    "Блокирует системные окна при зажатии Shift.", default=True)
        self._sticky_keys.pack(fill="x", pady=5)

        # ── Блок 3: Звук ─────────────────────────────────────────────────────
        sound_card = SectionCard(self, "Периферия: Звук", "🔊")
        sound_card.pack(fill="x", padx=24, pady=(0, 10))

        self._sound_quality = TweakRow(sound_card.body, "🎼", "Максимальное качество", 
                                      "Выставляет 24 бит/48 кГц автоматически.", default=True)
        self._sound_quality.pack(fill="x", pady=5)

        # ── Нижняя панель действий ───────────────────────────────────────────
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=24, pady=(20, 40))

        self._apply_btn = ctk.CTkButton(action_frame, text="Применить игровые настройки", 
                                        font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                        fg_color=ACCENT, hover_color=ACCENT_HOV, height=45,
                                        command=self._apply_tweaks)
        self._apply_btn.pack(side="left", padx=(0, 15), expand=True, fill="x")

        self._status_lbl = ctk.CTkLabel(action_frame, text="", font=ctk.CTkFont("Segoe UI", 12))
        self._status_lbl.pack(side="left")

    def _apply_tweaks(self):
        # Здесь будет логика применения через tweaks.py
        self._status_lbl.configure(text="✅ Настройки применены!", text_color=SUCCESS)
        self.after(3000, lambda: self._status_lbl.configure(text=""))
