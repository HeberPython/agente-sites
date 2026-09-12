"""
Replace HandyTested Amazon affiliate tags inside WordPress post content.

This is intentionally narrow: it only replaces the exact old tag string with the
new tag string. It does not rewrite URLs, titles, or any other article content.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


WP_URL = "https://handytested.com"
WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]
OLD_TAG = os.environ.get("OLD_AMAZON_TAG", "amazonrev089f-20")
NEW_TAG = os.environ.get("NEW_AMAZON_TAG", os.environ.get("HT_AMAZON_TAG", "handytested0d-20"))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"


def wp_headers() -> dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "HandyTested affiliate tag replacement",
    }


def wp_json(endpoint: str, payload: dict | None = None) -> object:
    data = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2{endpoint}",
        data=data,
        method=method,
        headers=wp_headers(),
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_posts() -> list[dict]:
    posts: list[dict] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({
            "per_page": 100,
            "page": page,
            "status": "any",
            "context": "edit",
            "_fields": "id,slug,title,content,status",
        })
        try:
            batch = wp_json(f"/posts?{query}")
        except urllib.error.HTTPError as exc:
            if exc.code == 400 and page > 1:
                break
            raise
        if not isinstance(batch, list) or not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def main() -> int:
    if not OLD_TAG or not NEW_TAG:
        raise SystemExit("OLD_AMAZON_TAG and NEW_AMAZON_TAG/HT_AMAZON_TAG are required.")
    if OLD_TAG == NEW_TAG:
        raise SystemExit("Old and new Amazon tags are identical; nothing to replace.")

    scanned = 0
    updated = 0
    for post in iter_posts():
        scanned += 1
        raw_content = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered") or ""
        if OLD_TAG not in raw_content:
            continue
        new_content = raw_content.replace(OLD_TAG, NEW_TAG)
        title = post.get("title", {}).get("raw") or post.get("title", {}).get("rendered") or post.get("slug")
        print(f"{'DRY-RUN' if DRY_RUN else 'Updating'} post {post['id']} | {post.get('slug')} | {title}")
        if not DRY_RUN:
            wp_json(f"/posts/{post['id']}", {"content": new_content})
        updated += 1

    print(f"Scanned {scanned} posts; {'would update' if DRY_RUN else 'updated'} {updated}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
