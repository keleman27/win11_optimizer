# Win11 Optimizer

Утилита оптимизации Windows 11 на Python + CustomTkinter.

## Структура проекта

```
win11_optimizer/
├── main.py          # Точка входа, Main GUI (Sidebar + контентная зона)
├── dashboard.py     # Вкладка 1: Дашборд (Паспорт системы)
├── system_info.py   # Модуль сбора системной информации
└── README.md
```

## Запуск

```powershell
cd c:\Users\kiril\Music\win11_optimizer
python main.py
```

## Зависимости

```
customtkinter
psutil
wmi
pywin32
```

Установка: `python -m pip install customtkinter psutil wmi`
