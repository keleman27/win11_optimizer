import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# 1. Добавляем путь к проекту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Создаем расширенный объект-заглушку для customtkinter
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

# Подменяем модуль
sys.modules['customtkinter'] = MockCTkModule()

# 3. Импортируем CleanupFrame (с перезагрузкой)
import importlib
try:
    import cleanup
    importlib.reload(cleanup)
except ImportError:
    import cleanup

from cleanup import CleanupFrame

class TestCleanupTab(unittest.TestCase):
    
    def setUp(self):
        # Патчим _load_autoruns, чтобы не трогать реестр при создании экземпляра
        with patch.object(CleanupFrame, '_load_autoruns', return_value=None):
            self.frame = CleanupFrame(MagicMock())
        
        if not hasattr(self.frame, '_autorun_switches'):
            self.frame._autorun_switches = []

    def test_logic_methods_exist(self):
        """Проверка наличия методов логики."""
        self.assertTrue(hasattr(self.frame, '_disable_third_party_autorun'))
        self.assertTrue(hasattr(self.frame, '_run_cleanup'))

    def test_disable_third_party_autorun(self):
        """Проверка логики отключения сторонней автозагрузки."""
        sw1 = MagicMock()
        sw2 = MagicMock()
        self.frame._autorun_switches = [sw1, sw2]
        
        self.frame._disable_third_party_autorun()
        
        sw1.deselect.assert_called_once()
        sw2.deselect.assert_called_once()

if __name__ == '__main__':
    unittest.main()
