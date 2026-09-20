"""Editorial regression checks for the indoor hydroponics guide."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_hydroponics_release import CONTENT, PRODUCTS, SOURCE, TITLE


class HydroponicsReleaseTest(unittest.TestCase):
    def test_sources_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_method_and_budget_precision(self) -> None:
        self.assertNotIn("Under $300", TITLE)
        self.assertIn("Smart Soil", CONTENT)
        self.assertIn("not direct product links", CONTENT)


if __name__ == "__main__":
    unittest.main()
