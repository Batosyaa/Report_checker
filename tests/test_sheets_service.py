import unittest

import config
from sheets_service import (
    get_column_indexes,
    build_updates,
    _column_letter,
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


class TestSheetNameAndStartRow(unittest.TestCase):

    def setUp(self):
        self._original_worksheet_name = config.WORKSHEET_NAME

    def tearDown(self):
        config.WORKSHEET_NAME = self._original_worksheet_name

    def test_plain_sheet_name_defaults_to_row_one(self):
        config.WORKSHEET_NAME = "Sheet1"
        self.assertEqual(_sheet_name_and_start_row(), ("Sheet1", 1))

    def test_range_with_start_row(self):
        config.WORKSHEET_NAME = "Sheet1!A2:Z"
        self.assertEqual(_sheet_name_and_start_row(), ("Sheet1", 2))


if __name__ == "__main__":
    unittest.main()
