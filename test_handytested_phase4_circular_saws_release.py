import unittest
from handytested_editorial_validator import validate
from handytested_phase4_circular_saws_release import CONTENT, PRODUCTS, SOURCE, TITLE

class CircularSawsReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
    def test_package_and_claim_limits_are_explicit(self) -> None:
        self.assertIn("has not cut lumber or measured runtime", CONTENT)
        self.assertIn("battery and charger are sold separately", CONTENT)
        self.assertIn("does not promise a fixed ceiling", CONTENT)
        self.assertNotIn("stars", CONTENT.lower())

if __name__ == "__main__": unittest.main()
