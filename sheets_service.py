"""

Отвечает за работу с Google Spreadsheet:
- чтение таблицы
- поиск колонок по заголовкам
- обновление значений (Да / Нет)
"""

import re
import logging

from googleapiclient.errors import HttpError

from google_client import get_sheets_service
from retry import with_retry
import config

logger = logging.getLogger("report_checker")


def _column_index(letters):
    """'A' -> 0, 'C' -> 2, 'AA' -> 26 ..."""

    index = 0
    for ch in letters.upper():
        index = index * 26 + (ord(ch) - ord("A") + 1)

    return index - 1


def _column_letter(index):

    letters = ""
    index += 1

    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters

    return letters


def _parse_worksheet_name():
    """
    Parses WORKSHEET_NAME (e.g. "Sheet1", "Sheet1!C4", "Sheet1!C4:F")
    into (sheet_name, start_row, start_col_index, end_col_index).

    start_row / start_col_index describe where the header actually
    lives on the sheet (1-based row, 0-based column). end_col_index
    is None when no explicit end column was given.

    This is purely local bookkeeping — it is NOT sent to the Sheets
    API as-is, since the API rejects mixed cell/column notation like
    "C4:F" (only same-column open ranges like "A5:A" are valid A1
    notation). See _fetch_range().
    """

    worksheet = config.WORKSHEET_NAME

    if "!" not in worksheet:
        return worksheet, 1, 0, None

    sheet_name, range_part = worksheet.split("!", 1)
    tokens = range_part.split(":")

    start_match = re.match(r"([A-Za-z]*)(\d*)", tokens[0])
    start_col_letters = start_match.group(1)
    start_row = int(start_match.group(2)) if start_match.group(2) else 1
    start_col_index = _column_index(start_col_letters) if start_col_letters else 0

    end_col_index = None
    if len(tokens) > 1:
        end_match = re.match(r"([A-Za-z]*)(\d*)", tokens[1])
        end_col_letters = end_match.group(1)
        if end_col_letters:
            end_col_index = _column_index(end_col_letters)

    return sheet_name, start_row, start_col_index, end_col_index


def _fetch_range():
    """
    Builds a range string that is guaranteed to be valid A1 notation
    for the Sheets API `values().get()` call: always full columns
    from row 1, never a mixed "C4:F" style range. The configured
    start row is applied locally once the data comes back, so this
    is also robust to the sheet growing beyond whatever row count
    someone guessed.
    """

    if "!" not in config.WORKSHEET_NAME:
        return config.WORKSHEET_NAME  # no range given -> whole sheet, already valid

    sheet_name, _start_row, start_col_index, end_col_index = _parse_worksheet_name()

    if end_col_index is None:
        end_col_index = start_col_index

    start_letter = _column_letter(start_col_index)
    end_letter = _column_letter(end_col_index)

    return f"{sheet_name}!{start_letter}:{end_letter}"


def _list_sheet_titles(service):
    """Best-effort lookup of the spreadsheet's real tab names, used to
    give a helpful hint when the configured sheet name doesn't resolve."""

    try:
        meta = service.spreadsheets().get(
            spreadsheetId=config.GOOGLE_SHEET_ID,
            fields="sheets.properties.title"
        ).execute()
        return [s["properties"]["title"] for s in meta.get("sheets", [])]
    except Exception:
        return []


@with_retry()
def get_sheet_data():

    service = get_sheets_service()
    fetch_range = _fetch_range()

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=config.GOOGLE_SHEET_ID,
            range=fetch_range
        ).execute()
    except HttpError as e:
        status = e.resp.status if e.resp is not None else None
        if status == 400:
            titles = _list_sheet_titles(service)
            hint = (
                f" Actual tab name(s) in this spreadsheet: {titles}."
                if titles else ""
            )
            raise Exception(
                f"Google Sheets rejected the range '{fetch_range}'. This usually means "
                f"the sheet/tab name in WORKSHEET_NAME (.env) doesn't match exactly "
                f"(it's case-sensitive).{hint} Update WORKSHEET_NAME accordingly, "
                f"e.g. WORKSHEET_NAME=<real tab name>!C4:F"
            ) from e
        raise

    return result.get("values", [])


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


def build_updates(rows, bin_set, header_row_index=0):
    """
    row_index in the returned updates is absolute within `rows`
    (0-based, where rows[0] is sheet row 1) — not relative to the
    header. update_sheet() turns it into a real sheet row with a
    plain +1.
    """

    header = rows[header_row_index]
    bin_idx, result_idx = get_column_indexes(header)

    updates = []
    seen_bins = set()
    duplicate_bins = set()

    for i in range(header_row_index + 1, len(rows)):
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

    sheet_name, _start_row, start_col_index, _end_col_index = _parse_worksheet_name()
    col_letter = _column_letter(start_col_index + result_idx)

    data = []
    for update in updates:
        sheet_row = update["row_index"] + 1  # rows[] is 0-based from sheet row 1
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

    _sheet_name, start_row, _start_col_index, _end_col_index = _parse_worksheet_name()
    header_row_index = start_row - 1

    rows = get_sheet_data()

    if not rows or len(rows) <= header_row_index:
        raise Exception(
            "Header row not found — check the row number in WORKSHEET_NAME (.env)"
        )

    if len(rows) <= header_row_index + 1:
        logger.warning("Sheet contains only a header row, no data rows to process")
        return 0

    updates, result_idx = build_updates(rows, bin_set, header_row_index)

    update_sheet(updates, result_idx)

    return len(updates)
