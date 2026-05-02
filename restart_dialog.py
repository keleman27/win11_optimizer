"""
restart_dialog.py — Диалог предложения перезагрузки после применения твиков.
"""

import customtkinter as ctk
import threading
from tweaks import restart_explorer, restart_pc

ACCENT     = "#4F8EF7"
ACCENT_HOV = "#3A75E0"
BG_CARD    = "#1E2130"
BG_DARK    = "#161824"
BORDER     = "#2D3354"
TEXT_PRIM  = "#EAEEF8"
TEXT_SEC   = "#8B9BB4"
WARNING    = "#FF9800"
SUCCESS    = "#4CAF50"


class RestartDialog(ctk.CTkToplevel):
    """
    Модальный диалог: предлагает перезапустить explorer.exe или ПК целиком.
    Появляется после применения твиков проводника / системы.
    """

    def __init__(self, parent, needs_reboot: bool = False):
        super().__init__(parent)
        self.title("Применить изменения")
        self.geometry("480x300")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self.grab_set()          # модальность
        self.focus_force()
        self.lift()

        # Центрирование относительно родителя
        self.after(10, self._center)

        self._needs_reboot = needs_reboot
        self._build()

    def _center(self):
        self.update_idletasks()
        pw = self.master.winfo_rootx() + self.master.winfo_width() // 2
        ph = self.master.winfo_rooty() + self.master.winfo_height() // 2
        x = pw - self.winfo_width() // 2
        y = ph - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        pad = {"padx": 28, "pady": 0}

        # Иконка + заголовок
        ctk.CTkLabel(self, text="🔄  Настройки применены",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=TEXT_PRIM).pack(pady=(28, 6), **pad)

        msg = ("Для вступления изменений в силу необходимо перезапустить "
               "Проводник Windows или перезагрузить компьютер.")
        ctk.CTkLabel(self, text=msg,
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=TEXT_SEC, wraplength=420, justify="center"
                     ).pack(pady=(0, 24), **pad)

        # Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=28)

        ctk.CTkButton(
            btn_frame, text="⟳  Перезапустить Explorer",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOV,
            height=42, corner_radius=10,
            command=self._do_explorer
        ).pack(fill="x", pady=(0, 8))

        reboot_color = "#D97706" if self._needs_reboot else "#374151"
        ctk.CTkButton(
            btn_frame, text="🖥️  Перезагрузить ПК (через 10 сек)",
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=reboot_color, hover_color="#92400E",
            height=42, corner_radius=10,
            command=self._do_reboot
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Позже",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="transparent", hover_color="#1E2130",
            border_width=1, border_color=BORDER,
            height=36, corner_radius=10,
            text_color=TEXT_SEC,
            command=self.destroy
        ).pack(fill="x")

    def _do_explorer(self):
        self.destroy()
        threading.Thread(target=restart_explorer, daemon=True).start()

    def _do_reboot(self):
        self.destroy()
        threading.Thread(target=restart_pc, daemon=True).start()
