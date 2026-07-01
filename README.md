# Report Checker (Google Drive + Google Sheets)

## Описание

Этот инструмент автоматически проверяет наличие PDF-отчётов в папке Google Drive и обновляет Google Таблицу (Google Sheets), отмечая наличие или отсутствие документа по каждому БИН.

Решение рассчитано на использование в продакшн-среде как внутренний автоматизированный сервис.

---

## Как работает система

1. Подключается к Google Drive через Service Account
2. Получает список PDF-файлов из указанной папки
3. Извлекает БИН из названий файлов
4. Подключается к Google Sheets
5. Считывает таблицу
6. Сравнивает БИНы из таблицы с файлами в Drive
7. Обновляет колонку результата:
   - "Есть" — документ найден
   - "Нет" — документа нет
8. Записывает логи выполнения

---

## Структура проекта

```
report_checker/

├── main.py                 # Точка входа
├── config.py               # Конфигурация
├── logger.py               # Логирование
├── google_client.py        # Авторизация Google API
├── drive_service.py        # Работа с Google Drive
├── sheets_service.py       # Работа с Google Sheets

├── requirements.txt
├── README.md

├── credentials/
│   └── service_account.json

├── logs/
│   └── report_checker.log

└── output/                 # (опционально, для будущих версий)
```

---

## Требования

- Python 3.9+
- Google Cloud проект с включёнными API:
  - Google Drive API
  - Google Sheets API
- Service Account JSON ключ

---

## Установка

```bash
pip install -r requirements.txt
```

---

## Настройка

Все основные настройки находятся в файле `config.py`.

### Обязательно заполнить:

#### ID папки Google Drive
```python
GOOGLE_DRIVE_FOLDER_ID = "your_folder_id"
```

#### ID Google Таблицы
```python
GOOGLE_SHEET_ID = "your_spreadsheet_id"
WORKSHEET_NAME = "Sheet1"
```

#### Названия колонок
В таблице должны быть заголовки:

- колонка БИН (например: `БИН`)
- колонка результата (например: `Наличие отчета`)

И в конфиге:

```python
BIN_COLUMN = "БИН"
RESULT_COLUMN = "Наличие отчета"
```

---

## Настройка Google (ВАЖНО)

### 1. Создать Service Account

- Открыть Google Cloud Console
- Создать Service Account
- Скачать JSON ключ
- Поместить файл сюда:

```
credentials/service_account.json
```

---

### 2. Выдать доступ

Нужно вручную выдать доступ сервисному аккаунту:

#### Google Drive папка:
Поделиться папкой с email сервисного аккаунта

#### Google Sheets:
Также открыть доступ для этого же email

---

## Запуск

```bash
python main.py
```

---

## Результат

Таблица будет обновлена:

| БИН           | Наличие отчета |
|---------------|----------------|
| 123456789012  | Есть           |
| 987654321000  | Нет            |

---

## Логирование

Логи сохраняются в:

```
logs/report_checker.log
```

Пример:

```
2026-07-01 12:00:00 | INFO | PDF BINs found: 245
2026-07-01 12:00:01 | INFO | Rows processed: 327
2026-07-01 12:00:02 | INFO | Execution time: 2.41 sec
2026-07-01 12:00:02 | INFO | Status: SUCCESS
```

---

## Производительность

- Используется batch update (одним запросом)
- Поиск БИНов через set (O(1))
- Подходит для 10k–100k строк

---

## Частые проблемы

### 1. Нет доступа
→ Проверь, что service account добавлен в доступ к Drive и Sheets

### 2. Ошибка колонок
→ Проверь названия в `config.py`

### 3. Пустая таблица
→ Первая строка должна быть заголовками

---

## Важно

- Не использовать личный Google аккаунт
- Всегда использовать Service Account
- Не менять структуру таблицы без обновления config.py

---

## Автор

Внутренний инструмент автоматизации проверки отчётов (Google Drive + Google Sheets)