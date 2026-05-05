"""
recommended.py — Вкладка 2: Рекомендуемые настройки (Быстрый старт).
"""

import customtkinter as ctk
import threading
from tweaks import (
    VISUAL_EFFECTS, apply_visual_effects, apply_power_plan,
    apply_copilot_disable, apply_explorer_settings,
    get_visual_effects_state, is_copilot_disabled,
    get_current_power_scheme_guid, set_power_scheme,
    is_recommended_power_plan_active,
    POWER_BALANCED, POWER_HIGH, POWER_ULTIMATE,
    apply_dark_mode, get_dark_mode_state,
    get_game_mode_state, apply_game_mode,
    is_m365_copilot_blocked,
    is_launch_to_this_pc, is_recycle_bin_in_nav,
    is_recycle_bin_hidden_on_desktop, is_end_task_enabled,
    is_end_task_supported,
    restart_explorer,
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
BG_CARD     = "#1A1A1E"
BG_DARK     = "#111114"
BORDER      = "#28282D"
TEXT_PRIM   = "#EAEEF8"
TEXT_SEC    = "#8B9BB4"
NAV_ACTIVE  = "#1E1E24"


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
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
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
        self._initial_state = {} # {cb_object: bool}
        self._registered_callbacks = []  # Store callback references for cleanup
        self._build_ui()
        self._refresh_fx_checkboxes()

    def cleanup_callbacks(self):
        """Unregister all callbacks registered by this frame."""
        from system_sync import sync_engine
        sync_engine.unregister_all(self)

    def on_show(self):
        """Вызывается при переключении на эту вкладку (синхронизация)."""
        # Обновляем только визуальные эффекты (быстрая операция реестра)
        self._refresh_fx_checkboxes() 
        # Остальные состояния будут обновляться через sync_engine, т.к. они зарегистрированы
        self._capture_initial_state() # Запоминаем текущее состояние для кнопки "Применить"

    def _refresh_fx_checkboxes(self):
        """Обновляет состояние чекбоксов визуальных эффектов."""
        enabled_fx = get_visual_effects_state()
        for i, cb in enumerate(self._fx_checkboxes):
            cb.set(i in enabled_fx)

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
        # Button starts hidden until changes are detected
        # self._apply_btn.pack(side="left", padx=(0, 8)) # Will be packed in _check_for_changes

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

        self._default_btn = ctk.CTkButton(
            bar, text="↩️ Сбросить",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color="#1F2937",
            border_width=1, border_color=WARNING, text_color=WARNING,
            height=40, corner_radius=10,
            command=self._revert_to_initial
        )
        self._default_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bar, text="⭐ Рекомендовано",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color="#1F2937",
            border_width=1, border_color=SUCCESS, text_color=SUCCESS,
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
            cb = TweakCheckbox(cols, fx["label"], default=is_enabled, command=self._on_checkbox_toggle)
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=4, pady=1)
            self._fx_checkboxes.append(cb)

        # ── Блок 2: Система и Питание ─────────────────────────────────────
        pwr_card = SectionCard(self, "Система и Питание", "⚡", expanded=True)
        pwr_card.pack(fill="x", padx=24, pady=(0, 10))

        is_laptop = app_state.device_type == "Ноутбук"
        pwr_label = "сбалансированная" if is_laptop else "максимальная производительность"

        from tweaks import is_recommended_power_plan_active
        self._pwr_cb = TweakCheckbox(
            pwr_card.body,
            f"Схема питания: {pwr_label}",
            default=is_recommended_power_plan_active(is_laptop),
            command=self._on_checkbox_toggle
        )
        self._pwr_cb.pack(anchor="w")

        from tweaks import get_sleep_disabled_state
        sleep_label = "Отключить сон и отключение экрана (⚠️ может вызвать перегрев в сумке)" if is_laptop else "Отключить сон и отключение экрана (Никогда)"
        self._sleep_cb = TweakCheckbox(
            pwr_card.body, sleep_label, default=get_sleep_disabled_state(), command=self._on_checkbox_toggle)
        self._sleep_cb.pack(anchor="w")

        self._copilot_cb = TweakCheckbox(
            pwr_card.body, "Отключить кнопку Copilot на панели задач",
            default=is_copilot_disabled(), command=self._on_checkbox_toggle)
        self._copilot_cb.pack(anchor="w")

        # M365 Copilot functionality removed
        # self._m365_copilot_cb = TweakCheckbox(
        #     pwr_card.body, "Заблокировать Microsoft 365 Copilot",
        #     default=is_m365_copilot_blocked(), command=self._on_checkbox_toggle)
        # self._m365_copilot_cb.pack(anchor="w")

        # ── Блок: Текущее состояние системы (Audit) ──────────────────────
        audit_card = SectionCard(self, "Аудит и Состояние системы", "🔍", expanded=True)
        audit_card.pack(fill="x", padx=24, pady=(0, 10))
        
        self._sync_items = {} # {key: checkbox}

        # Инфо об ОЗУ (динамическое)
        ram_row = ctk.CTkFrame(audit_card.body, fg_color="transparent")
        ram_row.pack(fill="x", pady=(2, 6))
        
        ctk.CTkLabel(
            ram_row, text="📊 Состояние ОЗУ:", 
            font=ctk.CTkFont("Segoe UI", 12), 
            text_color=TEXT_SEC
        ).pack(side="left", padx=(4, 8))
        
        self._ram_lbl = ctk.CTkLabel(
            ram_row, text="Загрузка...", 
            font=ctk.CTkFont("Segoe UI", 12, "bold"), 
            text_color=TEXT_PRIM
        )
        self._ram_lbl.pack(side="left")
        
        sync_engine.register("ram_info", lambda v: self._ram_lbl.configure(text=v))
        
        # Специальный чекбокс для Темной темы (с обработчиком)
        self._dark_mode_cb = TweakCheckbox(
            audit_card.body, "Тёмная тема Windows", 
            default=get_dark_mode_state(), 
            command=self._on_checkbox_toggle
        )
        self._dark_mode_cb.pack(anchor="w")
        self._sync_items["dark_mode"] = self._dark_mode_cb
        dark_mode_callback = self._create_sync_wrapper(self._dark_mode_cb)
        sync_engine.register("dark_mode", dark_mode_callback)
        self._registered_callbacks.append(("dark_mode", dark_mode_callback))

                
        # Game Mode checkbox (interactive)
        self._game_mode_cb = TweakCheckbox(
            audit_card.body, "Игровой режим (Game Mode)",
            default=get_game_mode_state(),
            command=self._on_checkbox_toggle
        )
        self._game_mode_cb.pack(anchor="w")
        self._sync_items["game_mode"] = self._game_mode_cb
        game_mode_callback = self._create_sync_wrapper(self._game_mode_cb)
        sync_engine.register("game_mode", game_mode_callback)
        self._registered_callbacks.append(("game_mode", game_mode_callback))

        # Обновляем подпись схемы питания, если тип устройства сменится
        app_state.on_device_type_change(self._refresh_power_label)

        # ── Блок 3: Проводник ─────────────────────────────────────────────
        exp_card = SectionCard(self, "Проводник (Explorer)", "📁", expanded=True)
        exp_card.pack(fill="x", padx=24, pady=(0, 10))

        self._launch_cb = TweakCheckbox(
            exp_card.body, "Открывать «Этот компьютер» по умолчанию", default=is_launch_to_this_pc(), command=self._on_checkbox_toggle)
        self._launch_cb.pack(anchor="w")

        self._recycle_nav_cb = TweakCheckbox(
            exp_card.body, "Добавить Корзину в боковую панель Проводника", default=is_recycle_bin_in_nav(), command=self._on_checkbox_toggle)
        self._recycle_nav_cb.pack(anchor="w")

        self._hide_recycle_cb = TweakCheckbox(
            exp_card.body, "Скрыть Корзину с Рабочего стола", default=is_recycle_bin_hidden_on_desktop(), command=self._on_checkbox_toggle)
        self._hide_recycle_cb.pack(anchor="w")

        self._kill_task_cb = TweakCheckbox(
            exp_card.body, "Включить функцию «Завершить задачу» (Kill task)", 
            default=is_end_task_enabled() if is_end_task_supported() else False,
            command=self._on_checkbox_toggle)
        self._kill_task_cb.pack(anchor="w")
        if not is_end_task_supported():
            self._kill_task_cb._cb.configure(state="disabled")

        # Синхронизация состояний проводника
        explorer_sync_map = {
            "explorer_launch_this_pc": self._launch_cb,
            "recycle_in_nav": self._recycle_nav_cb,
            "recycle_hidden_desktop": self._hide_recycle_cb,
            "end_task_enabled": self._kill_task_cb,
        }
        for key, cb in explorer_sync_map.items():
            self._sync_items[key] = cb
            wrapper = self._create_sync_wrapper(cb)
            sync_engine.register(key, wrapper)
            self._registered_callbacks.append((key, wrapper))

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
        label = "сбалансированная" if is_laptop else "максимальная производительность"
        self._pwr_cb._cb.configure(text=f"Схема питания: {label}")

        sleep_label = "Отключить сон и отключение экрана (⚠️ может вызвать перегрев в сумке)" if is_laptop else "Отключить сон и отключение экрана (Никогда)"
        self._sleep_cb._cb.configure(text=sleep_label)
        
        # Перепроверяем состояние чекбоксов, так как критерии "рекомендованности" изменились
        self._refresh_checkboxes()

    def _capture_initial_state(self):
        """Сохраняет текущие значения всех чекбоксов для отката."""
        self._initial_state = {}
        for cb in self._fx_checkboxes:
            self._initial_state[cb] = cb.get()
        for cb in (self._pwr_cb, self._copilot_cb, self._sleep_cb,
                   self._launch_cb, self._recycle_nav_cb, self._hide_recycle_cb, self._kill_task_cb,
                   self._dark_mode_cb, self._game_mode_cb):
            self._initial_state[cb] = cb.get()
        self._update_apply_button_visibility()

    def _create_sync_wrapper(self, cb):
        """Создает обертку для sync_engine callback, обновляющую initial_state."""
        def wrapper(value):
            try:
                # Check if widget still exists before updating
                if hasattr(cb, 'winfo_exists') and not cb.winfo_exists():
                    return
                # Skip sync for disabled checkboxes (e.g. Kill Task on unsupported builds)
                if hasattr(cb, '_cb') and str(cb._cb.cget('state')) == 'disabled':
                    return
                # Если пользователь уже изменил значение и не применил, не затираем его
                current_initial = self._initial_state.get(cb)
                if current_initial is not None and cb.get() != current_initial:
                    return
                # Обновляем чекбокс
                cb.set(value)
                # Всегда обновляем initial_state при автоматической синхронизации
                # чтобы отслеживать реальные изменения системы
                self._initial_state[cb] = value
                # Проверяем, нужно ли скрыть кнопку Применить
                # Check if frame still exists
                if hasattr(self, 'winfo_exists') and self.winfo_exists():
                    self._update_apply_button_visibility()
            except Exception:
                pass  # Silently ignore errors from destroyed widgets
        return wrapper

    def _clear_status(self):
        """Скрывает статусное сообщение."""
        self._status_lbl.configure(text="")

    def _on_checkbox_toggle(self):
        self._clear_status()
        self._update_apply_button_visibility()

    def _update_apply_button_visibility(self):
        """Показывает кнопку Применить, если есть изменения."""
        has_changes = False
        for cb, val in self._initial_state.items():
            if cb.get() != val:
                has_changes = True
                break
        
        if has_changes:
            if not self._apply_btn.winfo_ismapped():
                self._apply_btn.pack(side="left", padx=(0, 8), before=self._status_lbl)
        else:
            self._apply_btn.pack_forget()

    def _select_all(self, state: bool):
        for cb in self._initial_state.keys():
            cb.set(state)
        self._on_checkbox_toggle()

    def _revert_to_initial(self):
        """Восстанавливает настройки до изменений пользователя."""
        for cb, val in self._initial_state.items():
            cb.set(val)
        self._on_checkbox_toggle()
        self._status_lbl.configure(text="↩️ Изменения сброшены", text_color=WARNING)

    def _set_defaults(self):
        """Восстанавливает рекомендуемые настройки Win11 Optimizer."""
        # Визуальные эффекты — только помеченные recommended=True
        for i, (cb, fx) in enumerate(zip(self._fx_checkboxes, VISUAL_EFFECTS)):
            cb.set(fx["recommended"])

        # Питание и сон
        is_laptop = app_state.device_type == "Ноутбук"
        self._pwr_cb.set(True)
        self._sleep_cb.set(not is_laptop)

        # Copilot — отключить (рекомендуется)
        self._copilot_cb.set(True)

        # Microsoft 365 Copilot — заблокировать (рекомендуется)
        # self._m365_copilot_cb.set(True)

        # Game Mode — включить (рекомендуется)
        self._game_mode_cb.set(True)

        # Проводник
        self._launch_cb.set(True)        # Этот компьютер
        self._recycle_nav_cb.set(True)   # Корзина в боковой панели
        self._hide_recycle_cb.set(False) # Не скрывать корзину с рабочего стола
        self._kill_task_cb.set(is_end_task_supported())     # Kill task (only if supported)

        self._on_checkbox_toggle()
        self._status_lbl.configure(
            text="⭐ Выбраны рекомендуемые настройки",
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

            # 2. Визуальные эффекты (Требуют перезапуск)
            fx_changed = False
            for cb in self._fx_checkboxes:
                if cb.get() != self._initial_state[cb]:
                    fx_changed = True
                    break
            
            if fx_changed:
                enabled = [i for i, cb in enumerate(self._fx_checkboxes) if cb.get()]
                apply_visual_effects(enabled)
                needs_restart = True

            # 3. Питание (НЕ требуют перезапуск)
            if self._pwr_cb.get() != self._initial_state[self._pwr_cb]:
                if self._pwr_cb.get():
                    # Сохраняем текущую схему перед применением оптимизации
                    app_state.original_power_scheme = get_current_power_scheme_guid()
                    is_laptop = app_state.device_type == "Ноутбук"
                    apply_power_plan(is_laptop)
                else:
                    # Восстанавливаем старую схему
                    if app_state.original_power_scheme:
                        set_power_scheme(app_state.original_power_scheme)
                    else:
                        # Если бэкапа нет (программа только запустилась), ставим Balanced по умолчанию
                        set_power_scheme(POWER_BALANCED)
            
            # Сон и монитор (НЕ требуют перезапуск)
            if self._sleep_cb.get() != self._initial_state[self._sleep_cb]:
                from tweaks import apply_sleep_timeouts
                apply_sleep_timeouts(self._sleep_cb.get())

            # Темная тема (НЕ требует перезапуск)
            if self._dark_mode_cb.get() != self._initial_state[self._dark_mode_cb]:
                from tweaks import apply_dark_mode
                apply_dark_mode(self._dark_mode_cb.get())

            # Game Mode (НЕ требует перезапуск)
            if self._game_mode_cb.get() != self._initial_state[self._game_mode_cb]:
                apply_game_mode(self._game_mode_cb.get())

            # 4. Copilot (Требует перезапуск explorer.exe)
            if self._copilot_cb.get() != self._initial_state[self._copilot_cb]:
                apply_copilot_disable(self._copilot_cb.get())
                # Перезапускаем explorer.exe для немедленного применения изменений
                restart_explorer()
                needs_restart = False  # explorer.exe перезапущен, полная перезагрузка не нужна

            # 4.1. Microsoft 365 Copilot functionality removed

            # 5. Проводник (Требует перезапуск)
            exp_tweaks = [self._launch_cb, self._recycle_nav_cb, self._hide_recycle_cb, self._kill_task_cb]
            explorer_changed = any(cb.get() != self._initial_state[cb] for cb in exp_tweaks)
            print(f"[DEBUG] _apply_worker: explorer_changed={explorer_changed}")
            for cb in exp_tweaks:
                print(f"[DEBUG]   cb={cb._cb.cget('text')[:40]} current={cb.get()} initial={self._initial_state.get(cb)}")
            if explorer_changed:
                apply_explorer_settings(
                    open_to_this_pc=self._launch_cb.get(),
                    recycle_in_nav=self._recycle_nav_cb.get(),
                    hide_recycle_desktop=self._hide_recycle_cb.get(),
                    enable_end_task=self._kill_task_cb.get()
                )
                print("[DEBUG] _apply_worker: calling restart_explorer()")
                restart_explorer()
                print("[DEBUG] _apply_worker: restart_explorer() done")

            self.after(0, lambda: self._on_done(needs_restart, success=True))
        except Exception as e:
            self.after(0, lambda: self._on_done(False, success=False, error=str(e)))

    def _on_done(self, needs_restart: bool, success: bool, error: str = ""):
        self._apply_btn.configure(state="normal", text="✅  Применить выбранное")
        if success:
            self._status_lbl.configure(
                text="✔ Настройки применены", text_color=SUCCESS)
            self._capture_initial_state() # Update state after success
            if needs_restart:
                RestartDialog(self.winfo_toplevel())
        else:
            self._status_lbl.configure(
                text=f"❌ Ошибка: {error}", text_color=DANGER)

    def __del__(self):
        """Cleanup when frame is destroyed."""
        try:
            self.cleanup_callbacks()
        except Exception:
            pass  # Ignore errors during cleanup
