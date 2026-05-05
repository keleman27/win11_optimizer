"""state.py — Общее состояние приложения (device_type и т.д.)."""


class AppState:
    def __init__(self):
        self.device_type: str = "Стационарный ПК"
        self.original_power_scheme: str = ""
        self._listeners: list = []

    def set_device_type(self, dtype: str):
        self.device_type = dtype
        for fn in self._listeners:
            try:
                fn(dtype)
            except Exception:
                pass

    def on_device_type_change(self, fn):
        """Регистрирует callback, вызываемый при смене типа устройства."""
        self._listeners.append(fn)


# Глобальный синглтон
app_state = AppState()
