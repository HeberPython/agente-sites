"""Revision-guarded WordPress release for digital torque wrenches."""
from __future__ import annotations
import json, os, re, time
from pathlib import Path
from handytested_editorial_validator import validate
from handytested_phase3_paint_release import api, public_meta
from handytested_phase3_review import DISCLOSURE, TAG
from handytested_public_audit import fetch_html, plain

ROOT = Path(__file__).parent
SLUG = "top-5-digital-torque-wrenches-under-100-for-accurate-torque"
POST_ID = 62
TITLE = "3/8-Inch Digital Torque Wrenches by Range and Alert"
SEO_TITLE = TITLE + " | HandyTested"
DESCRIPTION = "Compare GEARWRENCH 85076, ACDelco ARM601-3 and CRAFTSMAN CMMT99435 by range, accuracy conditions, alerts and calibration limits."
CONTENT = (ROOT / "handytested_phase4_digital_torque_wrenches.html").read_text(encoding="utf-8")
SOURCE = ROOT / "handytested_sources" / (SLUG + ".md")
SNAPSHOT = ROOT / "handytested_sources" / "public_snapshot.json"
MODE = os.getenv("MODE", "dry-run")
BACKUP = Path(os.getenv("BACKUP_DIR", "handytested-phase4-digital-torque-backup"))
PRODUCTS = {"GEARWRENCH 85076", "ACDelco ARM601-3", "CRAFTSMAN CMMT99435"}
RELATED = ("/best-cordless-ratchets-for-diy-mechanics-in-2025/", "/best-cordless-impact-wrenches-under-300-for-2025/")

def check_public(url: str) -> dict[str, str]:
    source = fetch_html(url); meta = public_meta(source); body = plain(source)
    if len(re.findall(r"<h1\b", source, re.I)) != 1 or TITLE not in body or DISCLOSURE not in body: raise RuntimeError("Public title/H1 or disclosure missing")
    if not all(p in body for p in PRODUCTS): raise RuntimeError("Documented product missing")
    if source.count(TAG) < 3 or meta["canonical"] != url: raise RuntimeError("Tagged links or canonical missing")
    if not all(p in source for p in RELATED): raise RuntimeError("Related guide missing")
    return meta

def main() -> None:
    if MODE not in {"dry-run", "apply"}: raise ValueError("MODE must be dry-run or apply")
    findings = validate(TITLE, CONTENT, source_record=SOURCE, verified_products=PRODUCTS)
    if any(i["severity"] == "BLOCK" for i in findings): raise RuntimeError(f"Validator blocked release: {findings}")
    baseline = next(p for p in json.loads(SNAPSHOT.read_text(encoding="utf-8"))["posts"] if p["slug"] == SLUG)
    current = api(f"/wp/v2/posts/{POST_ID}?context=edit")
    if current["id"] != POST_ID or current["slug"] != SLUG or current["status"] != "publish": raise RuntimeError("Post identity/status changed")
    if current["modified"] != baseline["modified"] or current["content"]["rendered"] != baseline["content"]["rendered"] or current["title"]["raw"] != plain(baseline["title"]["rendered"]): raise RuntimeError("Post changed since snapshot; re-review before editing")
    old_meta = public_meta(fetch_html(current["link"]))
    if old_meta["canonical"] != current["link"]: raise RuntimeError("Baseline canonical changed")
    print(json.dumps({"mode": MODE, "post": SLUG, "old_title": plain(current["title"]["rendered"]), "new_title": TITLE, "old_meta": old_meta, "validator": findings}, ensure_ascii=False))
    if MODE == "dry-run": return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps({"post": current, "public_meta": old_meta}, ensure_ascii=False, indent=2), encoding="utf-8")
    (BACKUP / "release.json").write_text(json.dumps({"new_title": TITLE, "new_seo_title": SEO_TITLE, "new_description": DESCRIPTION, "url": current["link"]}, indent=2), encoding="utf-8")
    try:
        result = api(f"/wp/v2/posts/{POST_ID}", {"title": TITLE, "content": CONTENT})
        if result.get("id") != POST_ID: raise RuntimeError("WordPress update not acknowledged")
        api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": POST_ID, "meta": {"rank_math_title": SEO_TITLE, "rank_math_description": DESCRIPTION}})
        for attempt in range(4):
            try:
                live = check_public(current["link"])
                if SEO_TITLE not in live["title"] or live["description"] != DESCRIPTION: raise RuntimeError(f"SEO metadata not updated: {live}")
                print("Public verification passed:", json.dumps(live, ensure_ascii=False)); return
            except RuntimeError:
                if attempt == 3: raise
                time.sleep(3)
    except Exception:
        api("/rankmath/v1/updateMeta", {"objectType": "post", "objectID": POST_ID, "meta": {"rank_math_title": old_meta["title"], "rank_math_description": old_meta["description"]}})
        api(f"/wp/v2/posts/{POST_ID}", {"title": current["title"]["raw"], "content": current["content"]["raw"]}); raise

if __name__ == "__main__": main()
