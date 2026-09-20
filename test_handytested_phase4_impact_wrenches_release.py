"""Focused editorial checks for the impact-wrench release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_impact_wrenches_release import CONTENT, PRODUCTS, SOURCE, TITLE


class ImpactWrenchReleaseTest(unittest.TestCase):
    def test_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_model_identity_and_torque_safety(self) -> None:
        self.assertIn("LGC120 as a garden cultivator", CONTENT)
        self.assertIn("finish with a hand torque wrench", CONTENT)
        self.assertIn("battery and charger are sold separately", CONTENT)
        self.assertNotIn("72 hours", CONTENT)


if __name__ == "__main__":
    unittest.main()
