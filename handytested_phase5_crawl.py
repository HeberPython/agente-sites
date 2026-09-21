"""Public, read-only Phase 5 WordPress and sitemap inventory."""

from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


BASE = "https://handytested.com"
UA = {"User-Agent": "HandyTested public Phase 5 audit"}


def get(url: str) -> tuple[int, str, dict[str, str], bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as response:
            return response.status, response.url, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.url, dict(exc.headers), exc.read()


def api(path: str) -> list[dict]:
    status, _, _, body = get(BASE + "/wp-json/wp/v2/" + path)
    if status != 200:
        raise RuntimeError(f"REST {path}: HTTP {status}")
    data = json.loads(body)
    if not isinstance(data, list):
        raise RuntimeError(f"REST {path}: expected a list")
    return data


def sitemap(path: str) -> set[str]:
    status, _, _, body = get(BASE + path)
    if status != 200:
        raise RuntimeError(f"Sitemap {path}: HTTP {status}")
    root = ET.fromstring(body)
    return {
        child.text
        for url in root
        if url.tag.endswith("url")
        for child in url
        if child.tag.endswith("loc") and child.text
    }


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.h1 = []
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.schemas = []
        self.links = []
        self.images = []
        self._capture = ""
        self._text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        if tag == "title" or tag == "h1" or (tag == "script" and attrs.get("type") == "application/ld+json"):
            self._capture = tag if tag != "script" else "schema"
            self._text = ""
        if tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.meta[key.lower()] = attrs.get("content") or ""
        if tag == "link" and "canonical" in (attrs.get("rel") or "").lower():
            self.canonical = attrs.get("href") or ""
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "img":
            self.images.append({key: attrs.get(key) for key in ("src", "alt", "width", "height", "loading")})

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._text += data

    def handle_endtag(self, tag: str) -> None:
        if (tag == self._capture) or (tag == "script" and self._capture == "schema"):
            value = html.unescape(self._text.strip())
            if self._capture == "title":
                self.title = value
            elif self._capture == "h1":
                self.h1.append(value)
            elif self._capture == "schema":
                try:
                    self.schemas.append(json.loads(value))
                except json.JSONDecodeError:
                    self.schemas.append({"invalid_json": True})
            self._capture = ""
            self._text = ""


def plain(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value))).strip()


def inspect(item: dict, kind: str, sitemaps: dict[str, set[str]]) -> dict:
    url = item["link"]
    status, final, headers, body = get(url)
    page = Page()
    source = body.decode("utf-8", "replace")
    page.feed(source)
    robots = page.meta.get("robots", "")
    xrobots = headers.get("X-Robots-Tag", "")
    indexable = status == 200 and "noindex" not in (robots + xrobots).lower()
    expected_map = {"post": "posts", "page": "pages", "category": "categories"}
    in_sitemap = url in sitemaps[expected_map[kind]]
    issues = []
    if status != 200:
        issues.append(f"HTTP {status}")
    if final != url:
        issues.append("redirect")
    if indexable and page.canonical != url:
        issues.append("canonical")
    if not page.title:
        issues.append("title missing")
    if len(page.h1) != 1:
        issues.append(f"H1={len(page.h1)}")
    if indexable and not in_sitemap:
        issues.append("missing sitemap")
    if not indexable and in_sitemap:
        issues.append("noindex in sitemap")
    amazon = [x for x in page.links if "amazon.com" in x.lower() or "amzn.to" in x.lower()]
    if kind == "post" and "As an Amazon Associate I earn from qualifying purchases." not in plain(source):
        issues.append("disclosure missing")
    return {
        "url": url, "type": kind, "http": status, "final_url": final,
        "indexable": indexable, "robots": robots, "x_robots": xrobots,
        "canonical": page.canonical, "title": page.title, "description": page.meta.get("description", ""),
        "h1": page.h1, "sitemap": in_sitemap, "modified": item.get("modified", ""),
        "excerpt": plain(item.get("excerpt", {}).get("rendered", "")),
        "schemas": page.schemas, "amazon_links": amazon, "links": page.links,
        "images": page.images, "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    posts = api("posts?per_page=100&_fields=id,slug,link,title,excerpt,modified,featured_media")
    pages = api("pages?per_page=100&_fields=id,slug,link,title,modified")
    categories = api("categories?per_page=100&_fields=id,slug,link,name,count")
    sitemaps = {
        "posts": sitemap("/post-sitemap.xml"),
        "pages": sitemap("/page-sitemap.xml"),
        "categories": sitemap("/category-sitemap.xml"),
    }
    rows = [inspect(item, kind, sitemaps) for kind, items in (("page", pages), ("post", posts), ("category", categories)) for item in items]
    expected = {kind: {item["link"] for item in items} for kind, items in (("posts", posts), ("pages", pages), ("categories", categories))}
    extras = {kind: sorted(urls - expected[kind]) for kind, urls in sitemaps.items()}
    status, _, _, robots_body = get(BASE + "/robots.txt")
    lines = [
        "# HandyTested Phase 5 public baseline",
        "",
        "Read-only crawl of public REST, HTML, Rank Math XML and robots.txt. Indexable means HTTP 200 without an observed noindex directive; it does not prove Google indexing.",
        "",
        f"Posts: {len(posts)}; pages: {len(pages)}; categories: {len(categories)}. Sitemap counts: posts {len(sitemaps['posts'])}, pages {len(sitemaps['pages'])}, categories {len(sitemaps['categories'])}.",
        f"robots.txt: HTTP {status}.", "",
        "| URL | Type | HTTP | Indexable | Canonical | Title | H1 | Sitemap | Last modified | Issue |",
        "|---|---|---:|:---:|---|---|---|:---:|---|---|",
    ]
    for row in rows:
        cell = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(cell(x) for x in (
            row["url"], row["type"], row["http"], "yes" if row["indexable"] else "no",
            row["canonical"], row["title"], "; ".join(row["h1"]),
            "yes" if row["sitemap"] else "no", row["modified"], "; ".join(row["issues"])
        )) + " |")
    lines += ["", "## Sitemap extras", ""]
    for kind, urls in extras.items():
        lines.append(f"- {kind}: {', '.join(urls) if urls else 'none'}")
    lines += ["", "## robots.txt", "", "```text", robots_body.decode("utf-8", "replace").strip(), "```", ""]
    result = "\n".join(lines)
    if args.output:
        if args.output.exists() and not args.output.read_text(encoding="utf-8").startswith("# HandyTested Phase 5 public baseline"):
            raise RuntimeError(f"Refusing to overwrite non-baseline file {args.output}")
        args.output.write_text(result, encoding="utf-8")
        args.output.with_suffix(".json").write_text(json.dumps({"rows": rows, "sitemap_extras": extras}, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
