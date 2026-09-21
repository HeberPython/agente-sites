"""Guarded correction of stale Deals page, homepage copy and menu label."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

from handytested_phase2 import BASE, TOP_SLUGS, home_html, request
from handytested_phase3_paint_release import api as rankmath_api, public_meta
from handytested_public_audit import fetch_html, plain


MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-deals-backup"))
CONTENT = Path(__file__).with_name("handytested_phase5_deals.html").read_text(encoding="utf-8")
TITLE = "Value Picks & Product Discovery"
SEO_TITLE = "Value Picks & Product Discovery | HandyTested"
DESCRIPTION = "Explore research-led product guides for tools, home and useful tech. Compare exact models and trade-offs, then check current listings before buying."
EXPECTED_HOME_MODIFIED = "2026-09-21T17:45:00"
EXPECTED_DEALS_MODIFIED = "2026-09-19T18:27:09"
OLD_LINKS = (
    "top-discounts-on-baby-products-you-can-t-miss-2026-05-29",
    "unmissable-deals-in-the-upcoming-amazon-6-6-sale-2026-05-29",
)
NEW_LINKS = (
    "/best-cordless-drills-under-100/",
    "/best-random-orbital-sanders-for-diy-projects-2025/",
    "/best-robot-vacuums-for-pet-hair-under-300/",
)


def check_public() -> None:
    source = fetch_html(BASE + "/deals/")
    meta = public_meta(source)
    text = plain(source)
    if TITLE not in text or "As an Amazon Associate I earn from qualifying purchases." not in text:
        raise RuntimeError("Deals title/disclosure missing")
    if meta != {"title": SEO_TITLE, "description": DESCRIPTION, "canonical": BASE + "/deals/"}:
        raise RuntimeError(f"Deals SEO metadata mismatch: {meta}")
    if any(old in source for old in OLD_LINKS) or not all(link in source for link in NEW_LINKS):
        raise RuntimeError("Deals links are stale or missing")
    if "See Latest Deals" in fetch_html(BASE + "/"):
        raise RuntimeError("Homepage still promises latest deals")


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    deals = request("/pages/95?context=edit")
    home = request("/pages/18?context=edit")
    if deals["slug"] != "deals" or deals["status"] != "publish" or deals["modified"] != EXPECTED_DEALS_MODIFIED or deals["title"]["raw"] != "Amazon Deals":
        raise RuntimeError("Deals page changed since baseline")
    if not all(old in deals["content"]["raw"] for old in OLD_LINKS):
        raise RuntimeError("Deals page no longer contains the known stale links")
    if home["slug"] != "home-page" or home["modified"] != EXPECTED_HOME_MODIFIED or "See Latest Deals" not in home["content"]["raw"]:
        raise RuntimeError("Homepage changed since excerpt release")
    old_meta = public_meta(fetch_html(BASE + "/deals/"))
    if old_meta["canonical"] != BASE + "/deals/":
        raise RuntimeError("Deals canonical changed")
    menus = request("/menus?context=edit")
    primary = next((m for m in menus if "primary" in m.get("locations", [])), None)
    if not primary:
        raise RuntimeError("Primary menu unavailable")
    items = request(f"/menu-items?menus={primary['id']}&per_page=100&context=edit")
    deals_items = [i for i in items if i.get("url") == BASE + "/deals/"]
    if len(deals_items) != 1 or deals_items[0]["title"]["raw"] != "Deals":
        raise RuntimeError("Deals menu item changed")
    menu_item = deals_items[0]
    categories = request("/categories?per_page=100&_fields=id,slug,count")
    top_posts = [request(f"/posts?slug={slug}&_embed=1")[0] for slug in TOP_SLUGS]
    home_content = home_html(categories, top_posts)
    if "See Latest Deals" in home_content or "Explore Value Picks" not in home_content:
        raise RuntimeError("Homepage copy did not update")
    print(json.dumps({"mode": MODE, "deals_page": 95, "home_page": 18, "menu_item": menu_item["id"]}))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps({"deals": deals, "home": home, "menu_item": menu_item, "deals_public_meta": old_meta}, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = []
    try:
        request("/pages/95", {"title": TITLE, "content": CONTENT})
        changed.append("deals")
        rankmath_api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": 95, "meta": {"rank_math_title": SEO_TITLE, "rank_math_description": DESCRIPTION}})
        changed.append("meta")
        request("/pages/18", {"content": home_content})
        changed.append("home")
        request(f"/menu-items/{menu_item['id']}", {"title": "Value Picks"})
        changed.append("menu")
        for attempt in range(5):
            try:
                check_public()
                print("Published and verified value-picks page, homepage and menu")
                return
            except RuntimeError:
                if attempt == 4:
                    raise
                time.sleep(3)
    except Exception:
        if "menu" in changed:
            request(f"/menu-items/{menu_item['id']}", {"title": "Deals"})
        if "home" in changed:
            request("/pages/18", {"content": home["content"]["raw"]})
        if "meta" in changed:
            rankmath_api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": 95, "meta": {"rank_math_title": old_meta["title"], "rank_math_description": old_meta["description"]}})
        if "deals" in changed:
            request("/pages/95", {"title": deals["title"]["raw"], "content": deals["content"]["raw"]})
        raise


if __name__ == "__main__":
    main()
