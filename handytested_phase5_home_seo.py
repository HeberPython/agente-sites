"""Guarded homepage Rank Math metadata alignment with Value Picks."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

from handytested_phase2 import request
from handytested_phase3_paint_release import api, public_meta
from handytested_public_audit import BASE, fetch_html


MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-home-seo-backup"))
EXPECTED_MODIFIED = "2026-09-21T18:11:21"
OLD_TITLE = "HandyTested - Product Reviews, Buying Guides & Amazon Deals"
OLD_DESCRIPTION = "Practical product reviews, buying guides, and Amazon deal guidance for tools, electronics, smart home, DIY, kitchen, and everyday gear."
TITLE = "HandyTested | Research-Led Buying Guides & Value Picks"
DESCRIPTION = "Research-led buying guides for tools, DIY, home and useful tech. Compare exact models and trade-offs, then check current listings before buying."


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    home = request("/pages/18?context=edit&_fields=id,slug,status,modified,content")
    if home["id"] != 18 or home["slug"] != "home-page" or home["status"] != "publish" or home["modified"] != EXPECTED_MODIFIED or "Explore Value Picks" not in home["content"]["raw"]:
        raise RuntimeError("Homepage changed since accessibility release")
    old_meta = public_meta(fetch_html(BASE + "/"))
    if old_meta != {"title": OLD_TITLE, "description": OLD_DESCRIPTION, "canonical": BASE + "/"}:
        raise RuntimeError("Homepage SEO baseline changed")
    print(json.dumps({"mode": MODE, "home": 18, "title": TITLE}))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps({"home": home, "public_meta": old_meta}, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": 18, "meta": {"rank_math_title": TITLE, "rank_math_description": DESCRIPTION}})
        for attempt in range(5):
            meta = public_meta(fetch_html(BASE + "/"))
            if meta == {"title": TITLE, "description": DESCRIPTION, "canonical": BASE + "/"}:
                print("Homepage SEO metadata publicly verified")
                return
            if attempt == 4:
                raise RuntimeError(f"Homepage SEO metadata not public: {meta}")
            time.sleep(3)
    except Exception:
        api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": 18, "meta": {"rank_math_title": OLD_TITLE, "rank_math_description": OLD_DESCRIPTION}})
        raise


if __name__ == "__main__":
    main()
