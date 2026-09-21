"""Focused checks for the oscillating multi-tool release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_oscillating_tools_release import CONTENT, PRODUCTS, SOURCE, TITLE


class OscillatingToolsReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_false_claims_are_corrected(self) -> None:
        self.assertIn("has not cut, sanded, timed or vibration-tested", CONTENT)
        self.assertIn("battery and charger", CONTENT)
        self.assertIn("none of these models is guaranteed below a fixed ceiling", CONTENT)
        self.assertNotIn("stars", CONTENT.lower())


if __name__ == "__main__":
    unittest.main()
