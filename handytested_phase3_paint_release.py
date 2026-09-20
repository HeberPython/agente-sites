"""One-post, revision-guarded paint-sprayer correction via WordPress REST."""

from __future__ import annotations

import base64
import html
import json
import os
from pathlib import Path
import re
import time
import urllib.request

from handytested_editorial_validator import validate
from handytested_phase3_review import DISCLOSURE, TAG
from handytested_public_audit import BASE, fetch_html, plain


SLUG = "top-5-home-diy-paint-sprayers-under-300-in-2025"
TITLE = "Paint Sprayers for DIY Projects: Wagner vs Graco"
SEO_TITLE = TITLE + " | HandyTested"
DESCRIPTION = (
    "Compare the Wagner FLEXiO 590 and Graco TrueCoat 360 Dual Speed using "
    "manufacturer documentation. See key differences, trade-offs and buying checks."
)
ID = 87
CONTENT = Path(__file__).with_name("handytested_phase3_paint.html").read_text(encoding="utf-8")
SOURCE = Path(__file__).with_name("handytested_sources") / "verified-paint-sprayers.md"
SNAPSHOT = Path(__file__).with_name("handytested_sources") / "public_snapshot.json"
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase3-paint-backup"))
MODE = os.environ.get("MODE", "dry-run")


def api(path: str, payload: dict | None = None) -> dict:
    token = base64.b64encode(f"hebergravano@gmail.com:{os.environ['HT_WP_PASS']}".encode()).decode()
    request = urllib.request.Request(
        BASE + "/wp-json" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        method="POST" if payload is not None else "GET",
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json", "User-Agent": "HandyTested Phase 3 narrow release"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def public_meta(source: str) -> dict[str, str]:
    title = re.search(r"<title[^>]*>(.*?)</title>", source, re.I | re.S)
    description = re.search(r'<meta\b[^>]*name=["\']description["\'][^>]*>', source, re.I)
    value = re.search(r'content=["\']([^"\']+)["\']', description.group(), re.I) if description else None
    canonical = re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>', source, re.I)
    url = re.search(r'href=["\']([^"\']+)["\']', canonical.group(), re.I) if canonical else None
    return {"title": html.unescape(title.group(1).strip()) if title else "", "description": html.unescape(value.group(1)) if value else "", "canonical": url.group(1) if url else ""}


def check_public(url: str) -> dict[str, str]:
    source = fetch_html(url)
    meta = public_meta(source)
    if len(re.findall(r"<h1\b", source, re.I)) != 1:
        raise RuntimeError("Expected exactly one public H1")
    if TITLE not in plain(source) or DISCLOSURE not in plain(source):
        raise RuntimeError("Title or disclosure missing from public page")
    if "Cordless Paint Sprayer" in source or "we tested each paint sprayer" in source.lower():
        raise RuntimeError("Old product or test claim remains in public page")
    if source.count(TAG) < 2:
        raise RuntimeError("Expected two tagged Amazon search links")
    if meta["canonical"] != url:
        raise RuntimeError(f"Canonical changed unexpectedly: {meta['canonical']}")
    return meta


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products={"Wagner FLEXiO 590", "Graco 26D281"})
    if any(item["severity"] == "BLOCK" for item in findings):
        raise RuntimeError(f"Validator blocked release: {findings}")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    baseline = next(post for post in snapshot["posts"] if post["slug"] == SLUG)
    current = api(f"/wp/v2/posts/{ID}?context=edit")
    if current["id"] != ID or current["slug"] != SLUG or current["status"] != "publish":
        raise RuntimeError("Post identity/status changed")
    if current["modified"] != baseline["modified"]:
        raise RuntimeError("Post changed after snapshot; re-review before editing")
    if current["content"]["rendered"] != baseline["content"]["rendered"]:
        raise RuntimeError("Rendered content changed after snapshot; re-review before editing")
    old_meta = public_meta(fetch_html(current["link"]))
    if old_meta["canonical"] != current["link"]:
        raise RuntimeError("Baseline canonical is not self-referencing")
    print(json.dumps({"mode": MODE, "post": SLUG, "old_title": plain(current["title"]["rendered"]), "new_title": TITLE, "old_meta": old_meta, "validator": findings}, ensure_ascii=False))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps({"post": current, "public_meta": old_meta}, ensure_ascii=False, indent=2), encoding="utf-8")
    (BACKUP / "release.json").write_text(json.dumps({"new_title": TITLE, "new_seo_title": SEO_TITLE, "new_description": DESCRIPTION, "url": current["link"]}, indent=2), encoding="utf-8")
    meta_changed = False
    try:
        result = api(f"/wp/v2/posts/{ID}", {"title": TITLE, "content": CONTENT})
        if result.get("id") != ID:
            raise RuntimeError("WordPress update not acknowledged")
        result = api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": ID, "meta": {"rank_math_title": SEO_TITLE, "rank_math_description": DESCRIPTION}})
        print("Rank Math response:", json.dumps(result, ensure_ascii=False)[:500])
        meta_changed = True
        for attempt in range(4):
            try:
                live = check_public(current["link"])
                if SEO_TITLE not in live["title"] or live["description"] != DESCRIPTION:
                    raise RuntimeError(f"SEO metadata not updated: {live}")
                print("Public verification passed:", json.dumps(live, ensure_ascii=False))
                break
            except RuntimeError:
                if attempt == 3:
                    raise
                time.sleep(3)
    except Exception:
        print("Release failed; attempting rollback of this article only", flush=True)
        if meta_changed:
            api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": ID, "meta": {"rank_math_title": old_meta["title"].removesuffix(" - HandyTested"), "rank_math_description": old_meta["description"]}})
        api(f"/wp/v2/posts/{ID}", {"title": current["title"]["raw"], "content": current["content"]["raw"]})
        raise


if __name__ == "__main__":
    main()
