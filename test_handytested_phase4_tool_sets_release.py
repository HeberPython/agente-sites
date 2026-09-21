"""Focused checks for the home-tool-set release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_tool_sets_release import CONTENT, PRODUCTS, SOURCE, TITLE


class ToolSetsReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_false_claims_are_corrected(self) -> None:
        self.assertIn("has not used or durability-tested", CONTENT)
        self.assertIn("not a complete home tool chest", CONTENT)
        self.assertIn("not measurement instruments", CONTENT)


if __name__ == "__main__":
    unittest.main()
