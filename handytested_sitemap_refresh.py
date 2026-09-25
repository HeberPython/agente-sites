"""Compare public posts with Rank Math sitemap and optionally clear its transients."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
import xml.etree.ElementTree as ET


BASE = "https://handytested.com"
APPLY = os.environ.get("APPLY", "0") == "1"


def read(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "HandyTested sitemap check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def compare(*, cache_bust: bool = False) -> tuple[set[str], set[str]]:
    posts = json.loads(read(BASE + "/wp-json/wp/v2/posts?per_page=100&_fields=link,status"))
    published = {post["link"] for post in posts if post["status"] == "publish"}
    suffix = f"?ht_sitemap_check={int(time.time())}" if cache_bust else ""
    root = ET.fromstring(read(BASE + "/post-sitemap.xml" + suffix))
    sitemap = {element.text for element in root.iter() if element.tag.endswith("loc")}
    missing = published - sitemap
    extra = sitemap - published
    print(f"Published: {len(published)}; sitemap: {len(sitemap)}; missing: {len(missing)}; extra: {len(extra)}")
    for label, urls in (("Missing", missing), ("Extra", extra)):
        for url in sorted(urls):
            print(f"{label}: {url}")
    return missing, extra


def rank_math_action(action: str) -> None:
    token = base64.b64encode(
        f"hebergravano@gmail.com:{os.environ['HT_WP_PASS']}".encode()
    ).decode()
    request = urllib.request.Request(
        BASE + "/wp-json/rankmath/v1/toolsAction",
        data=json.dumps({"action": action}).encode(),
        method="POST",
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "HandyTested sitemap cache refresh",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        print(f"Rank Math {action} response:", response.read().decode()[:500])


def main() -> None:
    before = compare()
    if not APPLY:
        print("Dry-run only; no cache change")
        return
    if not any(before):
        print("Sitemap already matches published posts")
        return
    rank_math_action("flushPermalinks")
    rank_math_action("clear_transients")
    time.sleep(10)
    print("After permalink and transient refresh:")
    after = compare(cache_bust=True)
    if any(after):
        raise RuntimeError("Post sitemap still does not match published posts")


if __name__ == "__main__":
    main()
