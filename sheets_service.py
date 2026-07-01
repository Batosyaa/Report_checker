"""

Отвечает за работу с Google Spreadsheet:
- чтение таблицы
- поиск колонок по заголовкам
- обновление значений (Есть / Нет)
"""

from google_client import get_sheets_service
import config

def get_sheet_data():

    service = get_sheets_service()

    result = service.spreadsheets().values().get(
        spreadsheetId=config.GOOGLE_SHEET_ID,
        range=config.WORKSHEET_NAME
    ).execute()

    values = result.get("values", [])

    return values

def get_column_indexes(header_row):

    try:
        bin_index = header_row.index(config.BIN_COLUMN)
    except ValueError:
        raise Exception(f"Column not found: {config.BIN_COLUMN}")

    try:
        result_index = header_row.index(config.RESULT_COLUMN)
    except ValueError:
        raise Exception(f"Column not found: {config.RESULT_COLUMN}")

    return bin_index, result_index

def build_updates(rows, bin_set):

    header = rows[0]
    bin_idx, result_idx = get_column_indexes(header)

    updates = []

    for i in range(1, len(rows)):
        row = rows[i]

        if len(row) <= bin_idx:
            continue

        bin_value = str(row[bin_idx]).strip()

        if bin_value in bin_set:
            value = config.FOUND_TEXT
        else:
            value = config.NOT_FOUND_TEXT

        while len(row) <= result_idx:
            row.append("")

        row[result_idx] = value

        updates.append(row)

    return rows

def update_sheet(values):

    service = get_sheets_service()

    body = {
        "values": values
    }

    service.spreadsheets().values().update(
        spreadsheetId=config.GOOGLE_SHEET_ID,
        range=config.WORKSHEET_NAME,
        valueInputOption="RAW",
        body=body
    ).execute()
    
def process_sheet(bin_set):

    rows = get_sheet_data()

    if not rows:
        raise Exception("Sheet is empty")

    updated_rows = build_updates(rows, bin_set)

    update_sheet(updated_rows)

    return len(rows) - 1