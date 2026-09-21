"""Audit published article Amazon searches and contextual internal links."""

from __future__ import annotations

from collections import Counter
import html
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

from handytested_phase5_crawl import BASE, api, get


class Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.href = ""
        self.label = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href") or ""
            self.label = ""

    def handle_data(self, data: str) -> None:
        if self.href:
            self.label += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.href:
            self.links.append((self.href, " ".join(html.unescape(self.label).split())))
            self.href = ""
            self.label = ""


def norm(url: str, source: str) -> str:
    parsed = urlparse(urljoin(source, url))
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path, "", "", ""))


def main() -> None:
    out_amazon = Path("HANDYTESTED_PHASE5_AMAZON.md")
    out_links = Path("HANDYTESTED_PHASE5_INTERNAL_LINKS.md")
    if out_amazon.exists() or out_links.exists():
        raise RuntimeError("Refusing to overwrite existing audit output")
    posts = api("posts?per_page=100&_fields=id,slug,link,content")
    urls = {post["link"] for post in posts}
    incoming = Counter()
    amazon = []
    internal = []
    for post in posts:
        parser = Anchors()
        parser.feed(post["content"]["rendered"])
        for href, label in parser.links:
            url = norm(href, post["link"])
            parts = urlparse(href)
            if parts.hostname in {"www.amazon.com", "amazon.com"}:
                query = parse_qs(parts.query)
                amazon.append({
                    "article": post["link"], "product": query.get("k", [""])[0],
                    "label": label, "destination": href, "tag": query.get("tag", [""])[0],
                    "direct": parts.path.startswith("/dp/") or parts.path.startswith("/gp/product/"),
                    "region": parts.hostname,
                })
            elif urlparse(url).hostname == "handytested.com" and url != post["link"]:
                internal.append((post["link"], url, label))
                if url in urls:
                    incoming[url] += 1
    if len(posts) != 38:
        raise RuntimeError(f"Expected 38 posts, found {len(posts)}")
    if any(row["tag"] != "handytested0d-20" or not row["product"] or row["direct"] for row in amazon):
        raise RuntimeError("Unexpected Amazon destination or missing tag/query")
    lines = [
        "# HandyTested Phase 5 Amazon link inventory",
        "",
        f"Published article-body links: {len(amazon)} in {len(posts)} posts. These are syntactically verified tagged Amazon.com searches, not verified direct listings or confirmed availability. No ASIN was inferred.",
        "",
        "| Article | Product / exact search query | Current Amazon destination | Affiliate tag present | Direct listing verified? | ASIN verified? | Region | Status | Action |",
        "|---|---|---|:---:|:---:|:---:|---|---|---|",
    ]
    for row in amazon:
        cell = lambda x: str(x).replace("|", "\\|")
        lines.append("| " + " | ".join(cell(x) for x in (
            row["article"], row["product"], row["destination"], "yes", "no", "no", "Amazon US",
            "SEARCH VERIFIED", "Retain search; verify exact live listing in SiteStripe before direct-link conversion"
        )) + " |")
    out_amazon.write_text("\n".join(lines) + "\n", encoding="utf-8")
    targets = sorted({target for _, target, _ in internal})
    statuses = {target: get(target)[0] for target in targets}
    broken = [(source, target, label, statuses[target]) for source, target, label in internal if statuses[target] >= 400]
    orphans = sorted(urls - set(incoming))
    lines = [
        "# HandyTested Phase 5 contextual internal links",
        "",
        f"Article-body internal links: {len(internal)}; unique targets: {len(targets)}; broken links: {len(broken)}; posts without an incoming article-body link: {len(orphans)}. Theme navigation and category archive links are excluded from the orphan definition.",
        "",
        "## Broken links", "",
    ]
    lines += [f"- HTTP {status}: {source} -> {target} ({label})" for source, target, label, status in broken] or ["- None found."]
    lines += ["", "## Posts without an incoming contextual article-body link", ""]
    lines += [f"- {url}" for url in orphans] or ["- None found."]
    lines += ["", "## Target statuses", "", "| Target | HTTP |", "|---|---:|"]
    lines += [f"| {target} | {status} |" for target, status in statuses.items()]
    out_links.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"amazon_searches": len(amazon), "internal_links": len(internal), "broken": len(broken), "orphans": len(orphans)}, sort_keys=True))


if __name__ == "__main__":
    main()
