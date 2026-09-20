"""Editorial regression checks for smoothie blenders."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_blenders_release import CONTENT, PRODUCTS, SOURCE, TITLE


class BlendersReleaseTest(unittest.TestCase):
    def test_verified_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_tradeoffs_are_explicit(self) -> None:
        self.assertIn("72-ounce total-capacity pitcher", CONTENT)
        self.assertIn("separately sold", CONTENT)
        self.assertIn("not a laboratory or hands-on ranking", CONTENT)


if __name__ == "__main__":
    unittest.main()
