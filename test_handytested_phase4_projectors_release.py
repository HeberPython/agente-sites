"""Focused editorial checks for the projector release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_projectors_release import CONTENT, PRODUCTS, SOURCE, TITLE


class ProjectorReleaseTest(unittest.TestCase):
    def test_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_native_resolution_and_budget_caveat(self) -> None:
        self.assertIn("native 1920 x 1080", CONTENT)
        self.assertIn("only the Yaber manufacturer's displayed offer was below", CONTENT)
        self.assertIn("800 x 600 native pixels", CONTENT)


if __name__ == "__main__":
    unittest.main()
