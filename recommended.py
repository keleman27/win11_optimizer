"""
recommended.py — Вкладка 2: Рекомендуемые настройки (Быстрый старт).
"""

import customtkinter as ctk
import threading
from tweaks import (
    VISUAL_EFFECTS, apply_visual_effects, apply_power_plan,
    apply_copilot_disable, apply_explorer_settings,
    get_visual_effects_state, is_copilot_disabled
)
from registry_backup import backup_all_tweak_keys
from restart_dialog import RestartDialog
from state import app_state
from system_sync import sync_engine

# ── Цвета ────────────────────────────────────────────────────────────────
ACCENT      = "#4F8EF7"
ACCENT_HOV  = "#3A75E0"
SUCCESS     = "#4CAF50"
WARNING     = "#FF9800"
DANGER      = "#F44336"
BG_CARD     = "#1E2130"
BG_DARK     = "#161824"
BORDER      = "#2D3354"
TEXT_PRIM   = "#EAEEF8"
TEXT_SEC    = "#8B9BB4"
NAV_ACTIVE  = "#1E2A45"


# ════════════════════════════════════════════════════════════════════════════
# Вспомогательные виджеты
# ════════════════════════════════════════════════════════════════════════════

class SectionCard(ctk.CTkFrame):
    """Карточка-раздел с заголовком и collapsible-телом."""

    def __init__(self, parent, title: str, icon: str = "⚙️",
                 expanded: bool = True, **kw):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        self._expanded = expanded

        # ── Шапка (кликабельная) ─────────────────────────────────────────
        self._header = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        self._header.pack(fill="x", padx=16, pady=(12, 0))

        self._arrow = ctk.CTkLabel(
            self._header, text="▾" if expanded else "▸",
            font=ctk.CTkFont("Segoe UI", 14), text_color=TEXT_SEC, width=20)
        self._arrow.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            self._header, text=f"{icon}  {title}",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIM
        ).pack(side="left")

        self._header.bind("<Button-1>", self._toggle)
        for w in self._header.winfo_children():
            w.bind("<Button-1>", self._toggle)

        # ── Тело ─────────────────────────────────────────────────────────
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        if expanded:
            self._body.pack(fill="x", padx=16, pady=(8, 14))
        else:
            ctk.CTkFrame(self, height=1, fg_color=BORDER
                         ).pack(fill="x", padx=16, pady=(8, 0))

    @property
    def body(self):
        return self._body

    def _toggle(self, _=None):
        self._expanded = not self._expanded
        self._arrow.configure(text="▾" if self._expanded else "▸")
        if self._expanded:
            self._body.pack(fill="x", padx=16, pady=(8, 14))
        else:
            self._body.pack_forget()


class TweakCheckbox(ctk.CTkFrame):
    """Строка чекбокса с меткой, вписывается в карточку."""

    def __init__(self, parent, text: str, default: bool = False, command=None, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._var = ctk.BooleanVar(value=default)
        self._cb = ctk.CTkCheckBox(
            self, text=text, variable=self._var,
            font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT_PRIM,
            fg_color=ACCENT, hover_color=ACCENT_HOV,
            checkmark_color="#FFFFFF", border_color=BORDER,
            corner_radius=4, command=command
        )
        self._cb.pack(anchor="w", padx=4, pady=2)

    @property
    def var(self) -> ctk.BooleanVar:
        return self._var

    def get(self) -> bool:
        return self._var.get()

    def set(self, value: bool):
        self._var.set(value)


class MiniBlock(ctk.CTkFrame):
    """Усечённый блок (Gaming / Cleanup / BitLocker) с кнопкой «Подробнее»."""

    def __init__(self, parent, icon: str, title: str, description: str,
                 tab_index: int, switch_tab_callback, **kw):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(left, text=f"{icon}  {title}",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=TEXT_PRIM).pack(anchor="w")
        
        desc_lbl = ctk.CTkLabel(left, text=description,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=TEXT_SEC, justify="left"
                     )
        desc_lbl.pack(anchor="w", fill="x", pady=(4, 0))
        # Dynamically update wraplength on resize safely
        def _resize_desc_lbl(e, lbl=desc_lbl):
            current = lbl.cget("wraplength")
            new_w = max(100, e.width - 10)
            if current == "" or abs(int(current) - new_w) > 5:
                lbl.configure(wraplength=new_w)
        desc_lbl.bind("<Configure>", _resize_desc_lbl)

        ctk.CTkButton(
            row, text="Подробнее →",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color="transparent", hover_color=NAV_ACTIVE,
            border_width=1, border_color=ACCENT,
            text_color=ACCENT, width=110, height=34, corner_radius=8,
            command=lambda: switch_tab_callback(tab_index)
        ).pack(side="right", padx=(12, 0))


# ════════════════════════════════════════════════════════════════════════════
# Главный фрейм вкладки
# ════════════════════════════════════════════════════════════════════════════

class RecommendedFrame(ctk.CTkScrollableFrame):

    def __init__(self, parent, switch_tab_callback=None, **kw):
        super().__init__(parent, fg_color=BG_DARK,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=ACCENT, **kw)
        self._switch_tab = switch_tab_callback
        self._fx_checkboxes: list[TweakCheckbox] = []
        self._build_ui()

    # ── Построение интерфейса ─────────────────────────────────────────────

    def _build_ui(self):
        # ── Верхняя панель действий ───────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12,
                           border_width=1, border_color=BORDER)
        top.pack(fill="x", padx=24, pady=(20, 12))

        bar = ctk.CTkFrame(top, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=12)

        self._apply_btn = ctk.CTkButton(
            bar, text="✅  Применить выбранное",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOV,
            height=40, corner_radius=10,
            command=self._on_apply
        )
        self._apply_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bar, text="Выделить всё",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color=NAV_ACTIVE,
            border_width=1, border_color=BORDER, text_color=TEXT_SEC,
            height=40, corner_radius=10,
            command=lambda: self._select_all(True)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bar, text="Снять всё",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color=NAV_ACTIVE,
            border_width=1, border_color=BORDER, text_color=TEXT_SEC,
            height=40, corner_radius=10,
            command=lambda: self._select_all(False)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bar, text="⭐ По умолчанию",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color="#1A2A1A",
            border_width=1, border_color="#4CAF50", text_color="#4CAF50",
            height=40, corner_radius=10,
            command=self._set_defaults
        ).pack(side="left")

        self._status_lbl = ctk.CTkLabel(
            bar, text="", font=ctk.CTkFont("Segoe UI", 12), text_color=SUCCESS)
        self._status_lbl.pack(side="right")

        # ── Блок 1: Визуальные эффекты ────────────────────────────────────
        fx_card = SectionCard(self, "Визуальные эффекты", "🖼️", expanded=True)
        fx_card.pack(fill="x", padx=24, pady=(0, 10))

        cols = ctk.CTkFrame(fx_card.body, fg_color="transparent")
        cols.pack(fill="x")
        cols.columnconfigure((0, 1), weight=1)

        # Initialize visual effects based on system state
        enabled_fx = get_visual_effects_state()
        for i, fx in enumerate(VISUAL_EFFECTS):
            is_enabled = i in enabled_fx
            cb = TweakCheckbox(cols, fx["label"], default=is_enabled, command=self._clear_status)
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=4, pady=1)
            self._fx_checkboxes.append(cb)

        # ── Блок 2: Система и Питание ─────────────────────────────────────
        pwr_card = SectionCard(self, "Система и Питание", "⚡", expanded=True)
        pwr_card.pack(fill="x", padx=24, pady=(0, 10))

        is_laptop = app_state.device_type == "Ноутбук"
        pwr_label = ("Сбалансированная (ноутбук)" if is_laptop
                     else "Максимальная производительность")
        pwr_default = not is_laptop   # для ПК — галочка стоит по умолчанию

        self._pwr_cb = TweakCheckbox(
            pwr_card.body,
            f"Схема питания: {pwr_label}",
            default=pwr_default,
            command=self._clear_status
        )
        self._pwr_cb.pack(anchor="w")

        sleep_label = "Отключить сон и отключение экрана (⚠️ может вызвать перегрев в сумке)" if is_laptop else "Отключить сон и отключение экрана (Никогда)"
        self._sleep_cb = TweakCheckbox(
            pwr_card.body, sleep_label, default=pwr_default, command=self._clear_status)
        self._sleep_cb.pack(anchor="w")

        self._copilot_cb = TweakCheckbox(
            pwr_card.body, "Отключить кнопку Copilot на панели задач",
            default=is_copilot_disabled(), command=self._clear_status)
        self._copilot_cb.pack(anchor="w")

        # ── Блок: Текущее состояние системы (Audit) ──────────────────────
        audit_card = SectionCard(self, "Аудит и Состояние системы", "🔍", expanded=True)
        audit_card.pack(fill="x", padx=24, pady=(0, 10))
        
        self._sync_items = {} # {key: checkbox}
        
        audit_items = [
            ("dark_mode", "Тёмная тема Windows"),
            ("high_perf", "Режим высокой производительности"),
            ("game_mode", "Игровой режим (Game Mode)"),
            ("wifi_enabled", "Wi-Fi адаптер"),
            ("bluetooth_enabled", "Bluetooth сервис")
        ]
        
        for key, label in audit_items:
            cb = TweakCheckbox(audit_card.body, label, default=False)
            cb.pack(anchor="w")
            self._sync_items[key] = cb
            # Register for real-time updates
            sync_engine.register(key, cb.set)

        # Обновляем подпись схемы питания, если тип устройства сменится
        app_state.on_device_type_change(self._refresh_power_label)

        # ── Блок 3: Проводник ─────────────────────────────────────────────
        exp_card = SectionCard(self, "Проводник (Explorer)", "📁", expanded=True)
        exp_card.pack(fill="x", padx=24, pady=(0, 10))

        self._launch_cb = TweakCheckbox(
            exp_card.body, "Открывать «Этот компьютер» по умолчанию", default=True, command=self._clear_status)
        self._launch_cb.pack(anchor="w")

        self._recycle_nav_cb = TweakCheckbox(
            exp_card.body, "Добавить Корзину в боковую панель Проводника", default=True, command=self._clear_status)
        self._recycle_nav_cb.pack(anchor="w")

        self._hide_recycle_cb = TweakCheckbox(
            exp_card.body, "Скрыть Корзину с Рабочего стола", default=False, command=self._clear_status)
        self._hide_recycle_cb.pack(anchor="w")

        self._kill_task_cb = TweakCheckbox(
            exp_card.body, "Включить функцию «Завершить задачу» (Kill task)", default=True, command=self._clear_status)
        self._kill_task_cb.pack(anchor="w")

        # ── Блок 4: Игровой режим (усечённый) ────────────────────────────
        MiniBlock(
            self, "🕹️", "Игровой режим и Периферия",
            "Game Mode, HAGS, VRR, акселерация мыши, качество звука.",
            tab_index=4, switch_tab_callback=self._switch_tab
        ).pack(fill="x", padx=24, pady=(0, 10))

        # ── Блок 5: Очистка (усечённый) ──────────────────────────────────
        MiniBlock(
            self, "🧹", "Очистка и Приложения (Debloat)",
            "Удаление встроенных приложений, автозагрузка, очистка Temp.",
            tab_index=3, switch_tab_callback=self._switch_tab
        ).pack(fill="x", padx=24, pady=(0, 10))

        # ── Блок 6: BitLocker (усечённый) ─────────────────────────────────
        MiniBlock(
            self, "🔒", "Безопасность и Экспертные настройки",
            "BitLocker, защита стека (Faceit), активация Windows.",
            tab_index=5, switch_tab_callback=self._switch_tab
        ).pack(fill="x", padx=24, pady=(0, 24))

    # ── Обработчики ───────────────────────────────────────────────────────

    def _refresh_power_label(self, dtype: str):
        """Обновляет подпись схемы питания при смене типа устройства."""
        is_laptop = dtype == "Ноутбук"
        label = ("Сбалансированная (ноутбук)" if is_laptop
                 else "Максимальная производительность")
        self._pwr_cb._cb.configure(text=f"Схема питания: {label}")
        self._pwr_cb.set(not is_laptop)

        sleep_label = "Отключить сон и отключение экрана (⚠️ может вызвать перегрев в сумке)" if is_laptop else "Отключить сон и отключение экрана (Никогда)"
        self._sleep_cb._cb.configure(text=sleep_label)
        self._sleep_cb.set(not is_laptop)

    def _clear_status(self):
        """Скрывает статусное сообщение при ручном изменении настроек."""
        if self._status_lbl.cget("text") == "⭐ Выбраны рекомендуемые настройки Win11 Optimizer":
            self._status_lbl.configure(text="")

    def _select_all(self, state: bool):
        self._clear_status()
        for cb in self._fx_checkboxes:
            cb.set(state)
        for cb in (self._pwr_cb, self._copilot_cb, self._sleep_cb,
                   self._launch_cb, self._recycle_nav_cb, self._hide_recycle_cb, self._kill_task_cb):
            cb.set(state)

    def _set_defaults(self):
        """Восстанавливает рекомендуемые настройки Win11 Optimizer."""
        # Визуальные эффекты — только помеченные recommended=True
        for i, (cb, fx) in enumerate(zip(self._fx_checkboxes, VISUAL_EFFECTS)):
            cb.set(fx["recommended"])

        # Питание и сон
        is_laptop = app_state.device_type == "Ноутбук"
        self._pwr_cb.set(not is_laptop)
        self._sleep_cb.set(not is_laptop)

        # Copilot — отключить (рекомендуется)
        self._copilot_cb.set(True)

        # Проводник
        self._launch_cb.set(True)        # Этот компьютер
        self._recycle_nav_cb.set(True)   # Корзина в боковой панели
        self._hide_recycle_cb.set(False) # Не скрывать корзину с рабочего стола
        self._kill_task_cb.set(True)     # Kill task

        self._status_lbl.configure(
            text="⭐ Выбраны рекомендуемые настройки Win11 Optimizer",
            text_color="#4CAF50"
        )

    def _on_apply(self):
        """Запускает применение в фоне с бэкапом реестра."""
        self._apply_btn.configure(state="disabled", text="⏳ Применяется…")
        self._status_lbl.configure(text="")
        threading.Thread(target=self._apply_worker, daemon=True).start()

    def _apply_worker(self):
        needs_restart = False
        try:
            # 1. Бэкап реестра
            backup_all_tweak_keys()

            # 2. Визуальные эффекты
            enabled = [i for i, cb in enumerate(self._fx_checkboxes)
                       if cb.var.get()]
            apply_visual_effects(enabled)
            needs_restart = True

            # 3. Питание
            if self._pwr_cb.var.get():
                is_laptop = app_state.device_type == "Ноутбук"
                apply_power_plan(is_laptop)

            # 4. Copilot
            if self._copilot_cb.var.get():
                apply_copilot_disable()
                needs_restart = True

            # 5. Проводник
            apply_explorer_settings(
                open_to_this_pc=self._launch_cb.var.get(),
                recycle_in_nav=self._recycle_nav_cb.var.get(),
                hide_recycle_desktop=self._hide_recycle_cb.var.get()
            )
            needs_restart = True

            self.after(0, lambda: self._on_done(needs_restart, success=True))
        except Exception as e:
            self.after(0, lambda: self._on_done(False, success=False, error=str(e)))

    def _on_done(self, needs_restart: bool, success: bool, error: str = ""):
        self._apply_btn.configure(state="normal", text="✅  Применить выбранное")
        if success:
            self._status_lbl.configure(
                text="✔ Бэкап создан, настройки применены", text_color=SUCCESS)
            if needs_restart:
                RestartDialog(self.winfo_toplevel())
        else:
            self._status_lbl.configure(
                text=f"❌ Ошибка: {error}", text_color=DANGER)
