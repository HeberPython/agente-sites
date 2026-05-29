"""
Set up HandyTested as a review portal instead of a plain post feed.

This script is idempotent:
- creates editorial categories and operational tags
- creates/updates trust pages
- updates the home page with a portal-style layout
- creates a Deals page backed by the Amazon Deals category

Required environment variable:
  HT_WP_PASS
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any


WP_URL = "https://handytested.com"
WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]
MEDIA_CACHE: dict[int, str] = {}


CATEGORIES = {
    "electronics": ("Electronics", "Reviews and comparisons of consumer electronics, gadgets, and tech accessories."),
    "tools": ("Tools & Equipment", "Reviews of power tools, hand tools, and workshop equipment."),
    "diy": ("DIY & Home Improvement", "Guides, product recommendations, and tips for DIY projects and home improvement."),
    "smart-home": ("Smart Home", "Smart home devices, home automation, security, and connected living gear."),
    "kitchen": ("Kitchen", "Kitchen tools, small appliances, cookware, and useful home food prep gear."),
    "outdoor": ("Outdoor", "Outdoor, lawn, garden, camping, and backyard gear reviews."),
    "cleaning": ("Cleaning", "Vacuums, cleaning tools, laundry gear, and home maintenance products."),
    "office-gear": ("Office Gear", "Home office equipment, desk accessories, printers, monitors, and productivity gear."),
    "amazon-deals": ("Amazon Deals", "Time-sensitive Amazon deal roundups and promo-driven buying guidance."),
}

TAGS = {
    "evergreen": "Evergreen",
    "pinterest-safe": "Pinterest Safe",
    "review-guide": "Review Guide",
    "deal": "Deal",
    "promo-email": "Promo Email",
    "seasonal": "Seasonal",
}


def wp_headers() -> dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "HandyTested portal setup",
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


def rank_math_post(payload: dict[str, Any]) -> Any:
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/rankmath/v1/updateMeta",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=wp_headers(),
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def update_rank_math_meta(object_id: int, seo_title: str = "", seo_description: str = "") -> None:
    meta = {}
    if seo_title:
        meta["rank_math_title"] = seo_title
    if seo_description:
        meta["rank_math_description"] = seo_description
        meta["rank_math_facebook_description"] = seo_description
        meta["rank_math_twitter_description"] = seo_description
    if seo_title:
        meta["rank_math_facebook_title"] = seo_title
        meta["rank_math_twitter_title"] = seo_title
    if not meta:
        return
    rank_math_post({"objectType": "post", "objectID": object_id, "meta": meta})


def ensure_term(taxonomy: str, slug: str, name: str, description: str = "") -> int:
    existing = wp_get(f"/{taxonomy}?slug={urllib.parse.quote(slug)}&_fields=id,slug")
    if existing:
        term_id = int(existing[0]["id"])
        payload: dict[str, Any] = {"name": name}
        if description:
            payload["description"] = description
        wp_post(f"/{taxonomy}/{term_id}", payload)
        return term_id

    payload = {"name": name, "slug": slug}
    if description:
        payload["description"] = description
    created = wp_post(f"/{taxonomy}", payload)
    return int(created["id"])


def ensure_page(
    slug: str,
    title: str,
    content: str,
    menu_order: int = 0,
    seo_title: str = "",
    seo_description: str = "",
    home_layout: bool = False,
) -> dict[str, Any]:
    existing = wp_get(f"/pages?slug={urllib.parse.quote(slug)}&status=publish,draft&_fields=id,slug")
    payload = {
        "title": title,
        "slug": slug,
        "status": "publish",
        "content": content,
        "comment_status": "closed",
        "menu_order": menu_order,
    }
    if home_layout:
        payload["featured_media"] = 0

    meta = {}
    if home_layout:
        meta.update({
            "site-post-title": "disabled",
            "ast-featured-img": "disabled",
            "ast-banner-title-visibility": "disabled",
            "ast-breadcrumbs-content": "disabled",
            "site-sidebar-layout": "no-sidebar",
            "ast-site-content-layout": "full-width-container",
            "site-content-style": "unboxed",
        })
    if seo_title:
        meta["rank_math_title"] = seo_title
    if seo_description:
        meta["rank_math_description"] = seo_description
    if meta:
        payload["meta"] = meta
    if existing:
        page = wp_post(f"/pages/{existing[0]['id']}", payload)
    else:
        page = wp_post("/pages", payload)
    update_rank_math_meta(int(page["id"]), seo_title, seo_description)
    return page


def rendered_text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("rendered", "")
    text = re.sub(r"<[^>]+>", " ", str(value))
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def trim_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    clipped = value[: max_chars - 1].rsplit(" ", 1)[0].strip()
    return f"{clipped}..."


def format_post_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value[:10]
    return parsed.strftime("%b %d, %Y")


def media_url(media_id: int) -> str:
    if not media_id:
        return ""
    if media_id in MEDIA_CACHE:
        return MEDIA_CACHE[media_id]

    try:
        media = wp_get(f"/media/{media_id}?_fields=source_url,media_details")
    except Exception:
        MEDIA_CACHE[media_id] = ""
        return ""

    sizes = media.get("media_details", {}).get("sizes", {})
    for size in ("medium_large", "large", "medium", "thumbnail"):
        source = sizes.get(size, {}).get("source_url")
        if source:
            MEDIA_CACHE[media_id] = source
            return source

    source = media.get("source_url", "")
    MEDIA_CACHE[media_id] = source
    return source


def fetch_posts(
    category_ids: list[int],
    per_page: int,
    exclude_category_ids: list[int] | None = None,
) -> list[dict[str, str]]:
    params = {
        "status": "publish",
        "per_page": str(per_page),
        "orderby": "date",
        "order": "desc",
        "_fields": "id,date,link,title,excerpt,featured_media,categories",
    }
    if category_ids:
        params["categories"] = ",".join(str(category_id) for category_id in category_ids)
    if exclude_category_ids:
        params["categories_exclude"] = ",".join(str(category_id) for category_id in exclude_category_ids)

    raw_posts = wp_get(f"/posts?{urllib.parse.urlencode(params)}")
    posts = []
    for post in raw_posts:
        title = rendered_text(post.get("title", ""))
        if not title:
            continue
        posts.append({
            "title": title,
            "excerpt": trim_text(rendered_text(post.get("excerpt", "")), 132),
            "url": str(post.get("link", "#")),
            "date": format_post_date(str(post.get("date", ""))),
            "image": media_url(int(post.get("featured_media") or 0)),
        })
    return posts


def image_markup(post: dict[str, str], height: int) -> str:
    title = html.escape(post["title"], quote=True)
    image = post.get("image", "")
    if image:
        return (
            f'<img src="{html.escape(image, quote=True)}" alt="{title}" '
            f'style="width:100%;height:{height}px;object-fit:cover;display:block;background:#e9edf5;">'
        )
    return (
        f'<div aria-hidden="true" style="height:{height}px;background:#edf1f7;'
        'display:flex;align-items:center;justify-content:center;color:#516078;'
        'font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;">'
        "HandyTested</div>"
    )


def render_feature(post: dict[str, str] | None) -> str:
    if not post:
        return empty_panel("New review guides are being prepared.")
    title = html.escape(post["title"])
    url = html.escape(post["url"], quote=True)
    excerpt = html.escape(post["excerpt"])
    date = html.escape(post["date"])
    return f"""
<article style="border-bottom:1px solid #dfe5ef;padding-bottom:18px;">
  <a href="{url}" style="display:block;text-decoration:none;color:#172033;">{image_markup(post, 255)}</a>
  <p style="font-size:12px;color:#68748a;margin:12px 0 6px;">{date}</p>
  <h3 style="font-size:26px;line-height:1.18;margin:0 0 8px;color:#172033;"><a href="{url}" style="color:#172033;text-decoration:none;">{title}</a></h3>
  <p style="font-size:15px;line-height:1.6;color:#4b5870;margin:0;">{excerpt}</p>
</article>
""".strip()


def render_card_grid(posts: list[dict[str, str]], empty_message: str) -> str:
    if not posts:
        return empty_panel(empty_message)
    cards = []
    for post in posts:
        title = html.escape(post["title"])
        url = html.escape(post["url"], quote=True)
        excerpt = html.escape(post["excerpt"])
        date = html.escape(post["date"])
        cards.append(f"""
<article style="border:1px solid #dfe5ef;background:#fff;">
  <a href="{url}" style="display:block;text-decoration:none;color:#172033;">{image_markup(post, 142)}</a>
  <div style="padding:13px 14px 15px;">
    <p style="font-size:11px;color:#68748a;margin:0 0 6px;">{date}</p>
    <h3 style="font-size:17px;line-height:1.25;margin:0 0 7px;color:#172033;"><a href="{url}" style="color:#172033;text-decoration:none;">{title}</a></h3>
    <p style="font-size:13px;line-height:1.5;color:#4b5870;margin:0;">{excerpt}</p>
  </div>
</article>
""".strip())
    return (
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));'
        'gap:18px;">'
        + "\n".join(cards)
        + "</div>"
    )


def render_compact_list(posts: list[dict[str, str]], empty_message: str) -> str:
    if not posts:
        return empty_panel(empty_message)
    items = []
    for post in posts:
        title = html.escape(post["title"])
        url = html.escape(post["url"], quote=True)
        date = html.escape(post["date"])
        image = image_markup(post, 68)
        items.append(f"""
<article style="display:grid;grid-template-columns:82px 1fr;gap:12px;border-bottom:1px solid #e6ebf3;padding:0 0 13px;margin:0 0 13px;">
  <a href="{url}" style="display:block;text-decoration:none;">{image}</a>
  <div>
    <p style="font-size:11px;color:#68748a;margin:0 0 4px;">{date}</p>
    <h3 style="font-size:14px;line-height:1.3;margin:0;color:#172033;"><a href="{url}" style="color:#172033;text-decoration:none;">{title}</a></h3>
  </div>
</article>
""".strip())
    return "\n".join(items)


def render_deal_rail(deals: list[dict[str, str]], fallback_posts: list[dict[str, str]]) -> str:
    fallback_title = "Recent Buying Guides" if not deals else "More Buying Guides"
    return f"""
<aside class="ht-side-rail">
  <h2 style="font-size:20px;margin:0 0 10px;color:#172033;">Top Amazon Deals</h2>
  <p style="font-size:14px;line-height:1.6;color:#536078;margin:0 0 16px;">Time-sensitive deal posts are reviewed by the promo agent and removed from public view after the campaign expires.</p>
  {render_compact_list(deals, "No active deal guides are live right now.")}
  <p style="margin:8px 0 18px;"><a href="/deals/" style="font-weight:700;color:#0a3a78;text-decoration:none;">View all deal guidance</a></p>

  <div style="border-top:1px solid #e1e5ee;padding-top:18px;margin-top:18px;">
    <h2 style="font-size:18px;margin:0 0 12px;color:#172033;">{fallback_title}</h2>
    {render_compact_list(fallback_posts, "More buying guides are coming next.")}
  </div>

  <div style="background:#f7f9fc;border:1px solid #dfe5ef;padding:16px;margin-top:18px;">
    <h3 style="font-size:16px;margin:0 0 8px;color:#172033;">Before You Buy</h3>
    <p style="font-size:13px;line-height:1.6;color:#536078;margin:0;">We avoid fixed prices and stale discount claims. Always confirm current price, seller, shipping, and returns on Amazon before checkout.</p>
  </div>
</aside>
""".strip()


def empty_panel(message: str) -> str:
    return (
        '<div style="border:1px solid #dfe5ef;background:#f7f9fc;padding:16px;'
        'color:#526078;font-size:14px;line-height:1.55;">'
        f"{html.escape(message)}</div>"
    )


def portal_css() -> str:
    return """
<style>
body.home .entry-header,
body.home .post-thumb-img-content {
  display: none !important;
}
body.home .entry-content,
body.home #primary {
  margin-top: 0 !important;
}
.ht-portal a:hover {
  text-decoration: underline !important;
}
.ht-portal .ht-lead-grid {
  align-items: start !important;
  display: grid !important;
  gap: 28px !important;
  grid-template-columns: minmax(0, 1.7fr) minmax(300px, .9fr) !important;
}
.ht-portal .ht-side-rail {
  border-left: 4px solid #f2a733 !important;
  padding-left: 18px !important;
}
.ht-portal .ht-full-bleed {
  margin-left: calc(50% - 50vw) !important;
  margin-right: calc(50% - 50vw) !important;
}
.ht-portal .ht-full-bleed-inner {
  box-sizing: border-box !important;
  margin-left: auto !important;
  margin-right: auto !important;
  max-width: 1200px !important;
  padding-left: 28px !important;
  padding-right: 28px !important;
}
.ht-portal .ht-category-grid {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  gap: 12px !important;
}
.ht-portal .ht-category-card {
  min-width: 0 !important;
}
.ht-portal .ht-category-card a {
  align-items: center !important;
  background: #fff !important;
  border: 1px solid #d8deeb !important;
  box-sizing: border-box !important;
  color: #172033 !important;
  display: flex !important;
  font-weight: 700 !important;
  min-height: 56px !important;
  padding: 13px 14px !important;
  text-decoration: none !important;
  width: 100% !important;
}
@media (max-width: 820px) {
  .ht-portal .ht-lead-grid {
    grid-template-columns: 1fr !important;
  }
  .ht-portal .ht-side-rail {
    border-left: 0 !important;
    border-top: 4px solid #f2a733 !important;
    padding-left: 0 !important;
    padding-top: 18px !important;
  }
  .ht-portal .ht-category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}
@media (max-width: 640px) {
  .ht-portal .ht-hero-inner {
    padding: 30px 18px !important;
  }
  .ht-portal .ht-hero h1 {
    font-size: 31px !important;
  }
  .ht-portal .ht-category-grid {
    grid-template-columns: 1fr !important;
  }
}
</style>
""".strip()


def category_links() -> str:
    categories = [
        ("Electronics", "/category/electronics/"),
        ("Tools", "/category/tools/"),
        ("DIY & Home", "/category/diy/"),
        ("Smart Home", "/category/smart-home/"),
        ("Kitchen", "/category/kitchen/"),
        ("Outdoor", "/category/outdoor/"),
        ("Cleaning", "/category/cleaning/"),
        ("Office Gear", "/category/office-gear/"),
    ]
    links = [
        f'<div class="ht-category-card"><a href="{href}">{label}</a></div>'
        for label, href in categories
    ]
    return "\n".join(links)


def home_content(cat_ids: dict[str, int]) -> str:
    evergreen_ids = [
        cat_ids["electronics"],
        cat_ids["tools"],
        cat_ids["diy"],
        cat_ids["smart-home"],
        cat_ids["kitchen"],
        cat_ids["outdoor"],
        cat_ids["cleaning"],
        cat_ids["office-gear"],
    ]
    deal_id = cat_ids["amazon-deals"]
    latest = fetch_posts(evergreen_ids, 7, [deal_id])
    deals = fetch_posts([deal_id], 4)
    tools = fetch_posts([cat_ids["tools"]], 3, [deal_id])
    electronics = fetch_posts([cat_ids["electronics"], cat_ids["smart-home"], cat_ids["office-gear"]], 3, [deal_id])
    home = fetch_posts([cat_ids["diy"], cat_ids["kitchen"], cat_ids["cleaning"], cat_ids["outdoor"]], 3, [deal_id])

    return f"""
{portal_css()}
<div class="ht-portal" style="font-family:Arial,sans-serif;color:#172033;max-width:1200px;margin:0 auto;">
  <section class="ht-hero ht-full-bleed" style="background:#07153f;color:#fff;margin-top:0;margin-bottom:34px;">
    <div class="ht-hero-inner ht-full-bleed-inner" style="padding-top:42px;padding-bottom:36px;">
      <p style="letter-spacing:.08em;text-transform:uppercase;font-size:12px;margin:0 0 10px;color:#f2b34c;font-weight:700;">Independent buying guidance</p>
      <h1 style="font-size:42px;line-height:1.08;margin:0 0 14px;color:#fff;">Reviews before you buy tools, tech, and home gear.</h1>
      <p style="max-width:740px;font-size:18px;line-height:1.55;margin:0 0 24px;color:#dce5ff;">HandyTested turns product research, owner feedback, specs, safety signals, and Amazon deal trends into practical recommendations for real buyers.</p>
      <form role="search" method="get" action="/" style="display:flex;gap:10px;max-width:690px;flex-wrap:wrap;">
        <input type="search" name="s" placeholder="What are you looking for today?" style="flex:1;min-width:240px;padding:14px 16px;border:0;font-size:15px;">
        <button type="submit" style="background:#f2a733;color:#07153f;border:0;padding:14px 26px;font-weight:700;">Search</button>
      </form>
    </div>
  </section>

  <section style="margin:0 0 34px;">
    <div class="ht-lead-grid">
      <div>
        <h2 style="font-size:22px;letter-spacing:.02em;margin:0 0 14px;color:#172033;">Latest Reviews</h2>
        {render_feature(latest[0] if latest else None)}
        <div style="margin-top:18px;">{render_card_grid(latest[1:4], "More review guides are coming next.")}</div>
      </div>
      {render_deal_rail(deals, latest[4:7])}
    </div>
  </section>

  <section style="margin:0 0 34px;padding:26px 0;border-top:1px solid #e1e5ee;border-bottom:1px solid #e1e5ee;">
    <h2 style="font-size:22px;margin:0 0 16px;color:#172033;">Shop by Category</h2>
    <div class="ht-category-grid">
      {category_links()}
    </div>
  </section>

  <section style="margin:0 0 38px;">
    <h2 style="font-size:22px;margin:0 0 14px;color:#172033;">Tools & Workshop</h2>
    {render_card_grid(tools, "Tool and workshop reviews are being prepared.")}
    <h2 style="font-size:22px;margin:34px 0 14px;color:#172033;">Electronics & Smart Home</h2>
    {render_card_grid(electronics, "Electronics and smart home guides are being prepared.")}
    <h2 style="font-size:22px;margin:34px 0 14px;color:#172033;">Home, Kitchen & Outdoor</h2>
    {render_card_grid(home, "Home, kitchen, and outdoor guides are being prepared.")}
  </section>

  <section style="padding:42px 28px;background:#07153f;color:#fff;margin:38px 0 0;">
    <div style="max-width:880px;margin:0 auto;text-align:center;">
      <h2 style="font-size:28px;color:#fff;margin:0 0 12px;">Why trust HandyTested?</h2>
      <p style="font-size:16px;line-height:1.7;color:#dce5ff;max-width:720px;margin:0 auto 24px;">Our recommendations are built around practical buyer questions: what matters, what fails, who a product is best for, and when a simpler option is enough.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:18px;text-align:left;">
        <div><h3 style="color:#f2b34c;margin:0 0 8px;font-size:17px;">Clear criteria</h3><p style="color:#dce5ff;font-size:14px;line-height:1.6;margin:0;">Specs, safety, warranty, owner feedback, and buyer fit.</p></div>
        <div><h3 style="color:#f2b34c;margin:0 0 8px;font-size:17px;">No copied promos</h3><p style="color:#dce5ff;font-size:14px;line-height:1.6;margin:0;">Amazon campaigns become editorial guidance, not pasted ads.</p></div>
        <div><h3 style="color:#f2b34c;margin:0 0 8px;font-size:17px;">Stale deals expire</h3><p style="color:#dce5ff;font-size:14px;line-height:1.6;margin:0;">Seasonal posts are removed when the promotion window closes.</p></div>
      </div>
      <p style="margin:28px 0 0;"><a href="/how-we-review/" style="background:#f2a733;color:#07153f;padding:12px 22px;font-weight:700;text-decoration:none;">How we review</a></p>
    </div>
  </section>
</div>
""".strip()


def deals_content(deals_category_id: int) -> str:
    deals = fetch_posts([deals_category_id], 10)
    return f"""
<div style="max-width:1040px;margin:0 auto;font-family:Arial,sans-serif;color:#172033;">
  <h1>Amazon Deals Worth Checking</h1>
  <p><strong>Affiliate Disclosure:</strong> As an Amazon Associate, HandyTested earns from qualifying purchases.</p>
  <p>This page collects our deal-driven buying guides. We do not list fixed prices or copy Amazon promotional images. When a deal is tied to a seasonal campaign, our agent stores an expiration marker and removes the post from public view after the promotion ends.</p>
  <h2>Latest Deal Guides</h2>
  {render_card_grid(deals, "No active deal guides are live right now.")}
  <h2>How to Use This Page</h2>
  <ul>
    <li>Use deal guides as a shortlist, not as a final price guarantee.</li>
    <li>Check the Amazon product page for current price, shipping, seller, and availability.</li>
    <li>Prefer products with strong owner feedback, clear warranty terms, and easy returns.</li>
  </ul>
</div>
""".strip()


HOW_WE_REVIEW = """
<h1>How We Review Products</h1>
<p>HandyTested exists to help shoppers make faster, calmer buying decisions. Our reviews focus on practical fit: who a product is for, what tradeoffs matter, and when a cheaper or simpler option is enough.</p>
<h2>Our Review Criteria</h2>
<ul>
  <li><strong>Use case:</strong> We start with the job the product needs to do.</li>
  <li><strong>Specifications:</strong> We compare meaningful specs instead of marketing claims.</li>
  <li><strong>Owner feedback:</strong> We look for patterns in recent reviews, especially durability, support, and returns.</li>
  <li><strong>Safety and reliability:</strong> We pay special attention to tools, heating products, batteries, and electrical gear.</li>
  <li><strong>Value:</strong> We consider whether the product earns its place against cheaper and more expensive alternatives.</li>
</ul>
<h2>Testing and Research Notes</h2>
<p>Some articles are based on direct hands-on evaluation. Others are research-led buying guides built from specifications, verified owner feedback, seller signals, and category expertise. We do not claim physical testing unless it actually happened.</p>
<h2>Affiliate Independence</h2>
<p>HandyTested may earn commissions from Amazon links, but products cannot pay for positive coverage. Affiliate earnings do not change the criteria we use to recommend or reject a product.</p>
""".strip()


EDITORIAL_POLICY = """
<h1>Editorial Policy</h1>
<p>HandyTested publishes product reviews, comparisons, buying guides, and deal-driven shopping guidance for tools, electronics, DIY, home, and everyday gear.</p>
<h2>What We Publish</h2>
<ul>
  <li>Evergreen reviews and comparisons for products people actively research before buying.</li>
  <li>Buying guides that explain the tradeoffs between features, budgets, and use cases.</li>
  <li>Deal guides inspired by Amazon Associates campaigns, rewritten as original editorial guidance.</li>
</ul>
<h2>What We Avoid</h2>
<ul>
  <li>Copying Amazon promotional emails or product images into editorial content.</li>
  <li>Publishing fixed prices or discount claims unless supplied through approved live Amazon tooling.</li>
  <li>Leaving expired seasonal deal pages public after the promotion window closes.</li>
</ul>
<h2>Corrections</h2>
<p>If a recommendation is unclear, outdated, or wrong, contact us through the Contact page and we will review it.</p>
""".strip()


AFFILIATE_DISCLOSURE_PAGE = """
<h1>Affiliate Disclosure</h1>
<p>HandyTested is reader-supported. As an Amazon Associate, we earn from qualifying purchases.</p>
<p>This means that when you click an Amazon link on HandyTested and make a purchase, we may receive a commission at no extra cost to you.</p>
<h2>How This Affects Reviews</h2>
<p>Affiliate relationships do not determine whether a product is recommended. Our content is built around buyer fit, useful specifications, owner feedback, safety signals, warranty support, and practical value.</p>
<h2>Prices and Availability</h2>
<p>Amazon prices and availability change frequently. HandyTested avoids publishing fixed prices unless they are supplied directly through approved Amazon tools. Always confirm final price, seller, shipping, and return terms on Amazon before buying.</p>
""".strip()


def about_content() -> str:
    return """
<h1>About HandyTested</h1>
<p>HandyTested helps shoppers choose tools, electronics, DIY gear, smart home products, kitchen tools, and everyday home equipment with less guesswork.</p>
<p>We focus on practical recommendations: what is worth buying, who it is best for, what tradeoffs matter, and what to check before clicking purchase.</p>
<h2>Our Promise</h2>
<ul>
  <li>Clear buyer guidance instead of generic product roundups.</li>
  <li>Honest pros and cons for each recommendation.</li>
  <li>Seasonal deal content that expires when it should.</li>
  <li>Transparent affiliate disclosure.</li>
</ul>
<p>Learn more about <a href="/how-we-review/">how we review products</a>, our <a href="/editorial-policy/">editorial policy</a>, and our <a href="/affiliate-disclosure/">affiliate disclosure</a>.</p>
""".strip()


def main() -> None:
    category_ids = {
        slug: ensure_term("categories", slug, name, description)
        for slug, (name, description) in CATEGORIES.items()
    }
    tag_ids = {slug: ensure_term("tags", slug, name) for slug, name in TAGS.items()}

    home = ensure_page(
        "home-page",
        "Home",
        home_content(category_ids),
        0,
        "HandyTested - Product Reviews, Buying Guides & Amazon Deals",
        "Practical product reviews, buying guides, and Amazon deal guidance for tools, electronics, smart home, DIY, kitchen, and everyday gear.",
        home_layout=True,
    )
    ensure_page(
        "deals",
        "Amazon Deals",
        deals_content(category_ids["amazon-deals"]),
        10,
        "Amazon Deals Worth Checking - HandyTested",
        "HandyTested deal guides turn Amazon promotions into practical buying advice without copied promo text, fixed prices, or stale campaign pages.",
    )
    ensure_page(
        "how-we-review",
        "How We Review",
        HOW_WE_REVIEW,
        20,
        "How HandyTested Reviews Products",
        "Learn how HandyTested evaluates products using specifications, owner feedback, safety signals, warranties, use cases, and practical value.",
    )
    ensure_page(
        "editorial-policy",
        "Editorial Policy",
        EDITORIAL_POLICY,
        30,
        "Editorial Policy - HandyTested",
        "Read HandyTested's editorial standards for reviews, buying guides, Amazon deal coverage, corrections, and affiliate independence.",
    )
    ensure_page(
        "affiliate-disclosure",
        "Affiliate Disclosure",
        AFFILIATE_DISCLOSURE_PAGE,
        40,
        "Affiliate Disclosure - HandyTested",
        "HandyTested is reader-supported and may earn from qualifying Amazon purchases while keeping recommendations editorially independent.",
    )
    ensure_page(
        "about",
        "About HandyTested",
        about_content(),
        50,
        "About HandyTested",
        "HandyTested helps shoppers choose tools, electronics, DIY gear, smart home products, kitchen tools, and everyday home equipment.",
    )

    try:
        wp_post("/settings", {"show_on_front": "page", "page_on_front": home["id"]})
    except Exception as exc:
        print(f"Settings update warning: {exc}")

    print(json.dumps({
        "categories": category_ids,
        "tags": tag_ids,
        "home": home["link"],
    }, indent=2))


if __name__ == "__main__":
    main()
