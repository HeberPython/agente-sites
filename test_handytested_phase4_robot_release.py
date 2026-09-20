"""Editorial regression checks for the pet-hair robot-vacuum article."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_robot_release import CONTENT, SOURCE, TITLE


class RobotReleaseTest(unittest.TestCase):
    def test_verified_picks_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products={"Roborock Q7 M5", "Shark Navigator RV2120AE"})
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 2)

    def test_budget_and_model_precision(self) -> None:
        self.assertNotIn("Under $300", TITLE)
        self.assertIn("regular manufacturer list price exceeds", CONTENT)
        self.assertNotIn("Neato D4", CONTENT)


if __name__ == "__main__":
    unittest.main()
