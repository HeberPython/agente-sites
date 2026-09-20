"""Editorial regression checks for smart-home devices."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_smart_devices_release import CONTENT, PRODUCTS, SOURCE, TITLE


class SmartDevicesReleaseTest(unittest.TestCase):
    def test_verified_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_subscription_hvac_and_matter_caveats(self) -> None:
        self.assertIn("Protect subscription", CONTENT)
        self.assertIn("compatibility checker", CONTENT)
        self.assertIn("not mean the same energy chart", CONTENT)


if __name__ == "__main__":
    unittest.main()
