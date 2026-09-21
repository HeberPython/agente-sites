import unittest
from handytested_editorial_validator import validate
from handytested_phase4_digital_torque_wrenches_release import CONTENT, PRODUCTS, SOURCE, TITLE

class DigitalTorqueReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
    def test_accuracy_limits_are_explicit(self) -> None:
        self.assertIn("has not calibrated or torque-tested", CONTENT)
        self.assertIn("does not state the minimum calibrated range or an accuracy tolerance", CONTENT)
        self.assertIn("not a blanket promise", CONTENT)
        self.assertNotIn("stars", CONTENT.lower())

if __name__ == "__main__": unittest.main()
