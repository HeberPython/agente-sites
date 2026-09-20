"""Read-only Phase 3 snapshot and article-level editorial screening.

The generated records are review worksheets, not evidence that a claim or
product has been verified. No WordPress writes are performed here.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import parse_qs, urlparse

from handytested_public_audit import BASE, fetch, fetch_html, plain


TAG = "handytested0d-20"
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
TEST_CLAIMS = re.compile(
    r"\b(?:we (?:tested|measured|used|found during testing)|our (?:tests|testing)|"
    r"during (?:our )?tests?|hands.on test(?:ing)?|after (?:\w+ )?weeks? of testing)\b",
    re.I,
)
PRICE = re.compile(r"\$\s?\d[\d,.]*")
RATING = re.compile(r"\b\d(?:\.\d)?\s?/\s?5\b|[★☆]{2,}|\b(?:rating|rated)\b", re.I)


class Elements(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, dict[str, str], list[str]]] = []
        self.headings: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.paragraphs: list[str] = []
        self.table_rows: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "img":
            self.images.append({key: values.get(key, "") for key in ("src", "alt", "width", "height")})
        if tag in {"h1", "h2", "h3", "p", "a", "tr"}:
            self.stack.append((tag, values, []))

    def handle_data(self, data: str) -> None:
        for _, _, parts in self.stack:
            parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            kind, attrs, parts = self.stack[index]
            if kind != tag:
                continue
            value = " ".join(" ".join(parts).split())
            if kind in {"h1", "h2", "h3"} and value:
                self.headings.append({"level": kind, "text": value})
            elif kind == "p" and value:
                self.paragraphs.append(value)
            elif kind == "tr" and value:
                self.table_rows.append(value)
            elif kind == "a":
                self.links.append({"text": value, "href": attrs.get("href", "")})
            del self.stack[index]
            break


def parse(content: str) -> Elements:
    result = Elements()
    result.feed(content)
    return result


def candidate_products(elements: Elements) -> list[str]:
    products: list[str] = []
    for link in elements.links:
        url = urlparse(link["href"])
        if url.hostname not in {"amazon.com", "www.amazon.com"}:
            continue
        query = parse_qs(url.query).get("k", [])
        if query and query[0] not in products:
            products.append(query[0])
    return products


def amazon_links(elements: Elements) -> list[dict[str, str | bool]]:
    result = []
    for link in elements.links:
        url = urlparse(link["href"])
        if url.hostname not in {"amazon.com", "www.amazon.com"}:
            continue
        params = parse_qs(url.query)
        result.append({
            "text": link["text"], "url": link["href"],
            "tag_ok": params.get("tag", [""])[0] == TAG,
            "search": url.path == "/s",
        })
    return result


def meta_from_html(source: str, name: str) -> str:
    pattern = rf'<meta\b[^>]*name=["\']{re.escape(name)}["\'][^>]*>'
    match = re.search(pattern, source, re.I)
    if not match:
        return ""
    value = re.search(r'content=["\']([^"\']*)["\']', match.group(), re.I)
    return value.group(1) if value else ""


def build_record(post: dict, categories: dict[int, str], media: dict[int, dict], live_html: str) -> dict:
    content = post["content"]["rendered"]
    elements = parse(content)
    body = plain(content)
    title = plain(post["title"]["rendered"])
    links = amazon_links(elements)
    internal = [link for link in elements.links if urlparse(link["href"]).hostname in {"handytested.com", "www.handytested.com"}]
    claims = [p for p in elements.paragraphs if TEST_CLAIMS.search(p)]
    prices = [p for p in elements.paragraphs + elements.table_rows if PRICE.search(p)]
    ratings = [p for p in elements.paragraphs + elements.table_rows if RATING.search(p)]
    canonical_match = re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>', live_html, re.I)
    canonical = ""
    if canonical_match:
        href = re.search(r'href=["\']([^"\']+)["\']', canonical_match.group(), re.I)
        canonical = href.group(1) if href else ""
    page = parse(live_html)
    category = [categories.get(item, str(item)) for item in post["categories"]]
    return {
        "url": post["link"], "id": post["id"], "slug": post["slug"],
        "priority": "UNASSIGNED", "title": title, "category": category,
        "published": post["date"], "modified": post["modified"],
        "search_intent": "COMMERCIAL INVESTIGATION" if links else "UNDETERMINED",
        "primary_topic": title, "likely_primary_keyword": title,
        "secondary_topics": [], "proposed_title": None,
        "product_candidates_unverified": candidate_products(elements),
        "claim_passages_requiring_verification": claims,
        "price_passages_requiring_verification": prices,
        "price_values_detected": sorted(set(PRICE.findall(body))),
        "rating_passages_requiring_verification": ratings,
        "rating_values_detected": sorted(set(RATING.findall(body))),
        "amazon_links": links, "body_images": elements.images,
        "featured_media": media.get(post["featured_media"], {}),
        "internal_links": internal, "external_factual_sources": [],
        "disclosure_exact": DISCLOSURE in body,
        "title_has_year": bool(re.search(r"\b20\d\d\b", title)),
        "seo_title": re.search(r"<title[^>]*>(.*?)</title>", live_html, re.I | re.S).group(1).strip() if re.search(r"<title[^>]*>(.*?)</title>", live_html, re.I | re.S) else "",
        "meta_description": meta_from_html(live_html, "description"),
        "canonical": canonical, "h1": [item["text"] for item in page.headings if item["level"] == "h1"],
        "body_headings": elements.headings,
        "schema_present": 'application/ld+json' in live_html,
        "schema_review": "PENDING MANUAL SEMANTIC REVIEW",
        "html_fetched": bool(live_html),
        "update_decision": "BLOCKED - REQUIRES MANUAL VERIFICATION",
    }


def markdown(record: dict, checked: str) -> str:
    def lines(items: list, formatter) -> str:
        return "\n".join("- " + formatter(item) for item in items) or "- None detected by screening."

    links = lines(record["amazon_links"], lambda x: f"{x['text']} | {'SEARCH' if x['search'] else 'OTHER'} | tag {'OK' if x['tag_ok'] else 'ISSUE'} | {x['url']}")
    return f"""# {record['title']}

Screened: {checked}. **This is a review worksheet, not product verification.**

- URL: {record['url']}
- WordPress ID: {record['id']}
- Slug: {record['slug']}
- Priority: {record['priority']}
- Category: {', '.join(record['category'])}
- Published / modified: {record['published']} / {record['modified']}
- Search intent: {record['search_intent']}
- Primary topic / likely keyword: {record['primary_topic']}
- Proposed title: PENDING EDITORIAL REVIEW
- Secondary topics: PENDING EDITORIAL REVIEW
- Current SEO title: {record['seo_title']}
- Current meta description: {record['meta_description']}
- Canonical: {record['canonical']}
- H1: {', '.join(record['h1'])}
- Title includes year: {record['title_has_year']}
- Exact Amazon disclosure in post body: {record['disclosure_exact']}
- JSON-LD present: {record['schema_present']} (semantics unverified)
- Public HTML fetched: {record['html_fetched']}
- Update decision: {record['update_decision']}

## Product Candidates (Unverified)
{lines(record['product_candidates_unverified'], str)}

## Test/Experience Claims To Verify
{lines(record['claim_passages_requiring_verification'], str)}

## Price Passages To Verify
{lines(record['price_passages_requiring_verification'], str)}

Detected dollar values (including CTAs): {', '.join(record['price_values_detected']) or 'none'}

## Rating Passages To Verify
{lines(record['rating_passages_requiring_verification'], str)}

Detected rating markers: {', '.join(record['rating_values_detected']) or 'none'}

## Amazon Links
{links}

## Images
- Featured media: {json.dumps(record['featured_media'], ensure_ascii=False)}
- Body image elements: {json.dumps(record['body_images'], ensure_ascii=False)}
- Licensing and product match: UNVERIFIED

## Internal Links
{lines(record['internal_links'], lambda x: f"{x['text']} | {x['href']}")}

## Source Evidence
| Product | Manufacturer / primary source | Source type | Checked | Supported claim | Status / notes |
|---|---|---|---|---|---|
| PENDING | PENDING | PENDING | PENDING | PENDING | No recommendation approved yet |

## Editorial Decision
BLOCKED - REQUIRES MANUAL VERIFICATION. Screened fields above must be reviewed in context before a publish decision. Do not infer truth from a regex match or Amazon search result.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("handytested_sources"))
    args = parser.parse_args()
    posts = fetch("/wp-json/wp/v2/posts?per_page=100&_fields=id,slug,title,link,date,modified,categories,content,featured_media")
    categories = fetch("/wp-json/wp/v2/categories?per_page=100&_fields=id,slug")
    media = fetch("/wp-json/wp/v2/media?per_page=100&_fields=id,source_url,alt_text,media_details,caption,description")
    assert isinstance(posts, list) and isinstance(categories, list) and isinstance(media, list)
    if len(posts) != 38:
        raise RuntimeError(f"Expected 38 posts before making snapshot, got {len(posts)}")
    names = {item["id"]: item["slug"] for item in categories}
    images = {item["id"]: {"url": item["source_url"], "alt": item["alt_text"], "width": item.get("media_details", {}).get("width"), "height": item.get("media_details", {}).get("height")} for item in media}
    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    queue = Path(__file__).with_name("HANDYTESTED_PHASE2_REPORT.md").read_text(encoding="utf-8")
    priorities = {
        slug: priority
        for priority, slug in re.findall(r"^\| (P[012]) \| ([a-z0-9-]+) \|", queue, re.M)
    }
    if len(priorities) != 38:
        raise RuntimeError(f"Expected 38 priorities in Phase 2 report, got {len(priorities)}")
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for post in posts:
        live_html = ""
        for attempt in range(3):
            try:
                live_html = fetch_html(post["link"])
                break
            except (TimeoutError, OSError) as exc:
                print(f"HTML retry {attempt + 1}/3 {post['slug']}: {type(exc).__name__}", flush=True)
                time.sleep(attempt + 1)
        record = build_record(post, names, images, live_html)
        record["priority"] = priorities[record["slug"]]
        records.append(record)
        (args.output / f"{record['slug']}.md").write_text(markdown(record, checked), encoding="utf-8")
        print(f"Screened {len(records):02d}/38 {record['slug']}", flush=True)
    (args.output / "public_snapshot.json").write_text(json.dumps({"checked": checked, "posts": posts, "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved read-only snapshot and {len(records)} review worksheets in {args.output}")


if __name__ == "__main__":
    main()
