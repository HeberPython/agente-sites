"""Compare public posts with Rank Math sitemap and optionally clear its transients."""

from __future__ import annotations

import base64
import json
import os
import urllib.request
import xml.etree.ElementTree as ET


BASE = "https://handytested.com"
APPLY = os.environ.get("APPLY", "0") == "1"


def read(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "HandyTested sitemap check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def compare() -> tuple[set[str], set[str]]:
    posts = json.loads(read(BASE + "/wp-json/wp/v2/posts?per_page=100&_fields=link,status"))
    published = {post["link"] for post in posts if post["status"] == "publish"}
    root = ET.fromstring(read(BASE + "/post-sitemap.xml"))
    sitemap = {element.text for element in root.iter() if element.tag.endswith("loc")}
    missing = published - sitemap
    extra = sitemap - published
    print(f"Published: {len(published)}; sitemap: {len(sitemap)}; missing: {len(missing)}; extra: {len(extra)}")
    for label, urls in (("Missing", missing), ("Extra", extra)):
        for url in sorted(urls):
            print(f"{label}: {url}")
    return missing, extra


def clear_rank_math_transients() -> None:
    token = base64.b64encode(
        f"hebergravano@gmail.com:{os.environ['HT_WP_PASS']}".encode()
    ).decode()
    request = urllib.request.Request(
        BASE + "/wp-json/rankmath/v1/toolsAction",
        data=json.dumps({"action": "clear_transients"}).encode(),
        method="POST",
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "User-Agent": "HandyTested sitemap cache refresh",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        print("Rank Math response:", response.read().decode()[:500])


def main() -> None:
    before = compare()
    if not APPLY:
        print("Dry-run only; no cache change")
        return
    if not any(before):
        print("Sitemap already matches published posts")
        return
    clear_rank_math_transients()
    print("After transient clear:")
    compare()


if __name__ == "__main__":
    main()
