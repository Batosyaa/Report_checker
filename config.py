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

# Excel

INPUT_EXCEL_FILE = PROJECT_ROOT / "reports" / "report.xlsx"

OUTPUT_EXCEL_FILE = PROJECT_ROOT / "output" / "report_checked.xlsx"

# Logs

LOG_FILE = PROJECT_ROOT / "logs" / "report_checker.log"

# GOOGLE DRIVE

GOOGLE_DRIVE_FOLDER_ID = ""

# EXCEL

EXCEL_SHEET_NAME = None

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