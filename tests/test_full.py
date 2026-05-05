import os
import sys
import threading
import unittest
from unittest.mock import MagicMock, patch

# Добавляем корень проекта в sys.path, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestSystemInfoCollectAll(unittest.TestCase):

    def test_collect_all_returns_expected_payload_and_calls_callback(self):
        """Проверяем, что collect_all формирует словарь со всеми ключами и вызывает callback."""
        import system_info

        expected_payload = {
            "device_type": "Стационарный ПК",
            "os": "Windows 11 (Build 99999)",
            "cpu": "Sample CPU\n  Ядра: 8  |  Потоки: 16",
            "gpu": "Sample GPU (Driver)",
            "motherboard": "Sample Board",
            "ram": "32.0 ГБ  |  Использовано: 10.0 ГБ (31.3%)",
            "disks": [
                {
                    "drive": "C:",
                    "fs": "NTFS",
                    "total": "512.0 ГБ",
                    "free": "200.0 ГБ свободно",
                    "used_pct": 61.0,
                }
            ],
            "battery": {"percent": 88.0, "plugged": True},
        }

        callback_payload = []

        with patch.multiple(
            system_info,
            get_device_type=MagicMock(return_value=expected_payload["device_type"]),
            get_os_info=MagicMock(return_value=expected_payload["os"]),
            get_cpu_info=MagicMock(return_value=expected_payload["cpu"]),
            get_gpu_info=MagicMock(return_value=expected_payload["gpu"]),
            get_motherboard_info=MagicMock(return_value=expected_payload["motherboard"]),
            get_ram_info=MagicMock(return_value=expected_payload["ram"]),
            get_disks_info=MagicMock(return_value=list(expected_payload["disks"])),
            get_battery_info=MagicMock(return_value=dict(expected_payload["battery"])),
        ):
            result = system_info.collect_all(callback_payload.append)

        self.assertEqual(result, expected_payload)
        self.assertEqual(callback_payload, [expected_payload])

    def test_collect_all_async_executes_callback_in_background_thread(self):
        """Убеждаемся, что collect_all_async вызывает callback и возвращает поток."""
        import system_info

        event = threading.Event()
        received = {}

        def fake_collect_all(callback):
            payload = {"os": "async"}
            callback(payload)
            return payload

        with patch("system_info.collect_all", side_effect=lambda cb: fake_collect_all(cb)):
            thread = system_info.collect_all_async(lambda data: (received.update(data), event.set()))

        # Ждем выполнения фонового потока
        event.wait(timeout=2)
        thread.join(timeout=2)

        self.assertTrue(event.is_set(), "Callback из collect_all_async не был вызван")
        self.assertEqual(received, {"os": "async"})


if __name__ == "__main__":
    unittest.main()
