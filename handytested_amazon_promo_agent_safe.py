"""Safety/accuracy wrapper for the HandyTested Amazon Promo Agent.

Keeps the existing agent intact while hardening email parsing and deadline handling.
"""
from __future__ import annotations

import datetime as dt
import email
import html
import re
from email.message import Message
from typing import Any

import handytested_amazon_promo_agent as agent


MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def robust_body_from_message(msg: Message) -> tuple[str, list[str]]:
    """Read both plain and HTML bodies so campaign details/links are not lost."""
    text_parts: list[str] = []
    html_parts: list[str] = []
    links: list[str] = []
    for part in msg.walk():
        ctype = part.get_content_type()
        disposition = str(part.get("Content-Disposition", "")).lower()
        if "attachment" in disposition or ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        decoded = payload.decode(charset, errors="replace")
        links.extend(re.findall(r'https?://[^\s"<>]+', decoded))
        if ctype == "text/plain":
            text_parts.append(decoded)
        else:
            html_parts.append(decoded)

    # Include visible HTML even when a text/plain alternative exists. Marketing emails
    # often put CTA labels, deadline wording, or product blocks only in HTML.
    visible_html = [agent.html_to_text(part) for part in html_parts]
    combined = "\n\n".join([*text_parts, *visible_html])
    combined = re.sub(r"\n{3,}", "\n\n", combined).strip()
    # De-duplicate links while preserving source order.
    seen: set[str] = set()
    amazon_links: list[str] = []
    for raw in links:
        clean = agent.clean_tracking_link(raw)
        if "amazon" not in clean.lower() or clean in seen:
            continue
        seen.add(clean)
        amazon_links.append(clean)
    return combined[:20000], amazon_links[:80]


def infer_explicit_end_date(promo: agent.PromoEmail) -> dt.date | None:
    """Deterministically infer only explicit English deadline forms from subject/body."""
    source = f"{promo.subject}\n{promo.text}"
    year = agent.today_local().year

    # Examples: "Ends Oct 7", "ends October 7, 2026", "through Oct 7".
    pat = re.compile(
        r"\b(?:ends?|ending|through|until|valid\s+(?:through|until))\s+"
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\.?\s+(\d{1,2})(?:,?\s+(20\d{2}))?\b",
        re.IGNORECASE,
    )
    m = pat.search(source)
    if not m:
        return None
    month = MONTHS[m.group(1).lower().rstrip(".")]
    day = int(m.group(2))
    parsed_year = int(m.group(3)) if m.group(3) else year
    try:
        candidate = dt.date(parsed_year, month, day)
    except ValueError:
        return None
    # If no year was stated and the inferred date is implausibly far in the past,
    # interpret it as the next calendar year. Never invent other dates.
    if not m.group(3) and candidate < agent.today_local() - dt.timedelta(days=45):
        candidate = dt.date(parsed_year + 1, month, day)
    return candidate


_original_classify = agent.classify_campaign


def safe_classify_campaign(promo: agent.PromoEmail) -> dict[str, Any]:
    campaign = _original_classify(promo)
    if not campaign.get("is_relevant"):
        return campaign

    explicit = infer_explicit_end_date(promo)
    if explicit:
        campaign["is_time_sensitive"] = True
        campaign["promotion_end_date"] = explicit.isoformat()
        campaign["expiration_reason"] = (
            f"Explicit campaign deadline found in source email: {explicit.isoformat()}."
        )
    else:
        # Validate model-provided ISO dates. If invalid, remove them rather than guessing.
        raw = campaign.get("promotion_end_date")
        if raw and agent.parse_iso_date(raw) is None:
            campaign["promotion_end_date"] = None
            campaign["expiration_reason"] = (
                "Temporary promotion detected, but no safely parseable explicit end date was found."
            )
    return campaign


def safe_campaign_expiration_date(campaign: dict[str, Any]) -> dt.date | None:
    if not campaign.get("is_time_sensitive"):
        return None
    explicit = agent.parse_iso_date(campaign.get("promotion_end_date"))
    if explicit:
        # Keep the post live through the stated final day, then draft it next day.
        return explicit + dt.timedelta(days=1)
    # Unknown temporary deadline: conservative short fallback, not 21 days.
    return agent.today_local() + dt.timedelta(days=3)


agent.body_from_message = robust_body_from_message
agent.classify_campaign = safe_classify_campaign
agent.campaign_expiration_date = safe_campaign_expiration_date


if __name__ == "__main__":
    agent.run()
