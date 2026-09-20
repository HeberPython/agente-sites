"""Focused editorial checks for the brad-nailer release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_nailers_release import CONTENT, PRODUCTS, SOURCE, TITLE


class NailerReleaseTest(unittest.TestCase):
    def test_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_package_and_safety_caveats(self) -> None:
        self.assertIn("P320 discontinued", CONTENT)
        self.assertIn("battery and charger are sold separately", CONTENT)
        self.assertIn("not framing", CONTENT)


if __name__ == "__main__":
    unittest.main()
