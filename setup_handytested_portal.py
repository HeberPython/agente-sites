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
import json
import os
import urllib.parse
import urllib.request
from typing import Any


WP_URL = "https://handytested.com"
WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]


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
    meta = {}
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


def latest_posts_block(category_ids: list[int], posts_to_show: int = 3) -> str:
    attrs = {
        "categories": [{"id": category_id} for category_id in category_ids],
        "postsToShow": posts_to_show,
        "displayPostDate": True,
        "displayFeaturedImage": True,
        "featuredImageSizeSlug": "medium",
        "addLinkToFeaturedImage": True,
    }
    return f"<!-- wp:latest-posts {json.dumps(attrs, separators=(',', ':'))} /-->"


def home_content(cat_ids: dict[str, int]) -> str:
    latest = latest_posts_block([
        cat_ids["electronics"],
        cat_ids["tools"],
        cat_ids["diy"],
        cat_ids["smart-home"],
        cat_ids["kitchen"],
        cat_ids["outdoor"],
        cat_ids["cleaning"],
        cat_ids["office-gear"],
    ], 6)
    deals = latest_posts_block([cat_ids["amazon-deals"]], 4)
    tools = latest_posts_block([cat_ids["tools"]], 3)
    electronics = latest_posts_block([cat_ids["electronics"], cat_ids["smart-home"], cat_ids["office-gear"]], 3)
    home = latest_posts_block([cat_ids["diy"], cat_ids["kitchen"], cat_ids["cleaning"], cat_ids["outdoor"]], 3)

    return f"""
<div class="ht-portal" style="font-family:Inter,Arial,sans-serif;color:#172033;">
  <section style="padding:42px 24px 34px;background:#07153f;color:#fff;border-radius:0;margin:-24px -24px 34px;">
    <div style="max-width:1040px;margin:0 auto;">
      <p style="letter-spacing:.08em;text-transform:uppercase;font-size:12px;margin:0 0 10px;color:#f4b24d;">Independent buying guidance</p>
      <h1 style="font-size:42px;line-height:1.08;margin:0 0 14px;color:#fff;">Reviews before you buy tools, tech, and home gear.</h1>
      <p style="max-width:720px;font-size:18px;line-height:1.55;margin:0 0 24px;color:#dce5ff;">HandyTested turns product research, owner feedback, specs, safety signals, and Amazon deal trends into practical recommendations for real buyers.</p>
      <form role="search" method="get" action="/" style="display:flex;gap:10px;max-width:680px;flex-wrap:wrap;">
        <input type="search" name="s" placeholder="What are you looking for today?" style="flex:1;min-width:240px;padding:14px 16px;border-radius:4px;border:0;font-size:15px;">
        <button type="submit" style="background:#f4a62a;color:#07153f;border:0;border-radius:4px;padding:14px 26px;font-weight:700;">Search</button>
      </form>
    </div>
  </section>

  <section style="max-width:1040px;margin:0 auto 36px;">
    <div style="display:grid;grid-template-columns:2fr 1fr;gap:28px;">
      <div>
        <h2 style="font-size:22px;margin:0 0 14px;">Latest Reviews</h2>
        {latest}
      </div>
      <aside style="border-left:4px solid #f4a62a;padding-left:18px;">
        <h2 style="font-size:20px;margin:0 0 12px;">Top Amazon Deals</h2>
        <p style="font-size:14px;line-height:1.6;color:#536078;">Time-sensitive deal posts are reviewed by the promo agent and automatically removed from public view after expiration.</p>
        {deals}
        <p><a href="/deals/" style="font-weight:700;">View all deal guidance</a></p>
      </aside>
    </div>
  </section>

  <section style="max-width:1040px;margin:0 auto 34px;padding:28px 0;border-top:1px solid #e1e5ee;border-bottom:1px solid #e1e5ee;">
    <h2 style="font-size:22px;margin:0 0 16px;">Shop by Category</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;">
      <a href="/category/electronics/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">Electronics</a>
      <a href="/category/tools/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">Tools</a>
      <a href="/category/diy/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">DIY & Home</a>
      <a href="/category/smart-home/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">Smart Home</a>
      <a href="/category/kitchen/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">Kitchen</a>
      <a href="/category/outdoor/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">Outdoor</a>
      <a href="/category/cleaning/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">Cleaning</a>
      <a href="/category/office-gear/" style="padding:14px;border:1px solid #d8deeb;border-radius:6px;font-weight:700;">Office Gear</a>
    </div>
  </section>

  <section style="max-width:1040px;margin:0 auto 38px;">
    <h2 style="font-size:22px;margin:0 0 14px;">Tools & Workshop</h2>
    {tools}
    <h2 style="font-size:22px;margin:34px 0 14px;">Electronics & Smart Home</h2>
    {electronics}
    <h2 style="font-size:22px;margin:34px 0 14px;">Home, Kitchen & Outdoor</h2>
    {home}
  </section>

  <section style="padding:48px 24px;background:#07153f;color:#fff;border-radius:0;margin:42px -24px -24px;">
    <div style="max-width:880px;margin:0 auto;text-align:center;">
      <h2 style="font-size:28px;color:#fff;margin:0 0 12px;">Why trust HandyTested?</h2>
      <p style="font-size:16px;line-height:1.7;color:#dce5ff;max-width:720px;margin:0 auto 24px;">Our recommendations are built around practical buyer questions: what matters, what fails, who a product is best for, and when a cheaper option is enough.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:18px;text-align:left;">
        <div><h3 style="color:#f4b24d;margin:0 0 8px;">Clear criteria</h3><p style="color:#dce5ff;font-size:14px;line-height:1.6;">Specs, safety, warranty, owner feedback, and buyer fit.</p></div>
        <div><h3 style="color:#f4b24d;margin:0 0 8px;">No copied promos</h3><p style="color:#dce5ff;font-size:14px;line-height:1.6;">Amazon campaigns become editorial guidance, not pasted ads.</p></div>
        <div><h3 style="color:#f4b24d;margin:0 0 8px;">Stale deals expire</h3><p style="color:#dce5ff;font-size:14px;line-height:1.6;">Seasonal posts are removed when the promotion window closes.</p></div>
      </div>
      <p style="margin:28px 0 0;"><a href="/how-we-review/" style="background:#f4a62a;color:#07153f;padding:12px 22px;border-radius:4px;font-weight:700;text-decoration:none;">How we review</a></p>
    </div>
  </section>
</div>
""".strip()


def deals_content(deals_category_id: int) -> str:
    return f"""
<h1>Amazon Deals Worth Checking</h1>
<p><strong>Affiliate Disclosure:</strong> As an Amazon Associate, HandyTested earns from qualifying purchases.</p>
<p>This page collects our deal-driven buying guides. We do not list fixed prices or copy Amazon promotional images. When a deal is tied to a seasonal campaign, our agent stores an expiration marker and removes the post from public view after the promotion ends.</p>
<h2>Latest Deal Guides</h2>
{latest_posts_block([deals_category_id], 10)}
<h2>How to Use This Page</h2>
<ul>
  <li>Use deal guides as a shortlist, not as a final price guarantee.</li>
  <li>Check the Amazon product page for current price, shipping, seller, and availability.</li>
  <li>Prefer products with strong owner feedback, clear warranty terms, and easy returns.</li>
</ul>
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
