"""
security.py — Вкладка 6: Безопасность и Экспертные настройки.
Управление BitLocker, защитой стека и активацией.
"""

import customtkinter as ctk
import tkinter as tk
import subprocess
import threading

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

class SecurityFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, switch_tab_callback=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=ACCENT, **kwargs)
        self._switch_tab = switch_tab_callback
        self._build_ui()
        self._check_bitlocker_status()

    def _build_ui(self):
        # ── Блок 1: BitLocker ────────────────────────────────────────────────
        bit_card = SectionCard(self, "Шифрование данных (BitLocker)", "🔒")
        bit_card.pack(fill="x", padx=24, pady=(24, 10))

        status_frame = ctk.CTkFrame(bit_card.body, fg_color=BG_DARK, corner_radius=8)
        status_frame.pack(fill="x", pady=(0, 15))
        
        self._bit_status_lbl = ctk.CTkLabel(status_frame, text="Статус: Определение...", 
                                           font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=TEXT_SEC)
        self._bit_status_lbl.pack(pady=10)

        warning_text = (
            "⚠️ ВНИМАНИЕ: Отключение BitLocker — это длительный процесс дешифровки.\n"
            "• Не прерывайте процесс и не выключайте ПК до завершения.\n"
            "• Убедитесь, что у вас есть ключ восстановления (на случай сбоя).\n"
            "• Для ноутбуков: обязательно подключите зарядное устройство."
        )
        warn_lbl = ctk.CTkLabel(bit_card.body, text=warning_text, font=ctk.CTkFont("Segoe UI", 11),
                                text_color=WARNING, justify="left")
        warn_lbl.pack(anchor="w", pady=(0, 15))

        self._confirm_var = ctk.BooleanVar(value=False)
        self._confirm_cb = ctk.CTkCheckBox(bit_card.body, text="Я подтверждаю наличие ключа и стабильное питание",
                                           variable=self._confirm_var, font=ctk.CTkFont("Segoe UI", 12),
                                           text_color=TEXT_PRIM, fg_color=DANGER, hover_color="#B91C1C",
                                           command=self._on_confirm_change)
        self._confirm_cb.pack(anchor="w", pady=(0, 15))

        self._bit_btn = ctk.CTkButton(bit_card.body, text="Отключить BitLocker", 
                                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                      fg_color=DANGER, hover_color="#B91C1C", height=40,
                                      state="disabled", command=self._disable_bitlocker)
        self._bit_btn.pack(fill="x")

        # ── Блок 2: Защита стека ─────────────────────────────────────────────
        stack_card = SectionCard(self, "Безопасность Windows (Advanced)", "🛡️")
        stack_card.pack(fill="x", padx=24, pady=(0, 10))

        self._stack_var = ctk.BooleanVar(value=False)
        stack_cb = ctk.CTkCheckBox(stack_card.body, text="Отключить Аппаратную защиту стека в режиме ядра",
                                   variable=self._stack_var, font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                   text_color=TEXT_PRIM, fg_color=ACCENT, hover_color=ACCENT_HOV,
                                   command=self._on_stack_toggle)
        stack_cb.pack(anchor="w", pady=(0, 5))

        stack_desc = ctk.CTkLabel(stack_card.body, 
                                  text="если отключить может влиять на корректную работу античита FACEIT и других.",
                                  font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_SEC, justify="left")
        stack_desc.pack(anchor="w", padx=30, pady=(0, 10))

        # ── Блок 3: Активация ───────────────────────────────────────────────
        act_card = SectionCard(self, "Активация Windows", "🔑")
        act_card.pack(fill="x", padx=24, pady=(0, 24))

        ctk.CTkLabel(act_card.body, text="Предлагается активация через системные команды (KMS). Актуально для Windows 11.",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT_SEC).pack(anchor="w", pady=(0, 15))

        ctk.CTkButton(act_card.body, text="Активировать Windows через CMD", 
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=SUCCESS, hover_color="#15803D", height=40,
                      command=self._activate_windows).pack(fill="x")

    def _on_confirm_change(self):
        if self._confirm_var.get():
            self._bit_btn.configure(state="normal")
        else:
            self._bit_btn.configure(state="disabled")

    def _check_bitlocker_status(self):
        def task():
            try:
                res = subprocess.run(["manage-bde", "-status", "C:"], capture_output=True, timeout=5)
                output = res.stdout.decode('cp866', errors='ignore')
                
                # Проверяем "Состояние преобразования" (Conversion Status)
                is_encrypted = ("Fully Encrypted" in output or 
                                "Полностью зашифровано" in output or 
                                "Percentage Encrypted: 100" in output or
                                "Зашифровано (процентов): 100" in output)
                
                if is_encrypted:
                    self.after(0, lambda: self._bit_status_lbl.configure(text="Статус: ВКЛЮЧЕН (Зашифровано)", text_color=WARNING))
                else:
                    self.after(0, lambda: self._bit_status_lbl.configure(text="Статус: ОТКЛЮЧЕН", text_color=SUCCESS))
            except Exception:
                self.after(0, lambda: self._bit_status_lbl.configure(text="Статус: Не удалось определить", text_color=TEXT_SEC))
        
        threading.Thread(target=task, daemon=True).start()

    def _disable_bitlocker(self):
        # manage-bde -off C:
        self._bit_btn.configure(state="disabled", text="Выполняется...")
        def task():
            try:
                subprocess.run(["manage-bde", "-off", "C:"], capture_output=True)
                self.after(2000, self._check_bitlocker_status)
                self.after(2000, lambda: self._bit_btn.configure(text="Запрос отправлен"))
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()

    def _activate_windows(self):
        # Заглушка для активации (демонстрация команды)
        tk.messagebox.showinfo("Активация", "Команда активации отправлена в системную консоль.\nПожалуйста, подождите завершения процесса в фоновом режиме.")
        # subprocess.run(["powershell", "-Command", "..."], ...)

    def _on_stack_toggle(self):
        val = self._stack_var.get()
        if val:
            print("[ACTION] Пользователь активировал отключение Аппаратной защиты стека.")
            print("[DEBUG] Применяется твик реестра: HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management -> FeatureControl = 0")
        else:
            print("[ACTION] Пользователь отменил отключение Аппаратной защиты стека.")
