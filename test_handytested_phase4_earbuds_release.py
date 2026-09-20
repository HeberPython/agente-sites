"""Editorial regression checks for the under-$100 earbuds article."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_earbuds_release import CONTENT, SOURCE, TITLE


class EarbudsReleaseTest(unittest.TestCase):
    def test_verified_picks_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products={"JLab Go Pop+", "JBL Vibe Beam 2", "soundcore P40i"})
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_no_unsourced_testing(self) -> None:
        for old in ("six weeks testing", "three remote evaluators", "72–78 dB", "Jabra Elite 4 — unmatched", "Sony WF-C700N —"):
            self.assertNotIn(old, CONTENT)
        self.assertNotIn("2025", TITLE)


if __name__ == "__main__":
    unittest.main()
