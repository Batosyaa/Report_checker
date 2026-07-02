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
   - "Да" — документ найден
   - "Нет" — документа нет
8. Записывает логи выполнения

---

## Структура проекта

```
report_checker/

├── main.py                 # Точка входа
├── config.py               # Конфигурация (читает .env)
├── logger.py               # Логирование
├── google_client.py        # Авторизация Google API
├── drive_service.py        # Работа с Google Drive
├── sheets_service.py       # Работа с Google Sheets

├── requirements.txt
├── README.md

├── .env.example             # Шаблон конфигурации, безопасно коммитить
├── .env                      # Реальные значения, В GIT НЕ ПОПАДАЕТ

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

## Настройка (.env)

Все настройки читаются из переменных окружения через файл `.env`
в корне проекта. Он в `.gitignore` — реальные ID никогда не попадут в git.

```bash
cp .env.example .env
```

Затем заполните `.env`:

```bash
SERVICE_ACCOUNT_FILE=credentials/service_account.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
GOOGLE_SHEET_ID=your_spreadsheet_id
WORKSHEET_NAME=Sheet1!C4:F
BIN_COLUMN=БИН
RESULT_COLUMN=Наличие отчета
FOUND_TEXT=Да
NOT_FOUND_TEXT=Нет
```

### ID папки Google Drive

Из URL папки: `drive.google.com/drive/folders/<ЭТО>`

### ID Google Таблицы

Из URL таблицы: `docs.google.com/spreadsheets/d/<ЭТО>/edit`

### WORKSHEET_NAME — имя листа и диапазон

- `"Sheet1"` — заголовки предполагаются в строке 1, колонки с A
- `"Sheet1!C4:F"` — заголовки в строке 4, колонки начиная с C
  (например когда БИН находится в C4, а результат — в F4)

Скрипт сам вычисляет реальную колонку для записи результата на основе
начальной колонки диапазона — колонки указывать вручную больше нигде не нужно.

### Названия колонок

В таблице должны быть заголовки, совпадающие с `BIN_COLUMN` и `RESULT_COLUMN`
из `.env` (по умолчанию — `БИН` и `Наличие отчета`).

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

(путь можно изменить через `SERVICE_ACCOUNT_FILE` в `.env`)

---

### 2. Выдать доступ

Нужно вручную выдать доступ сервисному аккаунту (email вида
`...@...iam.gserviceaccount.com`, указан в JSON-ключе как `client_email`):

#### Google Drive папка:
Поделиться папкой с email сервисного аккаунта (доступ Viewer)

#### Google Sheets:
Также открыть доступ для этого же email (доступ Editor)

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
| 123456789012  | Да             |
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

## Тесты

```bash
python -m unittest discover -s tests -v
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
→ Проверь названия в `.env` (`BIN_COLUMN`, `RESULT_COLUMN`)

### 3. Пустая таблица
→ Первая строка диапазона должна быть заголовками

### 4. .env не подхватывается
→ Убедись, что файл называется именно `.env` и лежит в корне проекта
  (рядом с `config.py`), а не `.env.txt` или в другой папке

---

## Важно

- Не использовать личный Google аккаунт
- Всегда использовать Service Account
- Не менять структуру таблицы без обновления `.env`
- Не коммитить `.env` и `credentials/` — они уже в `.gitignore`

---

## Автор

Внутренний инструмент автоматизации проверки отчётов (Google Drive + Google Sheets)
