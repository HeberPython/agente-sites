"""Read-only inventory of public HandyTested WordPress content."""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request


BASE = "https://handytested.com"
CLAIM = re.compile(
    r"we tested|we measured|we used|during our testing|our testing|"
    r"hands-on testing|after testing|how we tested|during our tests",
    re.IGNORECASE,
)


def fetch(path: str) -> object:
    request = urllib.request.Request(BASE + path, headers={"User-Agent": "HandyTested public audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "HandyTested public audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def plain(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def main() -> None:
    posts = fetch(
        "/wp-json/wp/v2/posts?per_page=100&"
        "_fields=id,slug,title,link,date,modified,categories,content,featured_media"
    )
    pages = fetch("/wp-json/wp/v2/pages?per_page=100&_fields=id,slug,title,link,status")
    categories = fetch("/wp-json/wp/v2/categories?per_page=100&_fields=id,slug,name,count")
    assert isinstance(posts, list) and isinstance(pages, list) and isinstance(categories, list)
    category_names = {item["id"]: item["slug"] for item in categories}

    print(f"Published posts: {len(posts)} | Public pages: {len(pages)}")
    print("| Post | Category | Published | Old year | Test claim | Dollar | Rating | Amazon search links |")
    print("|---|---|---|---|---|---|---|---:|")
    for post in posts:
        title = plain(post["title"]["rendered"])
        body = plain(post["content"]["rendered"])
        raw = html.unescape(post["content"]["rendered"])
        categories_text = ", ".join(category_names.get(item, str(item)) for item in post["categories"])
        old_year = "yes" if re.search(r"\b202[45]\b", title) else ""
        claim = "yes" if CLAIM.search(body) else ""
        dollar = "yes" if re.search(r"\$\s?\d", body) else ""
        rating = "yes" if re.search(r"\b(?:rating|[1-5](?:\.\d)?/5)\b", body, re.IGNORECASE) else ""
        searches = raw.count("amazon.com/s?")
        print(
            f"| [{title}]({post['link']}) | {categories_text} | {post['date'][:10]} | "
            f"{old_year} | {claim} | {dollar} | {rating} | {searches} |"
        )

    print("\nPages:")
    for page in pages:
        print(f"- [{plain(page['title']['rendered'])}]({page['link']}) ({page['slug']})")
    print("\nCategories:")
    for category in categories:
        print(f"- {category['slug']}: {category['count']}")

    if "--html" in sys.argv:
        print("\nHTML checks:")
        print("| URL | H1 | Canonical | Description | OG | JSON-LD | Amazon tag |")
        print("|---|---:|:---:|:---:|:---:|:---:|:---:|")
        for item in [*pages, *posts]:
            url = item["link"]
            try:
                source = fetch_html(url)
            except Exception as exc:
                print(f"| {url} | ERROR: {type(exc).__name__} | | | | | |")
                continue
            h1 = len(re.findall(r"<h1\b", source, re.IGNORECASE))
            canonical = bool(re.search(r'<link[^>]+rel=["\']canonical["\']', source, re.IGNORECASE))
            description = bool(re.search(r'<meta[^>]+name=["\']description["\']', source, re.IGNORECASE))
            og = 'property="og:title"' in source or "property='og:title'" in source
            schema = 'type="application/ld+json"' in source
            tag = "handytested0d-20" in source
            print(f"| {url} | {h1} | {canonical} | {description} | {og} | {schema} | {tag} |")


if __name__ == "__main__":
    main()
