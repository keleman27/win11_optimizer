import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Глобальный мок customtkinter (аналогично cleanup)
class MockCTkModule:
    class BaseWidget:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def grid(self, *args, **kwargs): pass
        def place(self, *args, **kwargs): pass
        def configure(self, *args, **kwargs): pass
        def bind(self, *args, **kwargs): pass
        def winfo_rootx(self): return 0
        def winfo_rooty(self): return 0

    class CTkScrollableFrame(BaseWidget): pass
    class CTkFrame(BaseWidget): pass
    class CTkLabel(BaseWidget): pass
    class CTkButton(BaseWidget): pass
    class CTkCheckBox(BaseWidget): pass
    class CTkSwitch(BaseWidget):
        def select(self): pass
        def deselect(self): pass
    
    def CTkFont(self, *args, **kwargs): return MagicMock()
    def BooleanVar(self, *args, **kwargs): 
        var = MagicMock()
        var.get.return_value = False
        return var

sys.modules['customtkinter'] = MockCTkModule()

# Импорт SecurityFrame
from security import SecurityFrame

class TestSecurityTab(unittest.TestCase):
    
    def setUp(self):
        # Мокаем _check_bitlocker_status, так как он запускает поток
        with patch.object(SecurityFrame, '_check_bitlocker_status', return_value=None):
            self.frame = SecurityFrame(MagicMock())
        
        # Мокаем кнопки и переменные
        self.frame._bit_btn = MagicMock()
        self.frame._confirm_var = MagicMock()

    def test_bitlocker_confirm_logic(self):
        """Проверка активации кнопки BitLocker при подтверждении."""
        # Случай 1: подтверждение не установлено
        self.frame._confirm_var.get.return_value = False
        self.frame._on_confirm_change()
        self.frame._bit_btn.configure.assert_called_with(state="disabled")
        
        # Случай 2: подтверждение установлено
        self.frame._confirm_var.get.return_value = True
        self.frame._on_confirm_change()
        self.frame._bit_btn.configure.assert_called_with(state="normal")

    def test_activate_windows_call(self):
        """Проверка вызова метода активации."""
        self.assertTrue(hasattr(self.frame, '_activate_windows'))
        # Вызов не должен падать (там messagebox.showinfo)
        with patch('tkinter.messagebox.showinfo'):
            self.frame._activate_windows()

if __name__ == '__main__':
    unittest.main()
