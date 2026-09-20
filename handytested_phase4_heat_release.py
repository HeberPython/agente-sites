"""Revision-guarded WordPress release for the researched heat-gun article."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time

from handytested_editorial_validator import validate
from handytested_phase3_paint_release import api, public_meta
from handytested_phase3_review import DISCLOSURE, TAG
from handytested_public_audit import fetch_html, plain


ROOT = Path(__file__).parent
SLUG = "best-heat-guns-for-diy-projects-under-80-in-2025"
POST_ID = 56
TITLE = "Heat Guns for DIY Projects: Three Documented Options"
SEO_TITLE = TITLE + " | HandyTested"
DESCRIPTION = "Compare Wagner HT1000, BLACK+DECKER HG1300 and DEWALT D26950 heat guns using manufacturer specifications, trade-offs and safety guidance."
CONTENT = (ROOT / "handytested_phase4_heat_guns.html").read_text(encoding="utf-8")
SOURCE = ROOT / "handytested_sources" / (SLUG + ".md")
SNAPSHOT = ROOT / "handytested_sources" / "public_snapshot.json"
MODE = os.getenv("MODE", "dry-run")
BACKUP = Path(os.getenv("BACKUP_DIR", "handytested-phase4-heat-backup"))


def check_public(url: str) -> dict[str, str]:
    source = fetch_html(url)
    meta = public_meta(source)
    if len(re.findall(r"<h1\b", source, re.I)) != 1:
        raise RuntimeError("Expected one public H1")
    text = plain(source)
    if TITLE not in text or DISCLOSURE not in text:
        raise RuntimeError("Title or disclosure missing")
    for marker in ("Wagner HT1000", "BLACK+DECKER HG1300", "DEWALT D26950"):
        if marker not in text:
            raise RuntimeError(f"Missing product: {marker}")
    if "How We Tested" in text or "Milwaukee 2688-20 M12" in text:
        raise RuntimeError("Old fabricated testing or product description remains")
    if source.count(TAG) < 3:
        raise RuntimeError("Missing tagged Amazon searches")
    if meta["canonical"] != url:
        raise RuntimeError("Canonical changed")
    return meta


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    products = {"Wagner HT1000", "BLACK+DECKER HG1300", "DEWALT D26950"}
    findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=products)
    if any(item["severity"] == "BLOCK" for item in findings):
        raise RuntimeError(f"Validator blocked release: {findings}")
    baseline = next(post for post in json.loads(SNAPSHOT.read_text(encoding="utf-8"))["posts"] if post["slug"] == SLUG)
    current = api(f"/wp/v2/posts/{POST_ID}?context=edit")
    if current["id"] != POST_ID or current["slug"] != SLUG or current["status"] != "publish":
        raise RuntimeError("Post identity/status changed")
    if current["modified"] != baseline["modified"] or current["content"]["rendered"] != baseline["content"]["rendered"]:
        raise RuntimeError("Post changed since snapshot; re-review before editing")
    old_meta = public_meta(fetch_html(current["link"]))
    if old_meta["canonical"] != current["link"]:
        raise RuntimeError("Baseline canonical changed")
    print(json.dumps({"mode": MODE, "post": SLUG, "old_title": plain(current["title"]["rendered"]), "new_title": TITLE, "old_meta": old_meta, "validator": findings}, ensure_ascii=False))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps({"post": current, "public_meta": old_meta}, ensure_ascii=False, indent=2), encoding="utf-8")
    (BACKUP / "release.json").write_text(json.dumps({"new_title": TITLE, "new_seo_title": SEO_TITLE, "new_description": DESCRIPTION, "url": current["link"]}, indent=2), encoding="utf-8")
    try:
        result = api(f"/wp/v2/posts/{POST_ID}", {"title": TITLE, "content": CONTENT})
        if result.get("id") != POST_ID:
            raise RuntimeError("WordPress update not acknowledged")
        api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": POST_ID, "meta": {"rank_math_title": SEO_TITLE, "rank_math_description": DESCRIPTION}})
        for attempt in range(4):
            try:
                live = check_public(current["link"])
                if SEO_TITLE not in live["title"] or live["description"] != DESCRIPTION:
                    raise RuntimeError(f"SEO metadata not updated: {live}")
                print("Public verification passed:", json.dumps(live, ensure_ascii=False))
                return
            except RuntimeError:
                if attempt == 3:
                    raise
                time.sleep(3)
    except Exception:
        print("Release failed; attempting rollback of heat-gun article", flush=True)
        api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": POST_ID, "meta": {"rank_math_title": old_meta["title"].removesuffix(" - HandyTested"), "rank_math_description": old_meta["description"]}})
        api(f"/wp/v2/posts/{POST_ID}", {"title": current["title"]["raw"], "content": current["content"]["raw"]})
        raise


if __name__ == "__main__":
    main()
