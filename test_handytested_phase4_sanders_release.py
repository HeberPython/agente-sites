"""Editorial regression checks for the random orbital sander article."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_sanders_release import CONTENT, SOURCE, TITLE


class SandersReleaseTest(unittest.TestCase):
    def test_verified_picks_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products={"DEWALT DCW210B", "Makita BO5041", "BLACK+DECKER BDERO100"})
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_no_unsupported_old_claims(self) -> None:
        for old in ("We tested four popular models", "captured over 98%", "Battery life averaged", "★★★★★"):
            self.assertNotIn(old, CONTENT)
        self.assertNotIn("2025", TITLE)


if __name__ == "__main__":
    unittest.main()
