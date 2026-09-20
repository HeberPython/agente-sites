import os
import unittest
from unittest.mock import patch

from handytested_release_gate import require_publish_approval


class ReleaseGateTests(unittest.TestCase):
    def test_draft_needs_no_approval(self):
        require_publish_approval("draft", "Draft", "<p>Draft</p>")

    def test_publish_needs_explicit_approval(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "HT_EDITORIAL_APPROVED"):
                require_publish_approval("publish", "Guide", "<p>Guide</p>")

    def test_record_must_be_versioned(self):
        with patch.dict(os.environ, {"HT_EDITORIAL_APPROVED": "1", "HT_SOURCE_RECORD": "../private.md"}):
            with self.assertRaisesRegex(RuntimeError, "versioned"):
                require_publish_approval("publish", "Guide", "<p>Guide</p>")

    def test_matching_evidence_allows_clean_article(self):
        environment = {
            "HT_EDITORIAL_APPROVED": "1",
            "HT_SOURCE_RECORD": "verified-paint-sprayers.md",
            "HT_VERIFIED_PRODUCTS": "Wagner FLEXiO 590",
        }
        content = "<p>As an Amazon Associate I earn from qualifying purchases.</p><p>Wagner FLEXiO 590 is a documented sprayer.</p>"
        with patch.dict(os.environ, environment, clear=True):
            require_publish_approval("publish", "Paint sprayer guide", content)

    def test_unrelated_product_is_rejected(self):
        environment = {
            "HT_EDITORIAL_APPROVED": "1",
            "HT_SOURCE_RECORD": "verified-paint-sprayers.md",
            "HT_VERIFIED_PRODUCTS": "Unrelated model",
        }
        content = "<p>As an Amazon Associate I earn from qualifying purchases.</p><p>Unrelated model.</p>"
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaisesRegex(RuntimeError, "not present"):
                require_publish_approval("publish", "Guide", content)


if __name__ == "__main__":
    unittest.main()
