"""Guarded homepage LCP image optimization for HandyTested.

The release changes only the existing decorative hero image delivery. MODE=dry-run
performs all read-only guards. MODE=apply stores the original page before writing
and rolls it back if the public verification fails.
"""

from __future__ import annotations

import base64
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


BASE = "https://handytested.com"
API = BASE + "/wp-json/wp/v2"
MODE = os.environ.get("MODE", "dry-run")
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "handytested-phase5-mobile-performance-backup"))
HOME_ID = 18
EXPECTED_POSTS = 38

IMAGE_ROOT = BASE + "/wp-content/uploads/2026/05/Best-Cordless-Drills-Under-100"
IMAGE_300 = IMAGE_ROOT + "-300x200.jpg"
IMAGE_768 = IMAGE_ROOT + "-768x512.jpg"
IMAGE_1024 = IMAGE_ROOT + "-1024x683.jpg"

OLD_HERO_OPEN = '<section class="ht-hero" aria-labelledby="ht-hero-title"><div class="ht-wrap">'
HERO_IMAGE = (
    '<img class="ht-hero-media" '
    f'src="{IMAGE_1024}" '
    f'srcset="{IMAGE_300} 300w, {IMAGE_768} 768w, {IMAGE_1024} 1024w" '
    'sizes="100vw" width="1024" height="683" alt="" '
    'fetchpriority="high" decoding="async">'
)
NEW_HERO_OPEN = '<section class="ht-hero" aria-labelledby="ht-hero-title">' + HERO_IMAGE + '<div class="ht-wrap">'

OLD_HERO_CSS = (
    ".ht-hero{position:relative;isolation:isolate;min-height:370px;display:flex;align-items:center;"
    f"background:#182630 url('{IMAGE_1024}') center 45%/cover no-repeat;color:#fff}}"
)
NEW_HERO_CSS = (
    ".ht-hero{position:relative;isolation:isolate;min-height:370px;display:flex;align-items:center;"
    "background:#182630;color:#fff}"
    ".ht-hero-media{position:absolute;inset:0;z-index:-2;width:100%;height:100%;object-fit:cover;"
    "object-position:center 45%}"
)
OLD_MOBILE_CSS = ".ht-hero{min-height:355px;background-position:65% center}"
NEW_MOBILE_CSS = ".ht-hero{min-height:355px}.ht-hero-media{object-position:65% center}"


class AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        values = dict(attrs)
        if values.get("href") is not None:
            self.hrefs.append(str(values["href"]))


def anchor_hrefs(value: str) -> list[str]:
    parser = AnchorCollector()
    parser.feed(value)
    return parser.hrefs


def optimize_home_content(raw: str) -> tuple[str, bool]:
    """Return optimized content and whether a change is required."""
    already = (
        raw.count('<img class="ht-hero-media"') == 1
        and "fetchpriority=\"high\"" in raw
        and OLD_HERO_CSS not in raw
        and NEW_HERO_CSS in raw
    )
    if already:
        validate_candidate(raw, raw)
        return raw, False

    required = {
        "hero markup": raw.count(OLD_HERO_OPEN),
        "hero CSS": raw.count(OLD_HERO_CSS),
        "mobile hero CSS": raw.count(OLD_MOBILE_CSS),
    }
    if any(count != 1 for count in required.values()):
        raise RuntimeError(f"Homepage LCP baseline changed: {required}")

    updated = raw.replace(OLD_HERO_OPEN, NEW_HERO_OPEN, 1)
    updated = updated.replace(OLD_HERO_CSS, NEW_HERO_CSS, 1)
    updated = updated.replace(OLD_MOBILE_CSS, NEW_MOBILE_CSS, 1)
    validate_candidate(raw, updated)
    return updated, True


def validate_candidate(original: str, candidate: str) -> None:
    if candidate.count('<img class="ht-hero-media"') != 1:
        raise RuntimeError("Expected exactly one hero media image")
    image_tag = re.search(r'<img class="ht-hero-media"[^>]+>', candidate)
    if not image_tag:
        raise RuntimeError("Hero media tag missing")
    tag = image_tag.group(0)
    required = ('fetchpriority="high"', 'decoding="async"', 'sizes="100vw"', 'width="1024"', 'height="683"', 'alt=""')
    if any(value not in tag for value in required):
        raise RuntimeError("Hero media priority, dimensions, sizing or decorative alt is incomplete")
    if "loading=" in tag:
        raise RuntimeError("The LCP image must not use lazy loading")
    if not all(url in tag for url in (IMAGE_300, IMAGE_768, IMAGE_1024)):
        raise RuntimeError("Responsive hero sources are incomplete")
    if OLD_HERO_CSS in candidate or OLD_MOBILE_CSS in candidate:
        raise RuntimeError("Old CSS background delivery remains")
    if NEW_HERO_CSS not in candidate or NEW_MOBILE_CSS not in candidate:
        raise RuntimeError("New hero media positioning is incomplete")
    if anchor_hrefs(original) != anchor_hrefs(candidate):
        raise RuntimeError("Homepage links changed during the image-only optimization")
    for protected in ("handytested0d-20", "As an Amazon Associate I earn from qualifying purchases."):
        if original.count(protected) != candidate.count(protected):
            raise RuntimeError(f"Protected content changed: {protected}")


def auth_header() -> str:
    password = os.environ.get("HT_WP_PASS")
    if not password:
        raise RuntimeError("HT_WP_PASS is required")
    return "Basic " + base64.b64encode(f"hebergravano@gmail.com:{password}".encode()).decode()


def fetch(url: str, *, payload: dict | None = None, authenticated: bool = False) -> tuple[bytes, dict[str, str]]:
    headers = {"User-Agent": "HandyTested controlled mobile LCP release"}
    if authenticated:
        headers["Authorization"] = auth_header()
    data = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    for attempt in range(4 if payload is None else 1):
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                return response.read(), dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            if payload is not None or exc.code not in {403, 429, 500, 502, 503, 504} or attempt == 3:
                raise
            print(f"Read returned HTTP {exc.code}; retry {attempt + 1}/3", flush=True)
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            if payload is not None or attempt == 3:
                raise
            print(f"Read failed ({type(exc).__name__}); retry {attempt + 1}/3", flush=True)
        time.sleep(2 + attempt * 2)
    raise RuntimeError("Read retries exhausted")


def get_home_edit() -> dict:
    query = urllib.parse.urlencode({"slug": "home-page", "context": "edit", "_fields": "id,slug,status,modified,content"})
    body, _ = fetch(API + "/pages?" + query, authenticated=True)
    pages = json.loads(body)
    if not isinstance(pages, list) or len(pages) != 1:
        raise RuntimeError("Expected exactly one homepage")
    page = pages[0]
    if page.get("id") != HOME_ID or page.get("slug") != "home-page" or page.get("status") != "publish":
        raise RuntimeError("Homepage identity or status changed")
    return page


def update_home(content: str) -> dict:
    body, _ = fetch(API + f"/pages/{HOME_ID}", payload={"content": content}, authenticated=True)
    result = json.loads(body)
    if result.get("id") != HOME_ID:
        raise RuntimeError("Homepage update was not acknowledged")
    return result


def public_snapshot(html: str) -> dict[str, object]:
    title = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    canonical = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, re.I)
    return {
        "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else None,
        "canonical": canonical.group(1) if canonical else None,
        "h1_count": len(re.findall(r"<h1\b", html, re.I)),
        "json_ld_count": len(re.findall(r'application/ld\+json', html, re.I)),
        "affiliate_tag_count": html.count("handytested0d-20"),
        "disclosure": "As an Amazon Associate I earn from qualifying purchases." in html,
    }


def verify_sitemap() -> dict[str, object]:
    posts_body, _ = fetch(API + "/posts?per_page=100&_fields=link,status")
    published = {item["link"].rstrip("/") + "/" for item in json.loads(posts_body) if item.get("status") == "publish"}
    index_body, _ = fetch(BASE + "/sitemap_index.xml")
    post_body, _ = fetch(BASE + "/post-sitemap.xml")
    ET.fromstring(index_body)
    root = ET.fromstring(post_body)
    locations = {node.text.rstrip("/") + "/" for node in root.findall("{*}url/{*}loc") if node.text}
    if len(published) != EXPECTED_POSTS or locations != published:
        raise RuntimeError(f"Post sitemap guard failed: published={len(published)} sitemap={len(locations)}")
    return {"published_posts": len(published), "post_sitemap_urls": len(locations), "index_xml": "valid", "post_xml": "valid"}


def verify_public(before: dict[str, object]) -> dict[str, object]:
    for attempt in range(6):
        body, _ = fetch(BASE + "/?ht_lcp_verify=" + str(int(time.time())))
        html = body.decode("utf-8", "replace")
        if '<img class="ht-hero-media"' in html and 'fetchpriority="high"' in html:
            if re.search(r'<img class="ht-hero-media"[^>]*\bloading=', html):
                raise RuntimeError("Public LCP image unexpectedly uses loading")
            after = public_snapshot(html)
            if after != before:
                raise RuntimeError(f"Protected public homepage signals changed: before={before} after={after}")
            return after
        if attempt < 5:
            time.sleep(5)
    raise RuntimeError("Optimized hero image did not become public in time")


def main() -> None:
    if MODE not in {"dry-run", "apply"}:
        raise ValueError("MODE must be dry-run or apply")
    home = get_home_edit()
    original = home["content"]["raw"]
    candidate, changed = optimize_home_content(original)
    public_body, _ = fetch(BASE + "/")
    before = public_snapshot(public_body.decode("utf-8", "replace"))
    if before["canonical"] != BASE + "/" or before["h1_count"] != 1 or not before["disclosure"]:
        raise RuntimeError(f"Public homepage SEO/disclosure preflight failed: {before}")
    sitemap = verify_sitemap()
    print(json.dumps({"mode": MODE, "home_id": HOME_ID, "modified": home["modified"], "change_required": changed, "public": before, "sitemap": sitemap}, indent=2))
    if MODE == "dry-run" or not changed:
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / "homepage-before.json").write_text(json.dumps(home, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        update_home(candidate)
        current = get_home_edit()
        if current["content"]["raw"] != candidate:
            raise RuntimeError("WordPress did not retain the exact guarded homepage content")
        after = verify_public(before)
        sitemap_after = verify_sitemap()
        print(json.dumps({"status": "applied", "public": after, "sitemap": sitemap_after}, indent=2))
    except Exception:
        update_home(original)
        print("Homepage rolled back to the pre-write backup", flush=True)
        raise


if __name__ == "__main__":
    main()
