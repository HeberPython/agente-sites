import unittest
from handytested_editorial_validator import validate
from handytested_phase4_rotary_tools_release import CONTENT, PRODUCTS, SOURCE, TITLE
class RotaryToolsReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self):
        self.assertFalse([f for f in validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS) if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
    def test_claim_limits(self):
        self.assertIn("has not cut, carved, sanded or polished", CONTENT)
        self.assertIn("does not publish motor amperage or a speed range", CONTENT)
        self.assertIn("does not promise a fixed ceiling", CONTENT)
        self.assertNotIn("stars", CONTENT.lower())
if __name__ == "__main__": unittest.main()
