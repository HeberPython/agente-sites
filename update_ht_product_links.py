"""
Add tagged Amazon search links for discussed models to existing posts.

The update is idempotent: each run replaces the managed block between markers
instead of appending duplicates. Links use the current Amazon Associates tag.
"""
from __future__ import annotations

import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


WP_URL = "https://handytested.com"
WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]
AMAZON_TAG = os.environ.get("HT_AMAZON_TAG", "handytested0d-20")
AMAZON_DOMAIN = os.environ.get("HT_AMAZON_DOMAIN", "www.amazon.com")
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

START_MARKER = "<!-- handytested-product-links:start -->"
END_MARKER = "<!-- handytested-product-links:end -->"


PRODUCTS_BY_SLUG: dict[str, list[str]] = {
    "best-cordless-drills-under-100": [
        "DEWALT DCD771C2 20V MAX cordless drill driver kit",
        "BLACK+DECKER LD120VA 20V MAX drill driver kit",
        "CRAFTSMAN CMCD700C1 V20 cordless drill driver kit",
    ],
    "best-wireless-earbuds-under-100-for-2025": [
        "Soundcore by Anker Space A40 earbuds",
        "JBL Vibe Beam true wireless earbuds",
        "EarFun Air Pro 3 wireless earbuds",
    ],
    "best-oscillating-multi-tools-under-75-for-2025": [
        "DEWALT DCS356B oscillating multi tool",
        "WEN 2312 variable speed oscillating multi tool",
        "Genesis GMT15A oscillating multi purpose tool",
    ],
    "best-laser-levels-for-diy-home-projects-under-60": [
        "Bosch GLL30 laser level",
        "Huepar BOX-1G green laser level",
        "BLACK+DECKER BDL220S laser level",
    ],
    "best-random-orbital-sanders-for-diy-projects-2025": [
        "DEWALT DCW210B 20V MAX orbital sander",
        "Makita BO5041K random orbit sander",
        "BLACK+DECKER BDERO100 random orbit sander",
    ],
    "best-smart-home-hubs-under-150-for-2025": [
        "Amazon Echo Hub smart home control panel",
        "Aeotec Smart Home Hub",
        "Amazon Echo Show 8 smart display",
    ],
    "best-stud-finders-under-50-for-home-projects-2025": [
        "Franklin Sensors ProSensor M90 stud finder",
        "Zircon StudSensor A100 stud finder",
        "CRAFTSMAN stud finder CMHT77623",
    ],
    "best-rotary-tools-under-50-for-diy-projects-2025": [
        "Dremel 3000-1/25 variable speed rotary tool kit",
        "WEN 2305 rotary tool kit with flex shaft",
        "Avid Power rotary tool kit 6 speed",
    ],
    "best-voltage-testers-for-home-electrical-work-2025": [
        "Klein Tools NCVT-3P voltage tester",
        "Fluke 1AC II non contact voltage tester",
        "Southwire 40150N advanced AC non contact voltage tester",
    ],
    "best-multimeters-under-50-for-home-electricians-2025": [
        "AstroAI digital multimeter TRMS 6000",
        "Klein Tools MM400 digital multimeter",
        "Fluke 101 digital multimeter",
    ],
    "best-heat-guns-for-diy-projects-under-80-in-2025": [
        "Wagner Spraytech HT1000 heat gun",
        "SEEKONE 1800W heat gun",
        "DEWALT D26950 heat gun",
    ],
    "best-cordless-circular-saws-under-150-for-diy-projects": [
        "DEWALT DCS570B 20V MAX circular saw",
        "Ryobi P508 18V ONE+ brushless circular saw",
        "Makita XSS02Z 18V LXT circular saw",
    ],
    "top-5-digital-torque-wrenches-under-100-for-accurate-torque": [
        "EPAuto 3/8 inch digital torque wrench",
        "ACDelco ARM601-3 digital torque wrench",
        "GEARWRENCH 85077 electronic torque wrench",
    ],
    "best-home-drill-presses-under-300-for-diy-enthusiasts": [
        "WEN 4214T 12 inch variable speed drill press",
        "SKIL DP9505-00 10 inch drill press",
        "Shop Fox W1668 drill press",
    ],
    "best-noise-canceling-headphones-under-300-for-2025": [
        "Sony WH-1000XM5 noise canceling headphones",
        "Bose QuietComfort wireless noise cancelling headphones",
        "Soundcore Space Q45 noise cancelling headphones",
    ],
    "best-smart-tvs-under-300-for-2025-viewing-experience": [
        "TCL 50 inch Class S4 4K Roku TV",
        "Hisense 50 inch A6 Series 4K Google TV",
        "Amazon Fire TV 50 inch 4-Series 4K UHD",
    ],
    "best-electric-screwdrivers-for-diy-projects-in-2025": [
        "SKIL SD561201 cordless screwdriver",
        "BLACK+DECKER LI2000 cordless screwdriver",
        "WORX WX240L 4V cordless screwdriver",
    ],
    "best-cordless-ratchets-for-diy-mechanics-in-2025": [
        "Milwaukee 2457-21 M12 cordless ratchet kit",
        "ACDelco ARW1201 G12 cordless ratchet wrench",
        "KIMO 3/8 cordless electric ratchet wrench",
    ],
    "top-5-home-diy-paint-sprayers-under-300-in-2025": [
        "Graco Magnum X5 airless paint sprayer",
        "Wagner Control Pro 130 paint sprayer",
        "HomeRight Super Finish Max paint sprayer",
    ],
    "best-home-diy-tool-sets-for-under-300-in-2025": [
        "CRAFTSMAN 230 piece mechanics tool set",
        "DEKOPRO 228 piece tool set",
        "Amazon Basics 142 piece household tool kit",
    ],
    "best-smart-home-security-cameras-under-300-for-2025": [
        "Ring Stick Up Cam Battery",
        "Blink Outdoor 4 security camera",
        "Arlo Essential 2K outdoor security camera",
    ],
    "best-kitchen-appliances-under-300-for-home-chefs": [
        "Ninja AF101 air fryer",
        "Instant Pot Duo Plus 9-in-1 pressure cooker",
        "Ninja BN701 Professional Plus blender",
    ],
    "best-camping-gear-under-300-for-outdoor-adventures": [
        "Coleman Sundome camping tent",
        "TETON Sports Celsius XXL sleeping bag",
        "Coleman Triton 2 burner propane camping stove",
    ],
    "best-cordless-nail-guns-under-300-for-diy-projects": [
        "RYOBI P320 Airstrike brad nailer",
        "DEWALT DCN680B cordless brad nailer",
        "CRAFTSMAN CMCN618C1 cordless brad nailer kit",
    ],
    "best-carpet-cleaners-for-pet-owners-in-2025": [
        "BISSELL Little Green Pet Deluxe portable carpet cleaner",
        "Hoover PowerDash Pet Compact carpet cleaner",
        "BISSELL Revolution HydroSteam Pet carpet cleaner",
    ],
    "top-5-ergonomic-office-chairs-under-300-for-comfort": [
        "SIHOO M18 ergonomic office chair",
        "HON Ignition 2.0 ergonomic office chair",
        "FlexiSpot OC3B ergonomic office chair",
    ],
    "best-projectors-under-300-for-home-entertainment": [
        "Anker Nebula Capsule projector",
        "YABER Pro V9 projector",
        "WiMiUS K9 projector",
    ],
    "best-cordless-impact-wrenches-under-300-for-2025": [
        "DEWALT DCF899HB 20V MAX impact wrench",
        "Milwaukee 2767-20 M18 FUEL impact wrench",
        "Ryobi P262 ONE+ HP impact wrench",
    ],
    "best-diy-outdoor-furniture-kits-under-300-for-2025": [
        "Keter Solana 70 gallon storage bench",
        "Walker Edison outdoor wood patio bench",
        "Giantex 3 piece patio furniture set",
    ],
    "best-smart-home-devices-under-300-for-2025": [
        "Amazon Echo Show 8",
        "Ring Battery Doorbell Plus",
        "Kasa Smart Plug HS103P4",
    ],
    "best-kitchen-gadgets-under-300-for-modern-chefs": [
        "ThermoPro TP19H digital meat thermometer",
        "Ninja CREAMi ice cream maker",
        "FoodSaver vacuum sealer machine",
    ],
    "top-smart-home-automation-devices-under-300-for-2025": [
        "Amazon Echo Hub smart home control panel",
        "Philips Hue Bridge smart lighting hub",
        "Kasa Smart Dimmer Switch HS220",
    ],
    "best-high-performance-blenders-for-home-smoothies": [
        "Ninja BN701 Professional Plus blender",
        "Vitamix E310 Explorian blender",
        "NutriBullet ZNBF30500Z blender combo",
    ],
    "best-wireless-earbuds-under-300-for-2025": [
        "Apple AirPods Pro 2 USB-C",
        "Sony WF-1000XM5 earbuds",
        "Bose QuietComfort Ultra earbuds",
    ],
    "best-electric-lawn-mowers-under-300-for-2025": [
        "Greenworks 40V 16 inch cordless lawn mower",
        "Sun Joe MJ401E electric lawn mower",
        "BLACK+DECKER BEMW472BH electric lawn mower",
    ],
    "best-portable-outdoor-grills-under-300-for-2025": [
        "Weber Q1200 portable gas grill",
        "Coleman RoadTrip 285 portable stand-up propane grill",
        "Cuisinart CGG-180T Petit Gourmet portable gas grill",
    ],
    "best-indoor-hydroponic-gardening-systems-under-300": [
        "AeroGarden Harvest Elite indoor garden",
        "LetPot LPH-SE hydroponics growing system",
        "iDOO 12 pods hydroponics growing system",
    ],
    "best-robot-vacuums-for-pet-hair-under-300": [
        "iRobot Roomba 694 robot vacuum",
        "Eufy RoboVac 11S Max robot vacuum",
        "Shark ION Robot AV753 vacuum",
    ],
}


def wp_headers() -> dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "HandyTested product affiliate link updater",
    }


def wp_json(endpoint: str, payload: dict | None = None) -> object:
    data = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2{endpoint}",
        data=data,
        method=method,
        headers=wp_headers(),
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_posts() -> list[dict]:
    posts: list[dict] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({
            "per_page": 100,
            "page": page,
            "status": "publish",
            "context": "edit",
            "_fields": "id,slug,title,content,status",
        })
        try:
            batch = wp_json(f"/posts?{query}")
        except urllib.error.HTTPError as exc:
            if exc.code == 400 and page > 1:
                break
            raise
        if not isinstance(batch, list) or not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def amazon_link(query: str) -> str:
    params = urllib.parse.urlencode({"k": query, "tag": AMAZON_TAG})
    return f"https://{AMAZON_DOMAIN}/s?{params}"


def build_block(products: list[str]) -> str:
    items = []
    for product in products:
        url = amazon_link(product)
        items.append(
            '<li style="margin:8px 0;">'
            f'<a href="{html.escape(url, quote=True)}" '
            'rel="sponsored nofollow noopener" target="_blank">'
            f'{html.escape(product)}</a>'
            "</li>"
        )
    return (
        f"\n{START_MARKER}\n"
        '<div class="handytested-amazon-picks" '
        'style="border:1px solid #e6e8ef;border-left:4px solid #e8440a;'
        'border-radius:8px;padding:18px 20px;margin:28px 0;background:#fff;">'
        '<h2 style="margin-top:0;">Find these models on Amazon</h2>'
        '<p>These links open Amazon.com search results, which may include similar models and sponsored listings. '
        'Confirm the exact model, seller, price, and availability before buying.</p>'
        f'<ul>{"".join(items)}</ul>'
        "</div>\n"
        f"{END_MARKER}\n"
    )


def replace_block(content: str, block: str) -> str:
    pattern = re.compile(
        rf"\s*{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\s*",
        flags=re.DOTALL,
    )
    if pattern.search(content):
        return pattern.sub(block, content).strip()
    return content.rstrip() + "\n" + block


def main() -> int:
    scanned = 0
    updated = 0
    missing: list[str] = []

    for post in iter_posts():
        scanned += 1
        slug = str(post.get("slug") or "")
        products = PRODUCTS_BY_SLUG.get(slug)
        if not products:
            missing.append(slug)
            continue
        raw = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered") or ""
        new_content = replace_block(raw, build_block(products))
        if new_content == raw:
            continue
        title = post.get("title", {}).get("raw") or post.get("title", {}).get("rendered") or slug
        print(f"{'DRY-RUN' if DRY_RUN else 'Updating'} {post['id']} | {slug} | {title}")
        if not DRY_RUN:
            wp_json(f"/posts/{post['id']}", {"content": new_content})
        updated += 1

    print(f"Scanned {scanned} posts; {'would update' if DRY_RUN else 'updated'} {updated}.")
    if missing:
        print("No curated products for:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
