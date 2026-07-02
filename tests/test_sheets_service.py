import unittest
from unittest.mock import patch, MagicMock

import config
from sheets_service import (
    get_column_indexes,
    build_updates,
    update_sheet,
    get_sheet_data,
    _column_letter,
    _column_index,
    _parse_worksheet_name,
    _fetch_range,
)


class TestGetColumnIndexes(unittest.TestCase):

    def test_finds_both_columns(self):
        header = ["Name", config.BIN_COLUMN, config.RESULT_COLUMN]
        bin_idx, result_idx = get_column_indexes(header)
        self.assertEqual(bin_idx, 1)
        self.assertEqual(result_idx, 2)

    def test_missing_bin_column_raises(self):
        header = ["Name", config.RESULT_COLUMN]
        with self.assertRaises(Exception):
            get_column_indexes(header)

    def test_missing_result_column_raises(self):
        header = ["Name", config.BIN_COLUMN]
        with self.assertRaises(Exception):
            get_column_indexes(header)


class TestBuildUpdates(unittest.TestCase):

    def test_marks_found_and_not_found(self):
        rows = [
            ["Name", config.BIN_COLUMN, config.RESULT_COLUMN],
            ["Alpha", "111", ""],
            ["Beta", "222", ""],
        ]
        bin_set = {"111"}

        updates, result_idx = build_updates(rows, bin_set)

        self.assertEqual(result_idx, 2)
        self.assertEqual(
            {(u["row_index"], u["value"]) for u in updates},
            {(1, config.FOUND_TEXT), (2, config.NOT_FOUND_TEXT)},
        )

    def test_skips_rows_shorter_than_bin_column(self):
        rows = [
            ["Name", config.BIN_COLUMN, config.RESULT_COLUMN],
            ["Alpha"],
        ]
        updates, _ = build_updates(rows, set())
        self.assertEqual(updates, [])

    def test_logs_warning_on_duplicate_bins(self):
        rows = [
            ["Name", config.BIN_COLUMN, config.RESULT_COLUMN],
            ["Alpha", "111", ""],
            ["Beta", "111", ""],
        ]

        with self.assertLogs("report_checker", level="WARNING") as cm:
            build_updates(rows, set())

        self.assertTrue(any("111" in message for message in cm.output))

    def test_empty_bin_values_not_flagged_as_duplicates(self):
        rows = [
            ["Name", config.BIN_COLUMN, config.RESULT_COLUMN],
            ["Alpha", "", ""],
            ["Beta", "", ""],
        ]

        updates, _ = build_updates(rows, set())

        self.assertEqual(len(updates), 2)
        self.assertTrue(all(u["value"] == config.NOT_FOUND_TEXT for u in updates))

    def test_header_row_index_offset(self):
        # header not at rows[0] -- e.g. sheet has 3 title rows before it
        rows = [
            ["some title row"],
            [],
            [],
            ["Name", config.BIN_COLUMN, config.RESULT_COLUMN],  # index 3
            ["Alpha", "111", ""],
            ["Beta", "222", ""],
        ]
        bin_set = {"111"}

        updates, result_idx = build_updates(rows, bin_set, header_row_index=3)

        self.assertEqual(result_idx, 2)
        self.assertEqual(
            {(u["row_index"], u["value"]) for u in updates},
            {(4, config.FOUND_TEXT), (5, config.NOT_FOUND_TEXT)},
        )


class TestColumnLetter(unittest.TestCase):

    def test_single_letter_columns(self):
        self.assertEqual(_column_letter(0), "A")
        self.assertEqual(_column_letter(25), "Z")

    def test_double_letter_columns(self):
        self.assertEqual(_column_letter(26), "AA")
        self.assertEqual(_column_letter(51), "AZ")
        self.assertEqual(_column_letter(52), "BA")
        self.assertEqual(_column_letter(701), "ZZ")


class TestColumnIndex(unittest.TestCase):

    def test_roundtrips_with_column_letter(self):
        for letters in ["A", "C", "F", "Z", "AA", "AZ", "BA", "ZZ"]:
            self.assertEqual(_column_letter(_column_index(letters)), letters)

    def test_known_values(self):
        self.assertEqual(_column_index("A"), 0)
        self.assertEqual(_column_index("C"), 2)
        self.assertEqual(_column_index("F"), 5)


class TestParseWorksheetName(unittest.TestCase):

    def setUp(self):
        self._original_worksheet_name = config.WORKSHEET_NAME

    def tearDown(self):
        config.WORKSHEET_NAME = self._original_worksheet_name

    def test_plain_sheet_name_defaults_to_row_one_col_a(self):
        config.WORKSHEET_NAME = "Sheet1"
        self.assertEqual(_parse_worksheet_name(), ("Sheet1", 1, 0, None))

    def test_range_with_start_row_no_column(self):
        config.WORKSHEET_NAME = "Sheet1!A2:Z"
        self.assertEqual(_parse_worksheet_name(), ("Sheet1", 2, 0, 25))

    def test_range_with_start_row_and_column(self):
        # header at row 4, starting at column C, ending at column F
        # (BIN header at C4, result header at F4)
        config.WORKSHEET_NAME = "Sheet1!C4:F"
        self.assertEqual(_parse_worksheet_name(), ("Sheet1", 4, 2, 5))

    def test_single_cell_no_end_range(self):
        config.WORKSHEET_NAME = "Sheet1!C4"
        self.assertEqual(_parse_worksheet_name(), ("Sheet1", 4, 2, None))


class TestFetchRange(unittest.TestCase):
    """
    Regression test: the range sent to the Sheets API must always be
    valid A1 notation. Google's API rejects mixed cell/column ranges
    like "C4:F" (only same-column open ranges such as "A5:A" are
    valid), which is what originally caused:
    'Unable to parse range: Sheet1!C4:F'.
    """

    def setUp(self):
        self._original_worksheet_name = config.WORKSHEET_NAME

    def tearDown(self):
        config.WORKSHEET_NAME = self._original_worksheet_name

    def test_mixed_cell_column_range_becomes_full_columns(self):
        config.WORKSHEET_NAME = "Sheet1!C4:F"
        self.assertEqual(_fetch_range(), "Sheet1!C:F")

    def test_plain_sheet_name_fetches_whole_sheet(self):
        config.WORKSHEET_NAME = "Sheet1"
        self.assertEqual(_fetch_range(), "Sheet1")

    def test_single_column_start_only(self):
        config.WORKSHEET_NAME = "Sheet1!C4"
        self.assertEqual(_fetch_range(), "Sheet1!C:C")


class TestGetSheetDataUsesFetchRange(unittest.TestCase):

    def setUp(self):
        self._original_worksheet_name = config.WORKSHEET_NAME
        config.WORKSHEET_NAME = "Sheet1!C4:F"

    def tearDown(self):
        config.WORKSHEET_NAME = self._original_worksheet_name

    @patch("sheets_service.get_sheets_service")
    def test_requests_valid_range(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}

        get_sheet_data()

        get_call = mock_service.spreadsheets().values().get
        self.assertEqual(get_call.call_args.kwargs["range"], "Sheet1!C:F")


class TestGetSheetDataDiagnostics(unittest.TestCase):
    """
    Regression test: if the sheet/tab name in WORKSHEET_NAME doesn't
    match a real tab (e.g. "Sheet1" configured but the tab is actually
    named "Лист1"), the Sheets API returns the same generic 400
    "Unable to parse range" error as a syntax problem. We should turn
    that into an actionable message listing the real tab names.
    """

    def setUp(self):
        self._original_worksheet_name = config.WORKSHEET_NAME
        config.WORKSHEET_NAME = "Sheet1!C4:F"

    def tearDown(self):
        config.WORKSHEET_NAME = self._original_worksheet_name

    @patch("sheets_service.get_sheets_service")
    def test_wrong_sheet_name_lists_real_tabs_in_error(self, mock_get_service):
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_resp = MagicMock()
        mock_resp.status = 400
        mock_service.spreadsheets().values().get().execute.side_effect = HttpError(
            mock_resp, b'{"error": {"message": "Unable to parse range: Sheet1!C:F"}}'
        )
        mock_service.spreadsheets().get().execute.return_value = {
            "sheets": [{"properties": {"title": "Лист1"}}]
        }

        with self.assertRaises(Exception) as ctx:
            get_sheet_data()

        self.assertIn("Лист1", str(ctx.exception))
        self.assertIn("WORKSHEET_NAME", str(ctx.exception))


class TestUpdateSheetColumnOffset(unittest.TestCase):
    """
    Regression test: when the fetched range doesn't start at column A
    (e.g. "Sheet1!C4:F"), the write range must use the *absolute*
    sheet column and row, not ones relative to the fetched slice.
    """

    def setUp(self):
        self._original_worksheet_name = config.WORKSHEET_NAME
        config.WORKSHEET_NAME = "Sheet1!C4:F"

    def tearDown(self):
        config.WORKSHEET_NAME = self._original_worksheet_name

    @patch("sheets_service.get_sheets_service")
    def test_writes_to_absolute_result_column(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # header at absolute row 4 -> header_row_index 3
        # data row is rows[4] (absolute sheet row 5)
        # header row: C=БИН, D=..., E=..., F=Наличие отчета -> result_idx=3 (relative)
        updates = [{"row_index": 4, "value": "Да"}]
        result_idx = 3

        update_sheet(updates, result_idx)

        batch_update_call = mock_service.spreadsheets().values().batchUpdate
        body = batch_update_call.call_args.kwargs["body"]

        # column C is index 2, + relative offset 3 = index 5 = "F"
        # row_index 4 (0-based) -> sheet row 5
        self.assertEqual(body["data"][0]["range"], "Sheet1!F5")


if __name__ == "__main__":
    unittest.main()
