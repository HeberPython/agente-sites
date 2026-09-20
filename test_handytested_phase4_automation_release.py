"""Editorial regression checks for smart-home automation."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_automation_release import CONTENT, PRODUCTS, SOURCE, TITLE


class AutomationReleaseTest(unittest.TestCase):
    def test_verified_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 4)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_wiring_and_compatibility_caveats(self) -> None:
        self.assertIn("neutral wire", CONTENT)
        self.assertIn("single-pole", CONTENT)
        self.assertIn("not installed or performance-tested", CONTENT)


if __name__ == "__main__":
    unittest.main()
