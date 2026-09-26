"""Offline tests for the surgical homepage LCP optimization."""

from __future__ import annotations

import unittest

import handytested_phase5_mobile_performance as release


def baseline() -> str:
    return f'''<style>{release.OLD_HERO_CSS}@media(max-width:600px){{{release.OLD_MOBILE_CSS}}}</style>
<main><a href="/one/">One</a>{release.OLD_HERO_OPEN}<p>Hero copy</p></div></section>
<a href="https://www.amazon.com/s?k=test&tag=handytested0d-20">Amazon</a>
<p>As an Amazon Associate I earn from qualifying purchases.</p></main>'''


class MobilePerformanceTests(unittest.TestCase):
    def test_transform_makes_lcp_image_immediately_discoverable(self) -> None:
        original = baseline()
        updated, changed = release.optimize_home_content(original)
        self.assertTrue(changed)
        self.assertIn('<img class="ht-hero-media"', updated)
        self.assertIn('fetchpriority="high"', updated)
        self.assertIn('decoding="async"', updated)
        self.assertIn('sizes="100vw"', updated)
        self.assertNotIn('loading=', updated)
        self.assertNotIn(release.OLD_HERO_CSS, updated)
        self.assertNotIn(release.OLD_MOBILE_CSS, updated)

    def test_transform_preserves_links_affiliate_tag_and_disclosure(self) -> None:
        original = baseline()
        updated, _ = release.optimize_home_content(original)
        self.assertEqual(release.anchor_hrefs(original), release.anchor_hrefs(updated))
        self.assertEqual(original.count("handytested0d-20"), updated.count("handytested0d-20"))
        self.assertEqual(
            original.count("As an Amazon Associate I earn from qualifying purchases."),
            updated.count("As an Amazon Associate I earn from qualifying purchases."),
        )

    def test_transform_is_idempotent(self) -> None:
        updated, _ = release.optimize_home_content(baseline())
        repeated, changed = release.optimize_home_content(updated)
        self.assertFalse(changed)
        self.assertEqual(repeated, updated)

    def test_changed_baseline_is_refused(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "baseline changed"):
            release.optimize_home_content(baseline().replace("65% center", "60% center"))


if __name__ == "__main__":
    unittest.main()
