import tempfile
import unittest
from pathlib import Path

from handytested_editorial_validator import validate


class ValidatorTests(unittest.TestCase):
    def test_blocks_unsupported_hands_on_and_missing_disclosure(self):
        findings = validate("Best drills 2025", "<p>We tested three drills.</p>")
        codes = {item["code"] for item in findings}
        self.assertTrue({"TEST_CLAIM", "DISCLOSURE", "SOURCE_RECORD", "PRODUCT_VERIFICATION", "TITLE_YEAR"} <= codes)

    def test_flags_search_and_bad_tag(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "sources.md"
            record.write_text("Manufacturer source checked", encoding="utf-8")
            content = (
                f"<p>As an Amazon Associate I earn from qualifying purchases.</p>"
                '<a href="https://www.amazon.com/s?k=tool&tag=wrong-20">View</a>'
            )
            findings = validate("Tool guide", content, source_record=record, verified_products={"tool"})
            self.assertEqual({"AMAZON_SEARCH", "AMAZON_TAG"}, {item["code"] for item in findings})

    def test_clean_research_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "sources.md"
            record.write_text("Manufacturer source checked", encoding="utf-8")
            content = "<p>As an Amazon Associate I earn from qualifying purchases.</p><h2>Options</h2>"
            self.assertEqual([], validate("Tool guide", content, source_record=record, verified_products={"tool"}))


if __name__ == "__main__":
    unittest.main()
