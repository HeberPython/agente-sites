"""Offline checks for the WordPress phase 2 renderer."""

import os
import unittest

os.environ.setdefault("HT_WP_PASS", "offline-test-only")

import handytested_phase2 as phase2


def sample_post(slug: str) -> dict:
    return {
        "slug": slug,
        "title": {"rendered": "A &amp; B <em>guide</em>"},
        "link": "https://handytested.com/" + slug + "/",
        "excerpt": {"rendered": "Choose carefully before buying."},
        "_embedded": {"wp:featuredmedia": [{"media_details": {"sizes": {
            "medium_large": {"source_url": "https://handytested.com/image.jpg", "width": 768, "height": 432}
        }}}]},
    }


class Phase2Tests(unittest.TestCase):
    def test_home_uses_server_rendered_latest_posts(self) -> None:
        categories = [{"slug": "tools", "count": 14}, {"slug": "electronics", "count": 7}, {"slug": "cleaning", "count": 0}]
        posts = [sample_post(slug) for slug in phase2.TOP_SLUGS]
        result = phase2.home_html(categories, posts)
        self.assertIn('<!-- wp:latest-posts {"postsToShow":6', result)
        self.assertIn('displayFeaturedImage\":true', result)
        self.assertNotIn('/category/cleaning/', result)
        self.assertIn('/category/tools/', result)
        self.assertEqual(result.count('<h1'), 1)
        self.assertNotIn('handytested0d-20', result)
        self.assertIn('width="768" height="432"', result)
        self.assertIn('A &amp; B guide', result)

    def test_footer_has_exact_disclosure(self) -> None:
        result = phase2.footer_html()
        self.assertIn('As an Amazon Associate I earn from qualifying purchases.', result)
        self.assertIn('/affiliate-disclosure/', result)
        self.assertNotIn('/pinterest-connect/', result)


if __name__ == "__main__":
    unittest.main()
