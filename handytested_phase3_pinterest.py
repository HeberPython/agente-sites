"""Set only Rank Math noindex on the Pinterest OAuth callback page."""

from __future__ import annotations

from html.parser import HTMLParser
import json
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET

from handytested_phase3_paint_release import api
from handytested_public_audit import BASE, fetch_html


ID = 39
URL = BASE + "/pinterest-connect/"
MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase3-pinterest-backup"))


class RobotsMeta(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.value = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "meta":
            values = dict(attrs)
            if values.get("name", "").lower() == "robots":
                self.value = values.get("content") or ""


def robots(source: str) -> str:
    parser = RobotsMeta()
    parser.feed(source)
    return parser.value


def in_sitemap() -> bool:
    root = ET.fromstring(fetch_html(BASE + "/page-sitemap.xml"))
    return URL in {item.text for item in root.iter() if item.tag.endswith("loc")}


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    page = api(f"/wp/v2/pages/{ID}?context=edit")
    if page["id"] != ID or page["slug"] != "pinterest-connect" or page["status"] != "publish":
        raise RuntimeError("Pinterest page identity changed")
    if "[" not in page["content"]["raw"]:
        raise RuntimeError("Expected callback shortcode; do not proceed without inspecting page")
    source = fetch_html(URL)
    before = robots(source)
    print(json.dumps({"mode": MODE, "page_id": ID, "robots_before": before, "in_sitemap_before": in_sitemap(), "shortcode_preserved": True}))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps({"page": page, "robots_before": before}, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = False
    try:
        result = api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": ID, "meta": {"rank_math_robots": ["noindex", "follow"]}})
        print("Rank Math response:", json.dumps(result, ensure_ascii=False)[:500])
        changed = True
        for attempt in range(4):
            current = fetch_html(URL)
            if "noindex" in robots(current).lower():
                after_page = api(f"/wp/v2/pages/{ID}?context=edit")
                if after_page["content"]["raw"] != page["content"]["raw"]:
                    raise RuntimeError("Callback content changed unexpectedly")
                print(json.dumps({"robots_after": robots(current), "in_sitemap_after": in_sitemap(), "callback_page_200": True, "shortcode_unchanged": True}))
                return
            if attempt < 3:
                time.sleep(3)
        raise RuntimeError("Public robots did not show noindex")
    except Exception:
        if changed:
            previous = [item.strip() for item in before.split(",") if item.strip()] or ["index", "follow"]
            api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": ID, "meta": {"rank_math_robots": previous}})
        raise


if __name__ == "__main__":
    main()
