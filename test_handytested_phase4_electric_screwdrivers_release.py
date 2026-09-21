"""Focused checks for the electric-screwdriver release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_electric_screwdrivers_release import CONTENT, PRODUCTS, SOURCE, TITLE


class ElectricScrewdriversReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_false_claims_and_sensor_limit_are_corrected(self) -> None:
        self.assertIn("has not runtime-tested, torque-tested or assembled furniture", CONTENT)
        self.assertIn("sensor is a screening feature, not proof", CONTENT)
        self.assertIn("not a substitute for a drill/driver", CONTENT)
        self.assertNotIn("stars", CONTENT.lower())


if __name__ == "__main__":
    unittest.main()
