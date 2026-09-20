import unittest
from unittest.mock import patch

from handytested_phase4_multimeter_release import check_public


class MultimeterReleaseTests(unittest.TestCase):
    @patch("handytested_phase4_multimeter_release.public_meta")
    @patch("handytested_phase4_multimeter_release.fetch_html")
    def test_cat_iii_does_not_trigger_old_cat_ii_check(self, fetch, meta):
        fetch.return_value = (
            "<h1>Multimeters for Home Electrical Troubleshooting</h1>"
            "<p>As an Amazon Associate I earn from qualifying purchases.</p>"
            "<p>Klein Tools MM325; Klein Tools MM420; Fluke 110. "
            "The old Fluke 101 was actually CAT III 600 V.</p>"
            "handytested0d-20 handytested0d-20 handytested0d-20"
        )
        meta.return_value = {"canonical": "https://example.com/", "title": "", "description": ""}
        self.assertEqual(meta.return_value, check_public("https://example.com/"))


if __name__ == "__main__":
    unittest.main()
