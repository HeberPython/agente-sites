"""Editorial regression checks for the Phase 4 smart-home hub article."""

import unittest

from handytested_phase4_smart_hubs_release import CONTENT, DESCRIPTION, SOURCE, TITLE
from handytested_editorial_validator import validate


class SmartHubsReleaseTest(unittest.TestCase):
    def test_research_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products={"Amazon Echo Hub", "Google Nest Hub (2nd gen)", "Aeotec Smart Home Hub"})
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_no_old_claims(self) -> None:
        for old in ("2,100-square-foot", "0.9 seconds", "14-day test", "★★★★", "Echo Show 8 (3rd Gen)"):
            self.assertNotIn(old, CONTENT)
        self.assertNotIn("$150", TITLE)
        self.assertIn("Matter", DESCRIPTION)


if __name__ == "__main__":
    unittest.main()
