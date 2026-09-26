import re
import unittest

from handytested_phase4_stud_finders_release import (
    BASELINE_CONTENT,
    CONTENT,
    DESCRIPTION,
    NEW_OPENING,
    SEO_TITLE,
    TITLE,
    release_findings,
)


class StudFindersReleaseTest(unittest.TestCase):
    def test_models_disclosure_and_links(self):
        self.assertFalse([f for f in release_findings() if f["severity"] == "BLOCK"])
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), 3)

    def test_claim_limits(self):
        self.assertIn("not results from hands-on testing by HandyTested", CONTENT)
        self.assertIn("does not promise a fixed under-$50 ceiling", CONTENT)
        self.assertIn("cannot prove that a cavity contains no live wire", CONTENT)
        self.assertNotIn("★★★★★", CONTENT)

    def test_controlled_seo_experiment(self):
        self.assertEqual(TITLE, "Best Stud Finders for DIY Home Projects")
        self.assertEqual(SEO_TITLE, "Best Stud Finders for DIY Projects: Budget Picks for 2026")
        self.assertEqual(
            DESCRIPTION,
            "Compare stud finders for DIY home projects, including Franklin, Zircon and CRAFTSMAN. See key features, limitations and which model fits your needs.",
        )
        self.assertEqual(CONTENT.count(NEW_OPENING), 1)
        self.assertIn("The Zircon StudSensor e50 is an edge-finding model", NEW_OPENING)
        self.assertNotIn("we tested", CONTENT.lower())

    def test_links_and_commercial_signals_are_unchanged(self):
        self.assertEqual(CONTENT.count("tag=handytested0d-20"), BASELINE_CONTENT.count("tag=handytested0d-20"))
        self.assertEqual(
            re.findall(r'href="([^"]+)"', CONTENT),
            re.findall(r'href="([^"]+)"', BASELINE_CONTENT),
        )


if __name__ == "__main__":
    unittest.main()
