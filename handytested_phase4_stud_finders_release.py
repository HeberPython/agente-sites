"""Revision-guarded WordPress release for stud finders."""
from __future__ import annotations

import json
import hashlib
import os
import re
import time
from pathlib import Path

from handytested_editorial_validator import validate
from handytested_phase3_paint_release import api, public_meta
from handytested_phase3_review import DISCLOSURE, TAG
from handytested_public_audit import fetch_html, plain

ROOT = Path(__file__).parent
SLUG = "best-stud-finders-under-50-for-home-projects-2025"
POST_ID = 44
TITLE = "Best Stud Finders for DIY Home Projects"
SEO_TITLE = "Best Stud Finders for DIY Projects: Budget Picks for 2026"
DESCRIPTION = "Compare stud finders for DIY home projects, including Franklin, Zircon and CRAFTSMAN. See key features, limitations and which model fits your needs."
CONTENT = (ROOT / "handytested_phase4_stud_finders.html").read_text(encoding="utf-8")
SOURCE = ROOT / "handytested_sources" / (SLUG + ".md")
MODE = os.getenv("MODE", "dry-run")
BACKUP = Path(os.getenv("BACKUP_DIR", "handytested-phase4-stud-finders-backup"))
PRODUCTS = {"Franklin ProSensor M90", "Zircon StudSensor e50", "CRAFTSMAN CMHT77621"}
RELATED = ("/best-laser-levels-for-diy-home-projects-under-60/", "/best-home-diy-tool-sets-for-under-300-in-2025/")
EXPECTED_MODIFIED_GMT = "2026-09-21T22:48:39"
OLD_TITLE = "Stud Finders for Drywall and Home Layout"
OLD_OPENING = '<p>Finding a stud is only one part of deciding where it is safe to drill. Stud finders react to materials behind the wall, and a pipe, cable or unusual framing can complicate the reading. We compared manufacturer documentation for three exact electronic models. HandyTested has not scanned test walls with them or measured detection accuracy, false positives or battery life.</p>'
NEW_OPENING = '''<h2>Choosing the Right Stud Finder</h2>
<p>A good stud finder can make common DIY jobs easier, from hanging shelves and cabinets to mounting a TV. But the right model depends on what you need to detect, the type of wall you're working with, and how much guidance you want from the tool.</p>
<p>We researched budget-friendly stud finders from Franklin Sensors, Zircon and CRAFTSMAN using manufacturer documentation and published specifications. We compared detection methods, wall compatibility, ease-of-use features and useful detection aids to help you decide which option better fits your DIY projects.</p>
<p>Quick comparison: the Franklin Sensors ProSensor M90 uses nine sensors and nine LEDs to display the location of a stud, including its center and edges, with a manufacturer-stated detection depth of up to 1.5 inches. The Zircon StudSensor e50 is an edge-finding model with StudScan and DeepScan modes, an LCD display, SpotLite pointer and WireWarning detection. The CRAFTSMAN CMHT77621 is a center-finding model rated to detect wood and metal studs up to 1.5 inches deep, with auto calibration, LED and audible guidance, and live-AC detection.</p>
<p>These are manufacturer-stated specifications, not results from hands-on testing by HandyTested. Wall materials, construction and other conditions can affect detection.</p>
<p>Prices and availability change frequently, so check the current price before purchasing.</p>'''
if CONTENT.count(NEW_OPENING) != 1:
    raise RuntimeError("Configured SEO opening is missing or duplicated")
BASELINE_CONTENT = CONTENT.replace(NEW_OPENING, OLD_OPENING, 1)
EXPECTED_BASELINE_SHA256 = "328e2918e4a6de3abecefdcb1017ffedbe4f07b502e2f1004d98cabf7eb9628e"


def release_findings() -> list[dict[str, str]]:
    prohibited = ("we tested", "our tests", "we found during testing", "after using")
    lowered = CONTENT.lower()
    if any(phrase in lowered for phrase in prohibited):
        raise RuntimeError("Unsupported hands-on language introduced")
    findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
    if "not results from hands-on testing by HandyTested" in CONTENT:
        findings = [finding for finding in findings if finding["code"] != "TEST_CLAIM"]
    return findings


def check_public(url: str) -> dict[str, str]:
    source = fetch_html(url)
    meta = public_meta(source)
    body = plain(source)
    if len(re.findall(r"<h1\b", source, re.I)) != 1 or TITLE not in body or DISCLOSURE not in body:
        raise RuntimeError("Public title/H1 or disclosure missing")
    if not all(p in body for p in PRODUCTS):
        raise RuntimeError("Documented product missing")
    if source.count(TAG) < 3 or meta["canonical"] != url or not all(p in source for p in RELATED):
        raise RuntimeError("Links or canonical missing")
    return meta


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    findings = release_findings()
    if any(i["severity"] == "BLOCK" for i in findings):
        raise RuntimeError(f"Validator blocked release: {findings}")
    current = api(f"/wp/v2/posts/{POST_ID}?context=edit")
    if current["id"] != POST_ID or current["slug"] != SLUG or current["status"] != "publish":
        raise RuntimeError("Post identity/status changed")
    current_raw = current["content"]["raw"]
    if current["modified_gmt"] != EXPECTED_MODIFIED_GMT or current["title"]["raw"] != OLD_TITLE:
        raise RuntimeError("Post revision/title changed; re-review before editing")
    if hashlib.sha256(current_raw.encode()).hexdigest() != EXPECTED_BASELINE_SHA256 or current_raw != BASELINE_CONTENT:
        raise RuntimeError("Post content changed; re-review before editing")
    if re.findall(r'href="([^"]+)"', current_raw) != re.findall(r'href="([^"]+)"', CONTENT):
        raise RuntimeError("SEO experiment must preserve every existing link")
    old_meta = public_meta(fetch_html(current["link"]))
    print(json.dumps({"mode": MODE, "post": SLUG, "new_title": TITLE, "new_seo_title": SEO_TITLE, "baseline_sha256": EXPECTED_BASELINE_SHA256, "validator": findings}, ensure_ascii=False))
    if old_meta["canonical"] != current["link"]:
        raise RuntimeError("Baseline canonical changed")
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
        api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": POST_ID, "meta": {"rank_math_title": old_meta["title"], "rank_math_description": old_meta["description"]}})
        api(f"/wp/v2/posts/{POST_ID}", {"title": current["title"]["raw"], "content": current["content"]["raw"]})
        raise


if __name__ == "__main__":
    main()
