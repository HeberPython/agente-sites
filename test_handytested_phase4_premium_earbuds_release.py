"""Editorial regression checks for premium earbuds."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_premium_earbuds_release import CONTENT, PRODUCTS, SOURCE, TITLE


class PremiumEarbudsReleaseTest(unittest.TestCase):
    def test_verified_models_and_disclosure(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)
        self.assertIn("As an Amazon Associate I earn from qualifying purchases.", CONTENT)

    def test_ecosystem_caveats(self) -> None:
        self.assertNotIn("Under $300", TITLE)
        self.assertIn("select Galaxy", CONTENT)
        self.assertIn("not a controlled battery or ANC comparison", CONTENT)


if __name__ == "__main__":
    unittest.main()
