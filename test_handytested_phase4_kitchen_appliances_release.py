"""Focused checks for the kitchen-appliances release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_kitchen_appliances_release import CONTENT, PRODUCTS, SOURCE, TITLE


class KitchenAppliancesReleaseTest(unittest.TestCase):
    def test_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_capacity_price_and_variant_caveats(self) -> None:
        self.assertIn("64 oz maximum liquid capacity", CONTENT)
        self.assertIn("not a fixed-budget", CONTENT)
        self.assertIn("archived 49980A", CONTENT)


if __name__ == "__main__":
    unittest.main()
