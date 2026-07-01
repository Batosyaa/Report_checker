"""
CONFIGURATION FILE

Изменять только значения ниже.

После изменения ничего больше в проекте менять не нужно.
"""

from pathlib import Path

# PROJECT PATHS

PROJECT_ROOT = Path(__file__).parent

# Google credentials

SERVICE_ACCOUNT_FILE = PROJECT_ROOT / "credentials" / "service_account.json"

# Logs

LOG_FILE = PROJECT_ROOT / "logs" / "report_checker.log"

# GOOGLE DRIVE

# REQUIRED: id of the Drive folder containing the PDF reports
GOOGLE_DRIVE_FOLDER_ID = ""

# GOOGLE SHEETS

# REQUIRED: id of the target Google Spreadsheet
GOOGLE_SHEET_ID = ""

# REQUIRED: worksheet/tab name (and optional range), e.g. "Sheet1" or "Sheet1!A1:Z"
WORKSHEET_NAME = ""

# Название колонки с БИН

BIN_COLUMN = "БИН"

# Название колонки результата

RESULT_COLUMN = "Наличие отчета"

# WHAT TO WRITE

FOUND_TEXT = "Да"

NOT_FOUND_TEXT = "Нет"

# FILE TYPES

VALID_EXTENSIONS = [
    ".pdf"
]