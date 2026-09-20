"""Editorial regression checks for the electric mower guide."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_mowers_release import CONTENT, PRODUCTS, SOURCE, TITLE


class MowersReleaseTest(unittest.TestCase):
    def test_sources_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 2)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_variant_and_safety(self) -> None:
        self.assertNotIn("Under $300", TITLE)
        self.assertIn("battery and charger", CONTENT)
        self.assertIn("appropriate-gauge extension cord", CONTENT)


if __name__ == "__main__":
    unittest.main()
