"""Guarded replacement of four stale DEWALT PDF citations with exact product pages."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re

from handytested_phase2 import request


MODE = os.environ.get("MODE", "dry-run")
BACKUP = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-citation-backup"))
POST_ID = int(os.environ.get("POST_ID", "0"))
REPAIRS = (
    (
        56,
        "2026-09-21T21:44:42",
        '<a href="https://www.dewalt.com/GLOBALBOM/QU/D26960/10/Instruction_Manual/EN/N888399_D26950_NA.pdf" target="_blank" rel="noopener">manual</a>',
        '<a href="https://www.dewalt.com/en-us/product/d26950/heat-gun" target="_blank" rel="noopener">product page with manual</a>',
    ),
    (
        20,
        "2026-09-21T21:44:57",
        '<a href="https://www.dewalt.com/GLOBALBOM/QU/DCD771C2/2/Instruction_Manual/EN/N457137_DCD771.pdf" target="_blank" rel="noopener">DEWALT DCD771 manual</a>',
        '<a href="https://www.dewalt.com/en-us/product/dcd771c2/20v-max-compact-drilldriver-kit" target="_blank" rel="noopener">DEWALT DCD771C2 product page with manual</a>',
    ),
    (
        143,
        "2026-09-21T21:44:26",
        '<a href="https://www.dewalt.com/GLOBALBOM/QU/DCN680B/1/Instruction_Manual/EN/N496636_DCN680.pdf" target="_blank" rel="noopener">manual</a>',
        '<a href="https://www.dewalt.com/en-us/product/dcn680b/20v-max-xr-18ga-cordless-brad-nailer-tool-only" target="_blank" rel="noopener">product page with manual</a>',
    ),
    (
        59,
        "2026-09-21T21:44:41",
        '<a href="https://www.dewalt.com/GLOBALBOM/QU/DCS570B/1/Instruction_Manual/EN/N490072_DCS570.pdf" target="_blank" rel="noopener">DEWALT circular-saw safety manual</a>',
        '<a href="https://www.dewalt.com/en-us/product/dcs565b/20v-max-xr-6-12-brushless-cordless-circular-saw-tool-only" target="_blank" rel="noopener">DEWALT DCS565B product page with manual</a>',
    ),
)


def anchor_parts(anchor: str) -> tuple[str, str]:
    match = re.search(r'href="([^"]+)"[^>]*>([^<]+)</a>', anchor)
    if not match:
        raise ValueError("Invalid configured anchor")
    return match.group(1), match.group(2)


def replace_anchor(raw: str, old: str, new: str) -> str:
    old_url, old_label = anchor_parts(old)
    new_url, new_label = anchor_parts(new)
    pattern = re.compile(
        r'(<a\b[^>]*\bhref=")' + re.escape(old_url) + r'("[^>]*>)'
        + re.escape(old_label) + r'(</a>)'
    )
    if len(pattern.findall(raw)) != 1:
        raise RuntimeError(f"Citation anchor changed for {old_url}")
    updated = pattern.sub(
        lambda match: match.group(1) + new_url + match.group(2) + new_label + match.group(3),
        raw,
        count=1,
    )
    if old_url in updated or updated.count(new_url) != raw.count(new_url) + 1:
        raise RuntimeError(f"Citation replacement failed for {old_url}")
    return updated


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    selected = [row for row in REPAIRS if row[0] == POST_ID]
    if len(selected) != 1:
        raise ValueError("POST_ID must identify exactly one configured post")
    originals: dict[int, dict] = {}
    replacements: dict[int, str] = {}
    for post_id, modified, old, new in selected:
        post = request(f"/posts/{post_id}?context=edit")
        raw = post["content"]["raw"]
        if post["id"] != post_id or post["status"] != "publish" or post["modified_gmt"] != modified:
            raise RuntimeError(f"Post {post_id} revision/status changed")
        updated = replace_anchor(raw, old, new)
        if updated.count("handytested0d-20") != raw.count("handytested0d-20") or "As an Amazon Associate I earn from qualifying purchases." not in updated:
            raise RuntimeError(f"Post {post_id} commercial safeguards changed")
        originals[post_id] = post
        replacements[post_id] = updated
    print(json.dumps({"mode": MODE, "post_ids": list(replacements)}))
    if MODE == "dry-run":
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "originals.json").write_text(json.dumps(originals, ensure_ascii=False, indent=2), encoding="utf-8")
    post_id, _, old, new = selected[0]
    result = request(f"/posts/{post_id}", {"content": replacements[post_id]})
    if result.get("id") != post_id:
        raise RuntimeError(f"Post {post_id} update not acknowledged; inspect live state before retry")
    rendered = result["content"]["rendered"]
    old_url, _ = anchor_parts(old)
    new_url, new_label = anchor_parts(new)
    if result["status"] != "publish" or old_url in rendered or new_url not in rendered or new_label not in rendered:
        raise RuntimeError(f"Post {post_id} update response failed validation; inspect live state before retry")
    print(f"Published post {post_id}; independent public validation still required")


if __name__ == "__main__":
    main()
