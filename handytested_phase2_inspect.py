"""Read-only inventory of authenticated WordPress design surfaces."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request


BASE = "https://handytested.com/wp-json"
TOKEN = base64.b64encode(
    f"hebergravano@gmail.com:{os.environ['HT_WP_PASS']}".encode()
).decode()


def get(path: str) -> object:
    request = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Basic {TOKEN}", "User-Agent": "HandyTested phase 2 inspection"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> None:
    checks = {
        "menus": "/wp/v2/menus?per_page=100&context=edit",
        "menu_locations": "/wp/v2/menu-locations",
        "sidebars": "/wp/v2/sidebars?context=edit",
        "widgets": "/wp/v2/widgets?context=edit",
        "home": "/wp/v2/pages?slug=home-page&context=edit&_fields=id,slug,status,content,meta",
        "pinterest": "/wp/v2/pages?slug=pinterest-connect&context=edit&_fields=id,slug,status,content,meta",
        "settings": "/wp/v2/settings",
        "block": "/wp/v2/block-types/core/latest-posts",
        "astra": "/astra/v1/admin/settings",
    }
    for name, path in checks.items():
        try:
            data = get(path)
            if name in {"home", "pinterest"} and isinstance(data, list):
                data = [{
                    "id": page.get("id"),
                    "status": page.get("status"),
                    "content_length": len(page.get("content", {}).get("raw", "")),
                    "meta_keys": list(page.get("meta", {})),
                } for page in data]
            elif name == "settings" and isinstance(data, dict):
                data = {key: data.get(key) for key in ("show_on_front", "page_on_front", "page_for_posts", "stylesheet", "template")}
            elif name == "astra" and isinstance(data, dict):
                data = {"keys": list(data)[:60]}
            elif name == "block" and isinstance(data, dict):
                data = {"attributes": data.get("attributes", {})}
            print(name, json.dumps(data, ensure_ascii=False)[:9000])
        except urllib.error.HTTPError as exc:
            print(name, "HTTP", exc.code, exc.read().decode()[:300])

    try:
        menus = get(checks["menus"])
        if isinstance(menus, list):
            for menu in menus:
                menu_id = menu["id"]
                items = get(f"/wp/v2/menu-items?menus={menu_id}&per_page=100&context=edit")
                print("menu_items", menu_id, json.dumps(items, ensure_ascii=False)[:12000])
    except urllib.error.HTTPError as exc:
        print("menu_items HTTP", exc.code, exc.read().decode()[:300])


if __name__ == "__main__":
    main()
