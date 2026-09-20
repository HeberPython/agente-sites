"""Editorial regression checks for outdoor furniture kits."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_outdoor_furniture_release import CONTENT, PRODUCTS, SOURCE, TITLE


class OutdoorFurnitureReleaseTest(unittest.TestCase):
    def test_verified_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_material_cost_and_assembly_distinction(self) -> None:
        self.assertIn("lumber is not included", CONTENT)
        self.assertIn("not a custom-length lumber project", CONTENT)
        self.assertIn("Estimate the entire bill of materials first.", CONTENT)


if __name__ == "__main__":
    unittest.main()
