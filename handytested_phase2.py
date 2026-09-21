"""Reversible HandyTested homepage and navigation release through WordPress REST.

MODE=dry-run prints a plan without writes. MODE=apply stores original objects in
BACKUP_DIR before changing the homepage, primary menu, or footer widget.
"""

from __future__ import annotations

import base64
import html
import json
import os
from pathlib import Path
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request


BASE = "https://handytested.com"
API = BASE + "/wp-json/wp/v2"
MODE = os.environ.get("MODE", "dry-run")
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "handytested-phase2-backup"))
CSS = Path(__file__).with_name("handytested_phase2.css").read_text(encoding="utf-8")
TOKEN = base64.b64encode(f"hebergravano@gmail.com:{os.environ['HT_WP_PASS']}".encode()).decode()

TOP_SLUGS = (
    "best-cordless-drills-under-100",
    "best-random-orbital-sanders-for-diy-projects-2025",
    "best-smart-home-hubs-under-150-for-2025",
)
CATEGORY_COPY = (
    ("tools", "Tools", "Power tools, hand tools and workshop essentials."),
    ("diy", "DIY", "Gear for projects, repairs and home improvement."),
    ("electronics", "Electronics", "Useful tech, audio and everyday devices."),
    ("smart-home", "Smart Home", "Connected devices for a more practical home."),
    ("kitchen", "Kitchen", "Appliances and tools for everyday cooking."),
    ("cleaning", "Cleaning", "Cleaning equipment for home upkeep."),
    ("outdoor", "Outdoor", "Lawn, garden and outdoor gear."),
)
MENU = (
    ("Home", "/"),
    ("Best Picks", "/#top-picks"),
    ("Tools", "/category/tools/"),
    ("DIY", "/category/diy/"),
    ("Electronics", "/category/electronics/"),
    ("Learn", "/how-we-review/"),
    ("Value Picks", "/deals/"),
    ("Search", "/#site-search"),
)


def request(path: str, payload: dict | None = None) -> object:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        method="POST" if payload is not None else "GET",
        headers={
            "Authorization": f"Basic {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "HandyTested phase 2 release",
        },
    )
    for attempt in range(3 if payload is None else 1):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if payload is not None or exc.code not in {403, 429, 500, 502, 503, 504} or attempt == 2:
                raise
            print(f"Read {path} returned HTTP {exc.code}; retry {attempt + 1}/2", flush=True)
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            if payload is not None or attempt == 2:
                raise
            print(f"Read {path} failed ({type(exc).__name__}); retry {attempt + 1}/2", flush=True)
        time.sleep(1 + attempt * 2)
    raise RuntimeError("Read retries exhausted")


def backup(name: str, value: object) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / f"{name}.json").write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def clean(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("rendered", "")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", str(value)))).strip()


def get_post(slug: str) -> dict:
    data = request(f"/posts?{urllib.parse.urlencode({'slug': slug, '_embed': '1'})}")
    if not isinstance(data, list) or len(data) != 1:
        raise RuntimeError(f"Expected one published post for {slug}")
    return data[0]


def card(post: dict, label: str) -> str:
    title = html.escape(clean(post["title"]))
    link = html.escape(post["link"], quote=True)
    excerpt = clean(post.get("excerpt", ""))
    excerpt = html.escape(excerpt[:155].rsplit(" ", 1)[0] + "..." if len(excerpt) > 155 else excerpt)
    media = post.get("_embedded", {}).get("wp:featuredmedia", [{}])[0]
    sizes = media.get("media_details", {}).get("sizes", {})
    image = sizes.get("medium_large") or sizes.get("medium") or sizes.get("large") or {}
    if not image:
        raise RuntimeError(f"Featured image missing for {post['slug']}")
    src = html.escape(image["source_url"], quote=True)
    width = int(image["width"])
    height = int(image["height"])
    return f'''<article class="ht-card">
<a class="ht-card-media" href="{link}"><img src="{src}" width="{width}" height="{height}" alt="" loading="lazy" decoding="async"></a>
<div class="ht-card-body"><p class="ht-card-label">{html.escape(label)}</p><h3><a href="{link}">{title}</a></h3><p>{excerpt}</p><a class="ht-text-link" href="{link}">See Our Picks &#8594;</a></div>
</article>'''


def footer_html() -> str:
    columns = (
        ("Explore", (("Tools", "/category/tools/"), ("DIY", "/category/diy/"), ("Electronics", "/category/electronics/"), ("Smart Home", "/category/smart-home/"))),
        ("Resources", (("Best Picks", "/#top-picks"), ("Value Picks", "/deals/"), ("How We Review", "/how-we-review/"))),
        ("Company & Legal", (("About", "/about/"), ("Contact", "/contact/"), ("Editorial Policy", "/editorial-policy/"), ("Affiliate Disclosure", "/affiliate-disclosure/"), ("Privacy Policy", "/privacy-policy/"))),
    )
    links = "".join(
        "<div><h3>" + html.escape(title) + "</h3>" + "".join(
            f'<a href="{href}">{html.escape(label)}</a>' for label, href in items
        ) + "</div>" for title, items in columns
    )
    return f'''<div class="ht-global-footer"><div class="ht-footer-grid">
<div class="ht-footer-brand"><h2>HANDYTESTED</h2><p>Smarter product research for DIY, home and useful tech.</p></div>{links}
</div><p class="ht-footer-disclosure">As an Amazon Associate I earn from qualifying purchases.</p></div>'''


def home_html(categories: list[dict], posts: list[dict]) -> str:
    counts = {c["slug"]: c["count"] for c in categories}
    category_cards = "".join(
        f'<a class="ht-category" href="/category/{slug}/"><strong>{name}</strong><span>{description}</span></a>'
        for slug, name, description in CATEGORY_COPY if counts.get(slug, 0) > 0
    )
    top = "".join(card(post, label) for post, label in zip(posts, ("Tools", "DIY", "Smart Home")))
    latest_block = '<!-- wp:latest-posts {"postsToShow":6,"displayPostContent":true,"displayPostContentRadio":"excerpt","excerptLength":20,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageSizeSlug":"medium_large","addLinkToFeaturedImage":true,"className":"ht-latest-posts"} /-->'
    return f'''<style id="handytested-phase2-styles">{CSS}</style>
<main class="ht-home" id="ht-main">
<section class="ht-hero" aria-labelledby="ht-hero-title"><div class="ht-wrap"><p class="ht-eyebrow">HANDYTESTED / BUYING GUIDES</p><h1 id="ht-hero-title">Find the right tool.<br>Get the right price.</h1><p>We research tools, home gear and useful tech so you don't have to.</p><div class="ht-actions"><a class="ht-button ht-button-primary" href="#top-picks">Explore Our Picks</a><a class="ht-button ht-button-light" href="/deals/">Explore Value Picks</a></div></div></section>
<div class="ht-trust"><div class="ht-wrap"><span>Research-led picks</span><span>Clear comparisons</span><span>DIY focused</span><span>Affiliate transparency</span></div></div>
<section class="ht-section" id="top-picks"><div class="ht-wrap"><div class="ht-section-head"><div><p class="ht-eyebrow">START HERE</p><h2>Top Picks</h2><p>Focused guides for the gear people research before buying.</p></div><a class="ht-text-link" href="/category/tools/">Browse tools &#8594;</a></div><div class="ht-card-grid">{top}</div></div></section>
<section class="ht-section ht-section-alt" id="categories"><div class="ht-wrap"><div class="ht-section-head"><div><p class="ht-eyebrow">FIND YOUR CATEGORY</p><h2>Shop by Category</h2></div></div><div class="ht-category-grid">{category_cards}</div></div></section>
<section class="ht-section ht-latest" id="latest-guides"><div class="ht-wrap"><div class="ht-section-head"><div><p class="ht-eyebrow">FRESH RESEARCH</p><h2>Latest Guides</h2><p>Recently published buying guides, updated automatically by WordPress.</p></div></div>{latest_block}</div></section>
<section class="ht-section ht-section-alt" id="deals"><div class="ht-wrap ht-split"><div><p class="ht-eyebrow">SHOP SMARTER</p><h2>Value Picks</h2><p class="ht-section-intro">Compare useful products by task, package and trade-offs, then check the current listing before buying.</p><a class="ht-button ht-button-outline" href="/deals/">Explore Value Picks</a></div><div><p class="ht-eyebrow">BEFORE CHECKOUT</p><p class="ht-section-intro">Prices and availability change. Confirm the exact model, seller, shipping and current price on Amazon before you buy.</p></div></div></section>
<section class="ht-section ht-method" id="how-we-choose"><div class="ht-wrap ht-split"><div><p class="ht-eyebrow">OUR APPROACH</p><h2>How We Choose</h2><p class="ht-section-intro">We compare specifications, features, buyer feedback, brand reputation and overall value to help narrow down the options worth considering.</p><a class="ht-button ht-button-light" href="/how-we-review/">See Our Methodology</a></div><div id="site-search"><p class="ht-eyebrow">LOOKING FOR SOMETHING?</p><h2>Search the guides</h2><form class="ht-search" role="search" action="/" method="get"><label class="screen-reader-text" for="ht-search-input">Search HandyTested</label><input id="ht-search-input" type="search" name="s" placeholder="Tool, project or product" required><button class="ht-button ht-button-primary" type="submit">Search</button></form></div></div></section>
</main><footer class="ht-home-footer">{footer_html()}</footer>'''


def main() -> None:
    if MODE not in {"dry-run", "apply", "refresh-home"}:
        raise ValueError("MODE must be dry-run, apply, or refresh-home")
    pages = request("/pages?slug=home-page&context=edit&_fields=id,slug,content,status,meta")
    if not isinstance(pages, list) or len(pages) != 1 or pages[0]["status"] != "publish":
        raise RuntimeError("Expected one published home-page")
    home = pages[0]
    categories = request("/categories?per_page=100&_fields=id,slug,count")
    posts = [get_post(slug) for slug in TOP_SLUGS]
    content = home_html(categories, posts)
    if "<!-- wp:latest-posts " not in content or "handytested0d-20" in content:
        raise RuntimeError("Unexpected home content")
    if MODE == "refresh-home":
        backup("home", home)
        updated = request(f"/pages/{home['id']}", {"content": content})
        if updated.get("id") != home["id"]:
            raise RuntimeError("Homepage refresh not acknowledged")
        print("Refreshed homepage with editorial footer")
        return
    menus = request("/menus?context=edit")
    primary = next((m for m in menus if "primary" in m.get("locations", [])), None)
    if not primary:
        raise RuntimeError("Primary menu not found")
    items = request(f"/menu-items?menus={primary['id']}&per_page=100&context=edit")
    items.sort(key=lambda item: item["menu_order"])
    if len(items) != 5:
        raise RuntimeError(f"Expected five existing menu items, found {len(items)}")
    sidebars = request("/sidebars?context=edit")
    footer = next((s for s in sidebars if s["id"] == "footer-widget-1"), None)
    if not footer or footer["widgets"]:
        raise RuntimeError("Footer widget area is unavailable or occupied; refusing to overwrite it")
    print(f"Mode: {MODE}; home: {home['id']}; menu: {primary['id']}; footer: {footer['id']}")
    print("Homepage bytes:", len(content), "latest posts: native server-rendered block")
    print("Menu:", ", ".join(label for label, _ in MENU))
    if MODE == "dry-run":
        return
    backup("home", home)
    backup("menu", primary)
    backup("menu-items", items)
    backup("footer-sidebar", footer)
    updated = request(f"/pages/{home['id']}", {"content": content})
    if updated.get("id") != home["id"]:
        raise RuntimeError("Homepage update not acknowledged")
    print("Updated homepage")
    for order, (label, path) in enumerate(MENU, 1):
        payload = {"title": label, "url": BASE + path, "menu_order": order, "status": "publish", "menus": primary["id"]}
        if order <= 5:
            request(f"/menu-items/{items[order-1]['id']}", payload)
        else:
            payload["type"] = "custom"
            request("/menu-items", payload)
    request(f"/menus/{primary['id']}", {"locations": ["primary", "mobile_menu"]})
    print("Updated desktop and mobile menu")
    widget = request("/widgets", {"id_base": "block", "sidebar": "footer-widget-1", "instance": {"raw": {"content": '<!-- wp:html --><style id="handytested-phase2-global">' + CSS + '</style>' + footer_html() + '<!-- /wp:html -->'}}})
    print("Created footer widget:", widget.get("id"))


if __name__ == "__main__":
    main()
