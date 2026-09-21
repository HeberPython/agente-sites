"""Focused checks for the security-camera release."""

import unittest

from handytested_editorial_validator import validate
from handytested_phase4_security_cameras_release import CONTENT, PRODUCTS, SOURCE, TITLE


class SecurityCamerasReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_tagged_searches(self) -> None:
        findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
        self.assertFalse([f for f in findings if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_storage_and_generation_caveats(self) -> None:
        self.assertIn("Sync Module Core does not provide local storage", CONTENT)
        self.assertIn("cannot review, save or share missed videos", CONTENT)
        self.assertIn("VMC2050 is a separate lower-resolution variant", CONTENT)


if __name__ == "__main__":
    unittest.main()
