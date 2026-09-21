"""Focused editorial checks for the camping-gear release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_camping_release import CONTENT, PRODUCTS, SOURCE, TITLE


class CampingReleaseTest(unittest.TestCase):
    def test_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_budget_temperature_and_co_caveats(self) -> None:
        self.assertIn("not a complete kit", CONTENT)
        self.assertIn("25F-30F comfort range", CONTENT)
        self.assertIn("carbon monoxide", CONTENT)


if __name__ == "__main__":
    unittest.main()
