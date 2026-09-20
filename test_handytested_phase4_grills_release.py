"""Editorial regression checks for the portable grills guide."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_grills_release import CONTENT, PRODUCTS, SOURCE, TITLE


class GrillsReleaseTest(unittest.TestCase):
    def test_documented_picks_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 2)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_variant_safety_and_budget(self) -> None:
        self.assertNotIn("Under $300", TITLE)
        self.assertIn("Cuisinart labels its current product page discontinued", CONTENT)
        self.assertIn("carbon monoxide", CONTENT)


if __name__ == "__main__":
    unittest.main()
