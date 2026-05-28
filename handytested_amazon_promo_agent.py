"""
HandyTested Amazon Promo Agent

Reads promotional emails sent to promoassociados@handytested.com, turns each
Amazon Associates campaign into an editorial HandyTested post, and publishes it
to WordPress as a draft by default.

Required environment variables:
  OPENAI_API_KEY
  HT_WP_PASS
  PROMO_EMAIL_PASS

Optional environment variables:
  PROMO_EMAIL_USER           default: promoassociados@handytested.com
  PROMO_EMAIL_IMAP_HOST      default: imap.hostinger.com
  PROMO_EMAIL_IMAP_PORT      default: 993
  PROMO_EMAIL_FOLDER         default: INBOX
  PROMO_EMAIL_QUERY          default: UNSEEN
  OPENAI_MODEL               default: gpt-4o-mini
  PROMO_POST_STATUS          default: draft
  PROMO_MAX_EMAILS           default: 3
  PROMO_MARK_SEEN            default: 1
  TELEGRAM_TOKEN
  TELEGRAM_CHAT_ID
  PROMO_SAMPLE_EMAIL_FILE     parse a local .eml/.txt file instead of IMAP
"""

from __future__ import annotations

import base64
import datetime as dt
import email
import html
import http.client
import imaplib
import json
import os
import re
import socket
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import Message
from typing import Any


OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"

WP_URL = "https://handytested.com"
WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]
AMAZON_TAG = "amazonrev089f-20"
AMAZON_DOMAIN = os.environ.get("AMAZON_DOMAIN", "www.amazon.com")

PROMO_EMAIL_USER = os.environ.get("PROMO_EMAIL_USER", "promoassociados@handytested.com")
PROMO_EMAIL_PASS = os.environ["PROMO_EMAIL_PASS"]
PROMO_EMAIL_IMAP_HOST = os.environ.get("PROMO_EMAIL_IMAP_HOST", "imap.hostinger.com")
PROMO_EMAIL_IMAP_PORT = int(os.environ.get("PROMO_EMAIL_IMAP_PORT", "993"))
PROMO_EMAIL_FOLDER = os.environ.get("PROMO_EMAIL_FOLDER", "INBOX")
PROMO_EMAIL_QUERY = os.environ.get("PROMO_EMAIL_QUERY", "UNSEEN")
PROMO_MAX_EMAILS = int(os.environ.get("PROMO_MAX_EMAILS", "3"))
PROMO_MARK_SEEN = os.environ.get("PROMO_MARK_SEEN", "1") == "1"
PROMO_POST_STATUS = os.environ.get("PROMO_POST_STATUS", "draft")
PROMO_SAMPLE_EMAIL_FILE = os.environ.get("PROMO_SAMPLE_EMAIL_FILE", "")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

CATEGORIES = {
    "electronics": 2,
    "tools": 3,
    "diy": 4,
}

AFFILIATE_DISCLOSURE = (
    '<div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;'
    'margin:24px 0 32px;font-size:0.88em;color:#555;border-radius:0 4px 4px 0;">'
    "<strong>Affiliate Disclosure:</strong> HandyTested is reader-supported. As an Amazon "
    "Associate, we earn from qualifying purchases. Prices and availability can change "
    "quickly, so we avoid listing fixed prices unless they are supplied directly by Amazon."
    "</div>"
)


@dataclass
class PromoEmail:
    uid: bytes
    subject: str
    sender: str
    date: str
    message_id: str
    text: str
    links: list[str]


def log(message: str) -> None:
    print(f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def telegram_send(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20):
            pass
    except Exception as exc:
        log(f"Telegram error: {exc}")


def openai_json(prompt: str, max_tokens: int = 1200) -> dict[str, Any]:
    raw = openai_text(prompt, max_tokens=max_tokens)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start < 0 or end <= start:
        raise RuntimeError(f"OpenAI did not return JSON: {raw[:300]}")
    return json.loads(raw[start:end])


def openai_text(prompt: str, max_tokens: int = 2800) -> str:
    body = json.dumps({
        "model": OPENAI_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    conn = http.client.HTTPSConnection("api.openai.com", timeout=120)
    try:
        conn.request("POST", "/v1/chat/completions", body=body, headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        })
        response = conn.getresponse()
        data = response.read()
        if response.status != 200:
            raise RuntimeError(f"OpenAI {response.status}: {data[:400]}")
        payload = json.loads(data)
        return payload["choices"][0]["message"]["content"].strip()
    finally:
        conn.close()


def wp_headers() -> dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "HandyTested Amazon promo agent",
    }


def wp_get(endpoint: str) -> Any:
    req = urllib.request.Request(f"{WP_URL}/wp-json/wp/v2{endpoint}", headers=wp_headers())
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def wp_post(endpoint: str, payload: dict[str, Any]) -> Any:
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=wp_headers(),
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts = email.header.decode_header(value)
    decoded = []
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(text)
    return "".join(decoded)


def html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p\s*>", "\n", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"[ \t\r\f\v]+", " ", value).strip()


def body_from_message(msg: Message) -> tuple[str, list[str]]:
    text_parts: list[str] = []
    html_parts: list[str] = []
    links: list[str] = []

    for part in msg.walk():
        content_type = part.get_content_type()
        disposition = str(part.get("Content-Disposition", "")).lower()
        if "attachment" in disposition:
            continue
        if content_type not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        decoded = payload.decode(charset, errors="replace")
        links.extend(re.findall(r'https?://[^\s"<>]+', decoded))
        if content_type == "text/plain":
            text_parts.append(decoded)
        else:
            html_parts.append(decoded)

    text = "\n\n".join(text_parts).strip()
    if not text and html_parts:
        text = "\n\n".join(html_to_text(part) for part in html_parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    links = sorted({clean_tracking_link(link) for link in links if "amazon" in link.lower()})
    return text[:12000], links[:40]


def clean_tracking_link(link: str) -> str:
    link = html.unescape(link).rstrip(").,;]")
    return link


def connect_mailbox() -> imaplib.IMAP4_SSL:
    socket.setdefaulttimeout(40)
    mailbox = imaplib.IMAP4_SSL(PROMO_EMAIL_IMAP_HOST, PROMO_EMAIL_IMAP_PORT)
    mailbox.login(PROMO_EMAIL_USER, PROMO_EMAIL_PASS)
    mailbox.select(PROMO_EMAIL_FOLDER)
    return mailbox


def fetch_promo_emails() -> list[PromoEmail]:
    if PROMO_SAMPLE_EMAIL_FILE:
        return [load_sample_email(PROMO_SAMPLE_EMAIL_FILE)]

    mailbox = connect_mailbox()
    try:
        status, data = mailbox.uid("search", None, PROMO_EMAIL_QUERY)
        if status != "OK":
            raise RuntimeError(f"IMAP search failed: {status} {data}")
        uids = data[0].split()[-PROMO_MAX_EMAILS:]
        emails: list[PromoEmail] = []
        for uid in uids:
            status, raw_data = mailbox.uid("fetch", uid, "(RFC822)")
            if status != "OK" or not raw_data or not raw_data[0]:
                continue
            msg = email.message_from_bytes(raw_data[0][1])
            text, links = body_from_message(msg)
            emails.append(PromoEmail(
                uid=uid,
                subject=decode_header_value(msg.get("Subject")),
                sender=decode_header_value(msg.get("From")),
                date=decode_header_value(msg.get("Date")),
                message_id=decode_header_value(msg.get("Message-ID")),
                text=text,
                links=links,
            ))
        return emails
    finally:
        mailbox.logout()


def load_sample_email(path: str) -> PromoEmail:
    raw = open(path, "rb").read()
    try:
        msg = email.message_from_bytes(raw)
        text, links = body_from_message(msg)
        subject = decode_header_value(msg.get("Subject")) or "Sample Amazon Associates promotion"
        sender = decode_header_value(msg.get("From")) or "sample@amazon.com"
        message_id = decode_header_value(msg.get("Message-ID")) or f"sample-{dt.date.today().isoformat()}"
        if text:
            return PromoEmail(
                uid=b"sample",
                subject=subject,
                sender=sender,
                date=decode_header_value(msg.get("Date")),
                message_id=message_id,
                text=text,
                links=links,
            )
    except Exception:
        pass

    text = raw.decode("utf-8", errors="replace")
    links = sorted({clean_tracking_link(link) for link in re.findall(r'https?://[^\s"<>]+', text)})
    return PromoEmail(
        uid=b"sample",
        subject="Sample Amazon Associates promotion",
        sender="sample@amazon.com",
        date=dt.date.today().isoformat(),
        message_id=f"sample-{dt.date.today().isoformat()}",
        text=text[:12000],
        links=links[:40],
    )


def mark_seen(uid: bytes) -> None:
    if not PROMO_MARK_SEEN or uid == b"sample":
        return
    mailbox = connect_mailbox()
    try:
        mailbox.uid("store", uid, "+FLAGS", "(\\Seen)")
    finally:
        mailbox.logout()


def amazon_search(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return f"https://{AMAZON_DOMAIN}/s?k={encoded}&tag={AMAZON_TAG}"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:70]


def already_published(slug: str) -> bool:
    posts = wp_get(f"/posts?slug={urllib.parse.quote(slug)}&status=publish,draft,future,pending&_fields=id")
    return bool(posts)


def classify_campaign(promo: PromoEmail) -> dict[str, Any]:
    prompt = f"""You are the editorial intake agent for HandyTested.com, an English-language Amazon affiliate review site for US buyers.

Read this Amazon Associates promotional email. Do NOT copy promotional wording. Extract the useful editorial opportunity.

EMAIL SUBJECT:
{promo.subject}

EMAIL FROM:
{promo.sender}

EMAIL TEXT:
{promo.text[:9000]}

AMAZON LINKS FOUND:
{json.dumps(promo.links[:20], ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "is_relevant": true,
  "campaign_name": "short human name",
  "campaign_angle": "what shoppers are being pushed toward",
  "primary_category": "electronics OR tools OR diy",
  "secondary_categories": ["electronics", "tools", "diy"],
  "buyer_intent_keyword": "4-7 word English keyword for US Google shoppers",
  "article_title": "SEO title, max 70 characters",
  "recommended_products_or_searches": [
    {{"name_or_query": "specific product type or model", "why_it_fits": "short reason"}},
    {{"name_or_query": "specific product type or model", "why_it_fits": "short reason"}},
    {{"name_or_query": "specific product type or model", "why_it_fits": "short reason"}},
    {{"name_or_query": "specific product type or model", "why_it_fits": "short reason"}}
  ],
  "avoid_claims": ["claims from the email that should not be repeated without verification"],
  "notes": "anything important for the writer"
}}

Rules:
- If the email is not about Amazon Associates promotions, set is_relevant false.
- HandyTested uses Amazon.com US affiliate links. Convert Brazil-only campaign ideas into US-relevant product searches when needed.
- Do not rely on fixed prices, fixed discount percentages, or copied Amazon creative assets.
"""
    return openai_json(prompt, max_tokens=1200)


def generate_article(campaign: dict[str, Any]) -> str:
    products = campaign["recommended_products_or_searches"]
    product_lines = "\n".join(
        f"- {item['name_or_query']}: {item.get('why_it_fits', '')}" for item in products
    )
    prompt = f"""You are writing for HandyTested.com, a practical product review and buying-guide site for US Amazon shoppers.

Create a helpful affiliate article from this campaign intake. Write in American English. The article should feel like editorial review guidance, not a copied promo email.

Campaign:
{json.dumps(campaign, ensure_ascii=False, indent=2)}

Product/search candidates:
{product_lines}

Strict rules:
- Output ONLY valid HTML. No markdown, no code fences.
- Start with <p>.
- Use only: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <table>, <thead>, <tbody>, <tr>, <th>, <td>, <a>.
- Do not mention exact prices or discount percentages.
- Do not say we physically tested products unless the article says "we look for", "we check", or "our review criteria".
- Add Amazon links using placeholders exactly like this: [AMAZON SEARCH: search query]
- Make it 900-1300 words.
- Include a practical buyer checklist, honest cautions, and a bottom-line recommendation.
- The first paragraph must include the primary keyword: {campaign['buyer_intent_keyword']}.

Structure:
Intro
Quick Picks table
Why these deals are worth checking
3-5 product/category sections
Buying checklist
Mistakes to avoid
Bottom line
"""
    article = openai_text(prompt, max_tokens=3000)
    article = re.sub(r"^```[a-z]*\s*", "", article.strip(), flags=re.IGNORECASE)
    article = re.sub(r"\s*```$", "", article)
    article = replace_amazon_placeholders(article)
    return AFFILIATE_DISCLOSURE + "\n" + article


def replace_amazon_placeholders(article: str) -> str:
    def repl(match: re.Match[str]) -> str:
        query = match.group(1).strip()
        url = amazon_search(query)
        label = html.escape(f"Check current Amazon options for {query}")
        return f'<a href="{url}" rel="nofollow sponsored noopener" target="_blank">{label}</a>'

    return re.sub(r"\[AMAZON SEARCH:\s*([^\]]+)\]", repl, article)


def publish_campaign_post(campaign: dict[str, Any], article_html: str, promo: PromoEmail) -> dict[str, Any]:
    title = campaign["article_title"]
    week_stamp = dt.date.today().isoformat()
    slug = slugify(f"{title} {week_stamp}")
    if already_published(slug):
        log(f"Skipping duplicate slug: {slug}")
        return {"skipped": True, "reason": "duplicate_slug", "slug": slug}

    category_slugs = [campaign.get("primary_category", "electronics")]
    category_slugs += campaign.get("secondary_categories", [])
    category_ids = []
    for slug_name in category_slugs:
        cat_id = CATEGORIES.get(slug_name)
        if cat_id and cat_id not in category_ids:
            category_ids.append(cat_id)
    if not category_ids:
        category_ids = [CATEGORIES["electronics"]]

    excerpt = (
        f"HandyTested turns this week's Amazon Associates campaign into practical buying guidance "
        f"for {campaign['buyer_intent_keyword']}."
    )
    payload = {
        "title": title,
        "slug": slug,
        "status": PROMO_POST_STATUS,
        "content": article_html,
        "excerpt": excerpt,
        "categories": category_ids,
    }
    try:
        return wp_post("/posts", payload)
    except Exception as exc:
        raise RuntimeError(f"WordPress publish failed for '{title}': {exc}") from exc


def run() -> None:
    log(f"Reading {PROMO_EMAIL_USER} via {PROMO_EMAIL_IMAP_HOST}")
    messages = fetch_promo_emails()
    if not messages:
        log("No new promo emails found.")
        return

    created = []
    for promo in messages:
        log(f"Processing: {promo.subject}")
        campaign = classify_campaign(promo)
        if not campaign.get("is_relevant"):
            log("Email is not relevant. Marking as seen.")
            mark_seen(promo.uid)
            continue
        article_html = generate_article(campaign)
        post = publish_campaign_post(campaign, article_html, promo)
        if not post.get("skipped"):
            created.append(post)
            log(f"Created {PROMO_POST_STATUS}: {post.get('link')}")
        mark_seen(promo.uid)

    if created:
        lines = ["<b>HandyTested Amazon Promo Agent</b>", f"Created {len(created)} {PROMO_POST_STATUS} post(s):"]
        for post in created:
            lines.append(f"- {html.escape(post['title']['rendered'])}: {post['link']}")
        telegram_send("\n".join(lines))


if __name__ == "__main__":
    run()
