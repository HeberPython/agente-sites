"""Focused editorial checks for the carpet-cleaner release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_carpet_cleaners_release import CONTENT, PRODUCTS, SOURCE, TITLE


class CarpetCleanerReleaseTest(unittest.TestCase):
    def test_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_extraction_and_drying_caveats(self) -> None:
        self.assertIn("cannot extract a liquid spill", CONTENT)
        self.assertIn("without steam", CONTENT)
        self.assertIn("no universal clock", CONTENT.lower())


if __name__ == "__main__":
    unittest.main()
