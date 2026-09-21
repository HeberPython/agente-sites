"""Guarded Phase 5 excerpt refresh and curated homepage synchronization."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time

from handytested_phase2 import TOP_SLUGS, home_html, request
from handytested_public_audit import fetch


EXPECTED_DIGEST = "fd8d854b3e156f99521fa14627ad5cb74f2716e6507e23d25faaf8822f3652f0"
EXPECTED_HOME_MODIFIED = "2026-09-20T13:51:50"
MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-excerpts-backup"))

# Editorial summaries describe the current article's decision, not the old slug.
EXCERPTS = {
    187: "Compare two robot vacuums for pet hair by floor type, navigation and maintenance needs. See where a self-emptying dock helps and where it does not.",
    185: "Compare three countertop hydroponic gardens by pod capacity, lighting and upkeep. Find a setup that fits your kitchen and growing routine.",
    183: "Compare a portable propane grill with a charcoal option for camping. Choose by fuel access, cooking space, transport and site rules.",
    181: "Compare corded and cordless electric mowers for small yards. Check runtime, cord reach, cutting width and what comes in each package.",
    179: "Compare premium earbuds from Apple, Samsung and Bose by phone compatibility, noise control, fit and charging needs.",
    175: "Compare three blenders for smoothies by jar size, power claims, cleanup and countertop space. Find the right fit for your routine.",
    173: "Explore four starting points for smart-home automation, from hubs to devices. Compare ecosystem fit, protocols and setup trade-offs.",
    171: "Compare kitchen tools for preparation, temperature checks and food storage. Choose by task, space and maintenance rather than gadget count.",
    168: "Compare smart-home devices for the front door, HVAC and outlets. Check compatibility, subscriptions and installation before choosing.",
    164: "Compare outdoor furniture bracket kits with a ready-made storage bench. See what requires separate lumber, assembly and weather care.",
    159: "Compare compact and mid-torque cordless impact wrenches by drive size, battery platform and package contents for garage work.",
    156: "Compare home projectors by native resolution, brightness claims and setup needs. Match the display to your room and source devices.",
    150: "Compare ergonomic office chairs by adjustability, seat fit and support. Use the guide to narrow choices for your desk setup.",
    146: "Compare spot and whole-room carpet cleaners for pet messes. Choose by cleaning area, extraction method, storage and drying needs.",
    143: "Compare cordless brad nailers for trim by battery system, kit contents and safety controls. Find a fit for your project volume.",
    141: "Compare a tent, two-burner stove and compact chair for car camping. Prioritize campsite fit, packing space and safe stove use.",
    138: "Compare kitchen appliances for pressure cooking, blending and coffee. Choose the job you need done and check package details.",
    136: "Compare home security cameras by location, power and recording needs. Check subscriptions and installation limits before buying.",
    90: "Compare household, drill-and-driver and mechanics tool sets by project type. Check included pieces and battery platform before choosing.",
    87: "Compare Wagner and Graco paint sprayers for DIY projects by paint compatibility, setup and cleanup. Check the exact model before buying.",
    84: "Compare cordless ratchets by battery system, drive size and package contents. Find a practical fit for access and fastening work.",
    81: "Compare 4V electric screwdrivers for household assembly by grip, bits, charging and torque control. Choose for the tasks you repeat.",
    78: "Compare 50-inch smart TVs by platform, picture support and inputs. Check room fit and gaming limits before choosing a model.",
    72: "Compare noise-canceling headphones by travel priority, comfort, battery and wired-use limits. Find a fit for your listening habits.",
    69: "Compare three home drill presses by swing, speed range and bench space. Check the exact machine and accessories for your workshop.",
    62: "Compare 3/8-inch digital torque wrenches by range, alerts and calibration guidance. Match the tool to the fasteners you work on.",
    59: "Compare 6-1/2-inch cordless circular saws by battery platform, blade capacity and kit contents for home and workshop cuts.",
    56: "Compare three heat guns for DIY work by temperature control, airflow and included accessories. Check the material before applying heat.",
    53: "Compare multimeters for home electrical troubleshooting by measurement range, safety category and display. Know when to call an electrician.",
    50: "Compare non-contact voltage testers by detection range and controls. Understand their limits before any electrical work.",
    47: "Compare rotary tools for general DIY and detail work by speed, accessory system and handling. Match the kit to your projects.",
    44: "Compare stud finders for drywall layout by detection method, depth and AC warnings. Confirm placement before drilling.",
    41: "Compare Alexa, Google Home and SmartThings hubs by ecosystem, device support and setup needs. Choose the platform that fits your home.",
    37: "Compare three random orbital sanders for DIY by power source, dust collection and handling. Find a fit for furniture or wall prep.",
    31: "Compare cross-line and manual laser levels by beam visibility, leveling method and mounting needs for home layout projects.",
    28: "Compare oscillating multi-tools by power source, blade fit and kit contents. Choose for cutting, scraping or sanding tasks.",
    25: "Compare three wireless earbuds by fit, battery, controls and phone compatibility. Check current pricing before choosing a budget pair.",
    20: "Compare three cordless drill kits for home DIY by chuck, speed, included batteries and tool platform. Find the package that fits your projects.",
}


def digest(posts: list[dict]) -> str:
    fields = ("id", "slug", "modified", "excerpt")
    data = [{key: post[key] for key in fields} for post in posts]
    raw = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def public_posts() -> list[dict]:
    posts = fetch("/wp-json/wp/v2/posts?per_page=100&_fields=id,slug,modified,excerpt")
    if not isinstance(posts, list) or len(posts) != len(EXCERPTS):
        raise RuntimeError("Published post inventory changed")
    return posts


def verify_excerpt(post_id: int, excerpt: str) -> None:
    for attempt in range(5):
        public = fetch(f"/wp-json/wp/v2/posts/{post_id}?_fields=excerpt")
        if excerpt in public["excerpt"]["rendered"]:
            return
        time.sleep(3)
    raise RuntimeError(f"Excerpt {post_id} not visible in public REST")


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    posts = public_posts()
    if digest(posts) != EXPECTED_DIGEST or {p["id"] for p in posts} != set(EXCERPTS):
        raise RuntimeError("Posts changed since Phase 5 baseline; review before release")
    home = request("/pages?slug=home-page&context=edit&_fields=id,slug,status,modified,content")
    if len(home) != 1 or home[0]["id"] != 18 or home[0]["status"] != "publish" or home[0]["modified"] != EXPECTED_HOME_MODIFIED:
        raise RuntimeError("Homepage changed since Phase 5 baseline")
    originals = {}
    for post in posts:
        current = request(f"/posts/{post['id']}?context=edit&_fields=id,slug,status,modified,excerpt")
        if current["status"] != "publish" or current["slug"] != post["slug"] or current["modified"] != post["modified"] or current["excerpt"]["rendered"] != post["excerpt"]["rendered"]:
            raise RuntimeError(f"Post {post['id']} changed during preflight")
        originals[post["id"]] = current
    print(json.dumps({"mode": MODE, "posts": len(posts), "home": 18, "top_slugs": TOP_SLUGS}))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps({"home": home[0], "posts": originals}, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = []
    home_changed = False
    try:
        for post in posts:
            post_id = post["id"]
            result = request(f"/posts/{post_id}", {"excerpt": EXCERPTS[post_id]})
            if result.get("id") != post_id:
                raise RuntimeError(f"Post {post_id} update not acknowledged")
            changed.append(post_id)
            verify_excerpt(post_id, EXCERPTS[post_id])
        categories = request("/categories?per_page=100&_fields=id,slug,count")
        top_posts = [request(f"/posts?slug={slug}&_embed=1")[0] for slug in TOP_SLUGS]
        content = home_html(categories, top_posts)
        if any(EXCERPTS[p["id"]][:40] not in content for p in top_posts):
            raise RuntimeError("Homepage cards did not use current excerpts")
        result = request("/pages/18", {"content": content})
        if result.get("id") != 18:
            raise RuntimeError("Homepage update not acknowledged")
        home_changed = True
        live = fetch("/wp-json/wp/v2/pages/18?_fields=content")
        if "We tested three solid options" in live["content"]["rendered"]:
            raise RuntimeError("Stale homepage card still public")
        for post_id in (20, 37, 41):
            if EXCERPTS[post_id][:40] not in live["content"]["rendered"]:
                raise RuntimeError(f"Homepage card {post_id} not public")
        print("Published and verified 38 excerpts and 3 curated homepage cards")
    except Exception:
        if home_changed:
            request("/pages/18", {"content": home[0]["content"]["raw"]})
        for post_id in reversed(changed):
            request(f"/posts/{post_id}", {"excerpt": originals[post_id]["excerpt"]["raw"]})
        raise


if __name__ == "__main__":
    main()
