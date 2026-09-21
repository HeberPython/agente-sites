"""Guarded accessible-name fix for three curated homepage image links."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time

from handytested_phase2 import TOP_SLUGS, home_html, request
from handytested_public_audit import BASE, fetch_html


MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-home-accessibility-backup"))
EXPECTED_MODIFIED = "2026-09-21T18:03:57"


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    home = request("/pages/18?context=edit")
    if home["id"] != 18 or home["slug"] != "home-page" or home["modified"] != EXPECTED_MODIFIED or "Explore Value Picks" not in home["content"]["raw"]:
        raise RuntimeError("Homepage changed since Value Picks release")
    categories = request("/categories?per_page=100&_fields=id,slug,count")
    posts = [request(f"/posts?slug={slug}&_embed=1")[0] for slug in TOP_SLUGS]
    content = home_html(categories, posts)
    if len(re.findall(r'class="ht-card-media"[^>]*aria-label=', content)) != 3:
        raise RuntimeError("Expected three named Top Picks image links")
    print(json.dumps({"mode": MODE, "home": 18, "named_image_links": 3}))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps(home, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        result = request("/pages/18", {"content": content})
        if result.get("id") != 18:
            raise RuntimeError("Homepage update not acknowledged")
        for attempt in range(5):
            live = fetch_html(BASE + "/")
            if len(re.findall(r'class="ht-card-media"[^>]*aria-label=', live)) == 3:
                print("Three Top Picks image links publicly named")
                return
            if attempt == 4:
                raise RuntimeError("Accessible names not visible on homepage")
            time.sleep(3)
    except Exception:
        request("/pages/18", {"content": home["content"]["raw"]})
        raise


if __name__ == "__main__":
    main()
