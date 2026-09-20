"""Pre-publication screening; findings require a human factual decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlparse

from handytested_phase3_review import DISCLOSURE, PRICE, RATING, TAG, TEST_CLAIMS, parse
from handytested_public_audit import plain


def validate(title: str, content: str, *, source_record: Path | None = None,
             verified_products: set[str] | None = None) -> list[dict[str, str]]:
    """Return screening findings, not a machine judgment of factual truth."""
    findings: list[dict[str, str]] = []

    def flag(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    text = plain(content)
    elements = parse(content)
    if TEST_CLAIMS.search(text):
        flag("BLOCK", "TEST_CLAIM", "First-hand language requires documentary evidence or contextual rewrite.")
    if PRICE.search(text):
        flag("WARNING", "DOLLAR_PRICE", "Review fixed prices and budget promises against dated evidence.")
    if RATING.search(text):
        flag("WARNING", "RATING", "Review ratings and their source/methodology.")
    if re.search(r"\b20\d\d\b", title):
        flag("WARNING", "TITLE_YEAR", "Evaluate title freshness individually; keep slug by default.")
    if DISCLOSURE not in text:
        flag("BLOCK", "DISCLOSURE", "Exact Amazon Associate statement is absent from post body.")
    if source_record is None or not source_record.is_file():
        flag("BLOCK", "SOURCE_RECORD", "No article-specific source record supplied.")
    elif "PENDING" in source_record.read_text(encoding="utf-8"):
        flag("WARNING", "SOURCE_PENDING", "Source record contains unverified fields.")
    if verified_products is None or not verified_products:
        flag("BLOCK", "PRODUCT_VERIFICATION", "No verified product IDs supplied for this release.")
    for link in elements.links:
        url = urlparse(link["href"])
        if url.hostname not in {"amazon.com", "www.amazon.com"}:
            continue
        params = parse_qs(url.query)
        if params.get("tag", [""])[0] != TAG:
            flag("BLOCK", "AMAZON_TAG", f"Affiliate tag absent or wrong: {link['href']}")
        if url.path == "/s":
            flag("WARNING", "AMAZON_SEARCH", "Search destination needs a verified direct link when possible.")
    if any(item["level"] == "h1" for item in elements.headings):
        flag("WARNING", "BODY_H1", "Body H1 may duplicate the Astra article title; check rendered page.")
    if re.search(r'"@type"\s*:\s*"(?:Product|Review)"', content, re.I):
        flag("BLOCK", "PRODUCT_SCHEMA", "Product/Review JSON-LD needs factual and eligibility review.")
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--snapshot", type=Path, default=Path("handytested_sources/public_snapshot.json"))
    parser.add_argument("--source-record", type=Path)
    parser.add_argument("--verified-product", action="append", default=[])
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    matches = [post for post in snapshot["posts"] if post["slug"] == args.slug]
    if len(matches) != 1:
        raise SystemExit(f"Expected one snapshot post for {args.slug}")
    post = matches[0]
    findings = validate(
        plain(post["title"]["rendered"]), post["content"]["rendered"],
        source_record=args.source_record, verified_products=set(args.verified_product),
    )
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    raise SystemExit(1 if any(item["severity"] == "BLOCK" for item in findings) else 0)


if __name__ == "__main__":
    main()
