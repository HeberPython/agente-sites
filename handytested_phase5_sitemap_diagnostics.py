"""Read-only comparison of WordPress post state relevant to Rank Math XML."""

from __future__ import annotations

import json

from handytested_phase2 import request


SLUGS = (
    "best-robot-vacuums-for-pet-hair-under-300",
    "best-indoor-hydroponic-gardening-systems-under-300",
    "best-portable-outdoor-grills-under-300-for-2025",
    "best-electric-lawn-mowers-under-300-for-2025",
    "best-wireless-earbuds-under-300-for-2025",
    "top-father-s-day-gifts-for-2026-great-deals-and-ideas-2026-07-31",
    "discover-the-best-amazon-deals-this-summer-2026-08-05",
    "best-cordless-drills-under-100",
)

FIELDS = "id,slug,status,link,modified_gmt,meta"
SAFE_META = (
    "rank_math_robots",
    "rank_math_canonical_url",
    "rank_math_sitemap_exclude",
)


def main() -> None:
    for slug in SLUGS:
        posts = request(f"/posts?slug={slug}&context=edit&status=any&_fields={FIELDS}")
        if not isinstance(posts, list):
            raise RuntimeError(f"Unexpected REST response for {slug}")
        for post in posts:
            meta = post.get("meta") or {}
            print(
                json.dumps(
                    {
                        "slug": slug,
                        "id": post["id"],
                        "status": post["status"],
                        "modified_gmt": post["modified_gmt"],
                        "rank_math_meta_exposed": {
                            key: meta[key] for key in SAFE_META if key in meta
                        },
                    }
                )
            )
        if not posts:
            print(json.dumps({"slug": slug, "rest_result": "not returned"}))


if __name__ == "__main__":
    main()
