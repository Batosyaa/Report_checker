import unittest
from unittest.mock import patch, MagicMock

import config
from sheets_service import (
    get_column_indexes,
    build_updates,
    update_sheet,
    _column_letter,
    _column_index,
    _sheet_name_and_start_row,
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


class TestSheetNameAndStartRow(unittest.TestCase):

    def setUp(self):
        self._original_worksheet_name = config.WORKSHEET_NAME

    def tearDown(self):
        config.WORKSHEET_NAME = self._original_worksheet_name

    def test_plain_sheet_name_defaults_to_row_one_col_a(self):
        config.WORKSHEET_NAME = "Sheet1"
        self.assertEqual(_sheet_name_and_start_row(), ("Sheet1", 1, 0))

    def test_range_with_start_row_no_column(self):
        config.WORKSHEET_NAME = "Sheet1!A2:Z"
        self.assertEqual(_sheet_name_and_start_row(), ("Sheet1", 2, 0))

    def test_range_with_start_row_and_column(self):
        # header at row 4, starting at column C (as in the real sheet:
        # BIN header at C4, result header at F4)
        config.WORKSHEET_NAME = "Sheet1!C4:F"
        self.assertEqual(_sheet_name_and_start_row(), ("Sheet1", 4, 2))


class TestUpdateSheetColumnOffset(unittest.TestCase):
    """
    Regression test: when the fetched range doesn't start at column A
    (e.g. "Sheet1!C4:F"), the write range must use the *absolute*
    sheet column, not a column relative to the fetched range.
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

        # header row: C=БИН, D=..., E=..., F=Наличие отчета -> result_idx=3 (relative)
        updates = [{"row_index": 1, "value": "Да"}]
        result_idx = 3

        update_sheet(updates, result_idx)

        batch_update_call = mock_service.spreadsheets().values().batchUpdate
        body = batch_update_call.call_args.kwargs["body"]

        # column C is index 2, + relative offset 3 = index 5 = "F"
        # row_index 1 + start_row 4 = sheet row 5
        self.assertEqual(body["data"][0]["range"], "Sheet1!F5")


if __name__ == "__main__":
    unittest.main()
