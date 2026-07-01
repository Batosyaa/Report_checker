import unittest

from drive_service import extract_bins_from_files


class TestExtractBinsFromFiles(unittest.TestCase):

    def test_extracts_bin_from_pdf_name(self):
        files = [{"id": "1", "name": "123456789012.pdf"}]
        self.assertEqual(extract_bins_from_files(files), {"123456789012"})

    def test_suffix_only_stripped_not_substring(self):
        # ".pdf" appearing mid-name must not be stripped from the middle
        files = [{"id": "1", "name": "123456789012_report.pdf"}]
        self.assertEqual(extract_bins_from_files(files), {"123456789012_report"})

    def test_ignores_non_matching_extensions(self):
        files = [
            {"id": "1", "name": "123456789012.pdf"},
            {"id": "2", "name": "123456789013.docx"},
        ]
        self.assertEqual(extract_bins_from_files(files), {"123456789012"})

    def test_extension_check_is_case_insensitive(self):
        files = [{"id": "1", "name": "123456789012.PDF"}]
        self.assertEqual(extract_bins_from_files(files), {"123456789012"})

    def test_strips_whitespace(self):
        files = [{"id": "1", "name": " 123456789012 .pdf"}]
        self.assertEqual(extract_bins_from_files(files), {"123456789012"})


if __name__ == "__main__":
    unittest.main()
