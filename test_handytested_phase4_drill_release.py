"""Editorial regression checks for the under-$300 drill press article."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_drill_release import CONTENT, SOURCE, TITLE


class DrillReleaseTest(unittest.TestCase):
    def test_verified_picks_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products={"SKIL DP9505-00", "WEN 4212T", "Shop Fox W1667"})
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_no_unsupported_old_claims(self) -> None:
        for old in ("13-inch floor model with", "hands-on testing", "4.8/5", "Jet JDP-15B — under $300"):
            self.assertNotIn(old, CONTENT)
        self.assertNotIn("2025", TITLE)


if __name__ == "__main__":
    unittest.main()
