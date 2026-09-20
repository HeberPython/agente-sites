"""Explicit human evidence gate for HandyTested generator publication.

Draft creation is unaffected. Environment switches never substitute for a
source record or make the validator a fact-checker.
"""

from __future__ import annotations

import os
from pathlib import Path

from handytested_editorial_validator import validate


def require_publish_approval(status: str, title: str, content: str) -> None:
    if status != "publish":
        return
    if os.environ.get("HT_EDITORIAL_APPROVED") != "1":
        raise RuntimeError("HandyTested publication requires HT_EDITORIAL_APPROVED=1 after human review")
    root = Path(__file__).parent / "handytested_sources"
    source_name = os.environ.get("HT_SOURCE_RECORD", "")
    if not source_name or Path(source_name).name != source_name or not source_name.endswith(".md"):
        raise RuntimeError("HT_SOURCE_RECORD must name a versioned .md file in handytested_sources")
    source = root / source_name
    if not source.is_file():
        raise RuntimeError(f"Missing source record: {source_name}")
    evidence = source.read_text(encoding="utf-8")
    if "https://" not in evidence or "PENDING" in evidence or "UNVERIFIED" in evidence:
        raise RuntimeError("Source record is incomplete or has no primary-source URL")
    products = {item.strip() for item in os.environ.get("HT_VERIFIED_PRODUCTS", "").split(";") if item.strip()}
    for product in products:
        if product.casefold() not in evidence.casefold() or product.casefold() not in content.casefold():
            raise RuntimeError(f"Verified product is not present in both article and source record: {product}")
    findings = validate(title, content, source_record=source, verified_products=products)
    blockers = [item for item in findings if item["severity"] == "BLOCK"]
    commercial = [item for item in findings if item["code"] in {"DOLLAR_PRICE", "RATING"}]
    if blockers or (commercial and os.environ.get("HT_COMMERCIAL_CLAIMS_APPROVED") != "1"):
        raise RuntimeError(f"HandyTested editorial validation failed: {blockers + commercial}")
