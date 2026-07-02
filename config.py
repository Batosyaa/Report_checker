"""
CONFIGURATION FILE

Значения читаются из переменных окружения (.env файл в корне проекта).
Скопируйте .env.example в .env и заполните своими значениями —
сам .env в git не попадает (см. .gitignore).

После настройки .env ничего больше в проекте менять не нужно.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# PROJECT PATHS

PROJECT_ROOT = Path(__file__).parent

load_dotenv(PROJECT_ROOT / ".env")


def _env(name, default=""):
    return os.getenv(name, default)


# Google credentials

SERVICE_ACCOUNT_FILE = Path(
    _env("SERVICE_ACCOUNT_FILE", str(PROJECT_ROOT / "credentials" / "service_account.json"))
)

# Logs

LOG_FILE = PROJECT_ROOT / "logs" / "report_checker.log"

# GOOGLE DRIVE

# REQUIRED: id of the Drive folder containing the PDF reports
GOOGLE_DRIVE_FOLDER_ID = _env("GOOGLE_DRIVE_FOLDER_ID")

# GOOGLE SHEETS

# REQUIRED: id of the target Google Spreadsheet
GOOGLE_SHEET_ID = _env("GOOGLE_SHEET_ID")

# REQUIRED: worksheet/tab name and optional range, e.g.
#   "Sheet1"            -> header assumed in row 1, columns start at A
#   "Sheet1!C4:F"        -> header in row 4, columns start at C
WORKSHEET_NAME = _env("WORKSHEET_NAME")

# Название колонки с БИН

BIN_COLUMN = _env("BIN_COLUMN", "БИН")

# Название колонки результата

RESULT_COLUMN = _env("RESULT_COLUMN", "Наличие отчета")

# WHAT TO WRITE

FOUND_TEXT = _env("FOUND_TEXT", "Да")

NOT_FOUND_TEXT = _env("NOT_FOUND_TEXT", "Нет")

# FILE TYPES

VALID_EXTENSIONS = [
    ".pdf"
]
