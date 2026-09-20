"""Editorial regression checks for the voltage tester article."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_voltage_release import CONTENT, SOURCE, TITLE


class VoltageReleaseTest(unittest.TestCase):
    def test_verified_picks_disclosure_and_safety(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products={"Klein Tools NCVT-3P", "Fluke 1AC-A1-II", "Greenlee GT-16"})
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)
        self.assertIn("do not measure voltage, detect every hazard or establish that a circuit is safe to touch", CONTENT)
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_no_unsupported_old_claims(self) -> None:
        for old in ("zero false positives during testing", "After hands-on testing", "★★★★★", "~$35"):
            self.assertNotIn(old, CONTENT)
        self.assertNotIn("2025", TITLE)


if __name__ == "__main__":
    unittest.main()
