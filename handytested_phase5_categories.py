"""Guarded updates to descriptions of populated HandyTested categories."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

from handytested_phase2 import request
from handytested_public_audit import fetch_html, plain


MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-categories-backup"))
EXPECTED = {
    11: ("cleaning", "Vacuums, cleaning tools, laundry gear, and home maintenance products."),
    4: ("diy", "Guides, product recommendations, and tips for DIY projects and home improvement."),
    2: ("electronics", "Reviews and comparisons of consumer electronics, gadgets, and tech accessories."),
    9: ("kitchen", "Kitchen tools, small appliances, cookware, and useful home food prep gear."),
    12: ("office-gear", "Home office equipment, desk accessories, printers, monitors, and productivity gear."),
    10: ("outdoor", "Outdoor, lawn, garden, camping, and backyard gear reviews."),
    8: ("smart-home", "Smart home devices, home automation, security, and connected living gear."),
    3: ("tools", "Reviews of power tools, hand tools, and workshop equipment."),
}
NEW = {
    11: "Compare robot vacuums and carpet cleaners by floor type, mess type, upkeep and storage. Know when a spot cleaner or whole-room extractor makes sense.",
    4: "Research-led guides for home projects, from paint prep to furniture builds. Compare the work involved, required accessories and trade-offs before choosing gear.",
    2: "Compare earbuds, headphones, TVs, projectors and measurement tech by compatibility, features and setup. Check current listings for availability.",
    9: "Compare blenders, countertop appliances and prep tools by task, capacity and cleanup. Choose the exact tool your kitchen needs.",
    12: "Choose an ergonomic office chair by seat fit, adjustability and workstation needs. Compare trade-offs without assuming one chair fits everyone.",
    10: "Compare portable grills and car-camping gear by fuel, packing space and site rules. Find equipment suited to your campsite or backyard.",
    8: "Explore hubs, connected devices and security cameras by ecosystem, protocols, subscriptions and installation. Start with the system already in your home.",
    3: "Compare drills, saws, sanders and measuring tools by exact model, power source, package and safety needs. Start with the guide that matches your project.",
}


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    current = {}
    for category_id, (slug, description) in EXPECTED.items():
        item = request(f"/categories/{category_id}?context=edit")
        if item["id"] != category_id or item["slug"] != slug or plain(item["description"]) != description or item["count"] < 1:
            raise RuntimeError(f"Category {category_id} changed or is empty")
        current[category_id] = item
    print(json.dumps({"mode": MODE, "categories": list(NEW)}, sort_keys=True))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = []
    try:
        for category_id, description in NEW.items():
            result = request(f"/categories/{category_id}", {"description": description})
            if result.get("id") != category_id:
                raise RuntimeError(f"Category {category_id} update not acknowledged")
            changed.append(category_id)
            url = current[category_id]["link"]
            for attempt in range(5):
                if description in plain(fetch_html(url)):
                    break
                if attempt == 4:
                    raise RuntimeError(f"Category {category_id} description not public")
                time.sleep(3)
        print("Published and verified eight category descriptions")
    except Exception:
        for category_id in reversed(changed):
            request(f"/categories/{category_id}", {"description": EXPECTED[category_id][1]})
        raise


if __name__ == "__main__":
    main()
