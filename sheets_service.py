"""

Отвечает за работу с Google Spreadsheet:
- чтение таблицы
- поиск колонок по заголовкам
- обновление значений (Есть / Нет)
"""

import re
import logging

from google_client import get_sheets_service
from retry import with_retry
import config

logger = logging.getLogger("report_checker")


@with_retry()
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


def _column_index(letters):
    """'A' -> 0, 'C' -> 2, 'AA' -> 26 ..."""

    index = 0
    for ch in letters.upper():
        index = index * 26 + (ord(ch) - ord("A") + 1)

    return index - 1


def _sheet_name_and_start_row():
    """
    Parses WORKSHEET_NAME like "Sheet1", "Sheet1!C4" or "Sheet1!C4:F"
    into (sheet_name, start_row, start_col_index).

    start_col_index is 0-based and reflects the first column of the
    range (e.g. "C4" -> 2), so that column letters computed from a
    header index found within the fetched range can be translated
    back into real sheet columns.
    """

    worksheet = config.WORKSHEET_NAME

    if "!" in worksheet:
        sheet_name, range_part = worksheet.split("!", 1)
        match = re.match(r"([A-Za-z]*)(\d+)", range_part)

        if match:
            col_letters = match.group(1)
            start_row = int(match.group(2))
            start_col_index = _column_index(col_letters) if col_letters else 0
        else:
            start_row = 1
            start_col_index = 0
    else:
        sheet_name = worksheet
        start_row = 1
        start_col_index = 0

    return sheet_name, start_row, start_col_index


def _column_letter(index):

    letters = ""
    index += 1

    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters

    return letters


def build_updates(rows, bin_set):

    header = rows[0]
    bin_idx, result_idx = get_column_indexes(header)

    updates = []
    seen_bins = set()
    duplicate_bins = set()

    for i in range(1, len(rows)):
        row = rows[i]

        if len(row) <= bin_idx:
            continue

        bin_value = str(row[bin_idx]).strip()

        if bin_value and bin_value in seen_bins:
            duplicate_bins.add(bin_value)
        if bin_value:
            seen_bins.add(bin_value)

        if bin_value in bin_set:
            value = config.FOUND_TEXT
        else:
            value = config.NOT_FOUND_TEXT

        updates.append({"row_index": i, "value": value})

    if duplicate_bins:
        logger.warning(
            f"Duplicate {config.BIN_COLUMN} values found: {sorted(duplicate_bins)}"
        )

    return updates, result_idx


@with_retry()
def update_sheet(updates, result_idx):

    if not updates:
        return

    sheet_name, start_row, start_col_index = _sheet_name_and_start_row()
    col_letter = _column_letter(start_col_index + result_idx)

    data = []
    for update in updates:
        sheet_row = start_row + update["row_index"]
        data.append({
            "range": f"{sheet_name}!{col_letter}{sheet_row}",
            "values": [[update["value"]]]
        })

    service = get_sheets_service()

    body = {
        "valueInputOption": "RAW",
        "data": data
    }

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=config.GOOGLE_SHEET_ID,
        body=body
    ).execute()


def process_sheet(bin_set):

    rows = get_sheet_data()

    if not rows:
        raise Exception("Sheet is empty")

    if len(rows) <= 1:
        logger.warning("Sheet contains only a header row, no data rows to process")
        return 0

    updates, result_idx = build_updates(rows, bin_set)

    update_sheet(updates, result_idx)

    return len(updates)
