import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Глобальный мок customtkinter
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
        var.get.return_value = True
        return var

sys.modules['customtkinter'] = MockCTkModule()

# Импорт GamingFrame
from gaming import GamingFrame

class TestGamingTab(unittest.TestCase):
    
    def setUp(self):
        # Инициализируем фрейм
        self.frame = GamingFrame(MagicMock())
        # Мокаем статусную метку и after
        self.frame._status_lbl = MagicMock()
        self.frame.after = MagicMock()

    def test_apply_tweaks_status(self):
        """Проверка обновления статуса при применении настроек."""
        self.frame._apply_tweaks()
        # Проверяем, что текст изменился на "Настройки применены"
        self.frame._status_lbl.configure.assert_any_call(text="✅ Настройки применены!", text_color="#4CAF50")
        # Проверяем, что запланирована очистка статуса через 3000мс
        self.frame.after.assert_called_with(3000, unittest.mock.ANY)

    def test_tweak_methods_existence(self):
        """Проверка наличия всех ключевых методов."""
        self.assertTrue(hasattr(self.frame, '_apply_tweaks'))

if __name__ == '__main__':
    unittest.main()
