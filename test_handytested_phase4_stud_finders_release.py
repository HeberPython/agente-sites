import unittest

from handytested_editorial_validator import validate
from handytested_phase4_stud_finders_release import CONTENT, PRODUCTS, SOURCE, TITLE


class StudFindersReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self):
        self.assertFalse([f for f in validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS) if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_claim_limits(self):
        self.assertIn("has not scanned test walls", CONTENT)
        self.assertIn("does not promise a fixed under-$50 ceiling", CONTENT)
        self.assertIn("cannot prove that a cavity contains no live wire", CONTENT)
        self.assertNotIn("★★★★★", CONTENT)


if __name__ == "__main__":
    unittest.main()
