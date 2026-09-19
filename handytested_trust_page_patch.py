"""Narrow, idempotent WordPress trust-page corrections.

Dry-run is the default. APPLY=1 writes the five named pages after backing up
their existing raw content. WordPress also retains page revisions.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request


BASE = "https://handytested.com/wp-json/wp/v2"
USER = "hebergravano@gmail.com"
PASSWORD = os.environ["HT_WP_PASS"]
APPLY = os.environ.get("APPLY", "0") == "1"
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "handytested-page-backup"))
PAGES = ("about", "deals", "how-we-review", "editorial-policy", "affiliate-disclosure")
ASSOCIATE_STATEMENT = "As an Amazon Associate I earn from qualifying purchases."


def request(endpoint: str, payload: dict | None = None) -> object:
    token = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + endpoint,
        data=data,
        method="POST" if payload is not None else "GET",
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "HandyTested trust page patch",
        },
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.load(response)


def replace_once(content: str, old: str, new: str, slug: str) -> str:
    if old in content:
        return content.replace(old, new, 1)
    if new in content:
        return content
    raise ValueError(f"Unexpected {slug} content; expected text missing")


def revise(slug: str, content: str) -> str:
    content = re.sub(r"<h1(?:\s[^>]*)?>.*?</h1>\s*", "", content, count=1, flags=re.I | re.S)
    if slug == "how-we-review":
        content = replace_once(
            content,
            "Some articles are based on direct hands-on evaluation. Others are research-led buying guides built from specifications, verified owner feedback, seller signals, and category expertise. We do not claim physical testing unless it actually happened.",
            "Our buying guides are based on research and comparison of available specifications, manufacturer information, and publicly available buyer feedback. We identify physical testing only when it is documented in the individual article.",
            slug,
        )
    elif slug == "affiliate-disclosure":
        content = replace_once(
            content,
            "As an Amazon Associate, we earn from qualifying purchases.",
            ASSOCIATE_STATEMENT,
            slug,
        )
    elif slug == "deals":
        content = replace_once(
            content,
            "As an Amazon Associate, HandyTested earns from qualifying purchases.",
            ASSOCIATE_STATEMENT,
            slug,
        )
    return content


def main() -> None:
    changes: list[tuple[dict, str, str]] = []
    for slug in PAGES:
        query = urllib.parse.urlencode({"slug": slug, "context": "edit", "_fields": "id,slug,content,status"})
        pages = request(f"/pages?{query}")
        if not isinstance(pages, list) or len(pages) != 1:
            raise RuntimeError(f"Expected one page for {slug}, found {len(pages) if isinstance(pages, list) else 'invalid'}")
        page = pages[0]
        original = page["content"]["raw"]
        updated = revise(slug, original)
        print(f"{slug}: {'change' if updated != original else 'already current'}")
        if updated != original:
            changes.append((page, original, updated))

    if not APPLY:
        print(f"Dry-run: {len(changes)} page(s) would change")
        return
    if not changes:
        print("No changes needed")
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for page, original, _ in changes:
        path = BACKUP_DIR / f"{page['slug']}-{page['id']}.json"
        path.write_text(json.dumps({"id": page["id"], "slug": page["slug"], "status": page["status"], "content": original}, ensure_ascii=False, indent=2), encoding="utf-8")

    for page, _, updated in changes:
        request(f"/pages/{page['id']}", {"content": updated})
        print(f"Updated {page['slug']} ({page['id']})")


if __name__ == "__main__":
    main()
