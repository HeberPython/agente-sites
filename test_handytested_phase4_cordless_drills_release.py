import unittest

from handytested_editorial_validator import validate
from handytested_phase4_cordless_drills_release import CONTENT, PRODUCTS, SOURCE, TITLE


class CordlessDrillsReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self):
        self.assertFalse([f for f in validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS) if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_claim_limits(self):
        self.assertIn("has not drilled test holes", CONTENT)
        self.assertIn("does not promise a fixed under-$100 ceiling", CONTENT)
        self.assertIn("page's Includes section lists 1.3Ah", CONTENT)
        self.assertNotIn("4.8/5", CONTENT)


if __name__ == "__main__":
    unittest.main()
