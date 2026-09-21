"""Focused checks for the laser-level release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_laser_levels_release import CONTENT, PRODUCTS, SOURCE, TITLE


class LaserLevelsReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_false_claims_are_corrected(self) -> None:
        self.assertIn("has not calibrated, dropped or visibility-tested", CONTENT)
        self.assertIn("not a self-leveling cross-line laser", CONTENT)
        self.assertIn("none is guaranteed below a fixed ceiling", CONTENT)
        self.assertNotIn("stars", CONTENT.lower())


if __name__ == "__main__":
    unittest.main()

