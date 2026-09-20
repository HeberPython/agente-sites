"""Focused editorial checks for the office-chair release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_office_chairs_release import CONTENT, PRODUCTS, SOURCE, TITLE


class OfficeChairReleaseTest(unittest.TestCase):
    def test_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_fit_and_budget_caveats(self) -> None:
        self.assertIn("Fixed 15.9-inch seat depth", CONTENT)
        self.assertIn("full model code", CONTENT)
        self.assertIn("far above that ceiling", CONTENT)


if __name__ == "__main__":
    unittest.main()
