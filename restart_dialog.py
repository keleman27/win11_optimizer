"""
restart_dialog.py — Диалог предложения перезагрузки после применения твиков.
"""

import customtkinter as ctk
import threading
from tweaks import restart_explorer, restart_pc

from theme import (
    ACCENT, ACCENT_HOV, BG_DARK, BORDER, TEXT_PRIM, TEXT_SEC
)


class RestartDialog(ctk.CTkToplevel):
    """
    Модальный диалог: предлагает перезапустить explorer.exe или ПК целиком.
    """

    def __init__(self, parent, needs_reboot: bool = False):
        super().__init__(parent)
        self.title("Применить изменения")
        
        # Размеры и настройки
        self.geometry("480x320")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        
        # Модальность и фокус
        self.transient(parent)
        self.grab_set()
        
        self._needs_reboot = needs_reboot
        
        # Сначала строим UI
        self._build()
        
        # Потом центрируем и показываем
        self.withdraw() # Скрываем на время позиционирования
        self.after(100, self._show_and_center)

    def _show_and_center(self):
        """Центрирует окно относительно родителя и показывает его."""
        self.update_idletasks()
        if self.master:
            mx = self.master.winfo_rootx()
            my = self.master.winfo_rooty()
            mw = self.master.winfo_width()
            mh = self.master.winfo_height()
            
            x = mx + (mw // 2) - (self.winfo_width() // 2)
            y = my + (mh // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")
        
        self.deiconify() # Показываем
        self.focus_force()

    def _build(self):
        pad = {"padx": 30}

        # Контейнер для отступа сверху
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, pady=20)

        # Заголовок
        ctk.CTkLabel(main_frame, text="🔄  Настройки применены",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=TEXT_PRIM).pack(pady=(10, 8), **pad)

        msg = ("Для вступления изменений в силу рекомендуется перезапустить "
               "Проводник или перезагрузить компьютер.")
        ctk.CTkLabel(main_frame, text=msg,
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=TEXT_SEC, wraplength=400, justify="center"
                     ).pack(pady=(0, 25), **pad)

        # Кнопки
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", **pad)

        ctk.CTkButton(
            btn_frame, text="⟳  Перезапустить Проводник",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOV,
            height=44, corner_radius=10,
            command=self._do_explorer
        ).pack(fill="x", pady=(0, 10))

        reboot_color = "#D97706" if self._needs_reboot else "#2D2D33"
        ctk.CTkButton(
            btn_frame, text="🖥️  Перезагрузить систему",
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=reboot_color, hover_color="#92400E" if self._needs_reboot else "#3F3F46",
            height=44, corner_radius=10,
            command=self._do_reboot
        ).pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="Сделаю это позже",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color="#1E1E22",
            border_width=1, border_color=BORDER,
            height=38, corner_radius=10,
            text_color=TEXT_SEC,
            command=self.destroy
        ).pack(fill="x")

    def _do_explorer(self):
        self.destroy()
        # Перезапуск в отдельном потоке, чтобы не вешать UI
        threading.Thread(target=restart_explorer, daemon=True).start()

    def _do_reboot(self):
        self.destroy()
        threading.Thread(target=restart_pc, daemon=True).start()
