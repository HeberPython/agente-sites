"""Focused checks for the cordless-ratchet release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_cordless_ratchets_release import CONTENT, PRODUCTS, SOURCE, TITLE


class CordlessRatchetsReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_claims_and_safety_are_corrected(self) -> None:
        self.assertIn("has not torque-tested, timed or durability-tested", CONTENT)
        self.assertIn("calibrated torque wrench", CONTENT)
        self.assertIn("battery and charger are sold separately", CONTENT.lower())
        self.assertNotIn("stars", CONTENT.lower())


if __name__ == "__main__":
    unittest.main()
