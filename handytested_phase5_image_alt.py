"""Guarded alt text for visibly relevant existing featured images."""

from __future__ import annotations

import json
import os
from pathlib import Path

from handytested_phase2 import request


MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-image-alt-backup"))
INVENTORY = json.loads(Path(__file__).with_name("HANDYTESTED_PHASE5_IMAGES.json").read_text(encoding="utf-8"))
ALT = {
    174: "Kitchen counter with appliances and fresh produce.",
    172: "Smart door lock beside a smartphone.",
    170: "Modern kitchen with appliances and a countertop.",
    167: "Smart door lock beside a smartphone.",
    155: "White projector on a shelf near a wall outlet.",
    142: "Interior room under renovation with exposed framing.",
    140: "Green camping tent at a wooded campsite.",
    137: "Bright kitchen with cookware and a countertop.",
    71: "Over-ear headphones beside audio equipment.",
    58: "Circular saw beside stacked firewood.",
    52: "Digital multimeter with probes in front of a computer screen.",
    49: "Handheld electrical tester and battery pack on a white background.",
    46: "Rotary tool being used to shape a piece of wood.",
    40: "Smart displays showing information in a dim room.",
    30: "Green laser line projected onto a tiled wall.",
    27: "Oscillating multi-tool and accessories against a wall.",
    19: "Yellow and black cordless drill on a workbench.",
}


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    expected = {row["media_id"]: row for row in INVENTORY}
    originals = {}
    for media_id in ALT:
        row = expected[media_id]
        current = request(f"/media/{media_id}?context=edit")
        if current["id"] != media_id or current["source_url"] != row["url"] or current["alt_text"] != "":
            raise RuntimeError(f"Media {media_id} changed since visual audit")
        originals[media_id] = current
    print(json.dumps({"mode": MODE, "alt_updates": len(ALT)}))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "original.json").write_text(json.dumps(originals, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = []
    try:
        for media_id, alt in ALT.items():
            result = request(f"/media/{media_id}", {"alt_text": alt})
            if result.get("id") != media_id:
                raise RuntimeError(f"Media {media_id} update not acknowledged")
            changed.append(media_id)
            public = request(f"/media/{media_id}?_fields=id,alt_text")
            if public["alt_text"] != alt:
                raise RuntimeError(f"Media {media_id} alt not publicly verified")
        print("Published and publicly verified 17 descriptive alt texts")
    except Exception:
        for media_id in reversed(changed):
            request(f"/media/{media_id}", {"alt_text": originals[media_id]["alt_text"]})
        raise


if __name__ == "__main__":
    main()
