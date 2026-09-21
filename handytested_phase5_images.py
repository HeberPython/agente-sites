"""Read-only featured-media metadata audit and visual contact sheets."""

from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw

from handytested_phase5_crawl import BASE, api, get


def main() -> None:
    posts = api("posts?per_page=100&_fields=id,slug,link,featured_media")
    if len(posts) != 38:
        raise RuntimeError(f"Expected 38 posts, got {len(posts)}")
    rows = []
    thumbs = []
    for post in posts:
        media_id = post["featured_media"]
        if not media_id:
            raise RuntimeError(f"No featured media for {post['slug']}")
        media = api_media(media_id)
        details = media.get("media_details", {})
        sizes = details.get("sizes", {})
        thumb_url = (sizes.get("medium") or sizes.get("medium_large") or {}).get("source_url") or media["source_url"]
        status, _, _, data = get(thumb_url)
        if status != 200:
            raise RuntimeError(f"Image {media_id} returned HTTP {status}")
        picture = Image.open(BytesIO(data)).convert("RGB")
        thumbs.append((post["slug"], picture))
        rows.append({
            "article": post["link"], "media_id": media_id, "url": media["source_url"],
            "alt": media.get("alt_text", ""), "caption": media.get("caption", {}).get("rendered", ""),
            "description": media.get("description", {}).get("rendered", ""),
            "width": details.get("width"), "height": details.get("height"),
            "media_type": media.get("mime_type"), "thumbnail_bytes": len(data),
            "license_documented": False,
        })
    temp = Path(os.environ.get("TEMP", "/tmp"))
    for offset in range(0, len(thumbs), 20):
        subset = thumbs[offset:offset + 20]
        sheet = Image.new("RGB", (1200, 210 * 4), "white")
        draw = ImageDraw.Draw(sheet)
        for index, (slug, picture) in enumerate(subset):
            x = (index % 5) * 240
            y = (index // 5) * 210
            picture.thumbnail((224, 160))
            sheet.paste(picture, (x + 8, y + 4))
            draw.text((x + 8, y + 170), f"{offset + index + 1}. {slug[:29]}", fill="black")
        sheet.save(temp / f"handytested-phase5-images-{offset // 20 + 1}.jpg", quality=85)
    output = Path("HANDYTESTED_PHASE5_IMAGES.md")
    if output.exists():
        raise RuntimeError("Refusing to overwrite image audit")
    lines = [
        "# HandyTested Phase 5 featured-image inventory",
        "",
        "38 images inventoried from public WordPress media. Licensing remains uncertain unless a source/license record is produced; a filename or WordPress upload is not proof of rights. Visual classifications are recorded separately after contact-sheet review.",
        "",
        "| Article | Media ID | Image | Dimensions | MIME | Alt text | Source/license evidence | Classification |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for row in rows:
        cell = lambda value: str(value).replace("|", "\\|")
        lines.append("| " + " | ".join(cell(value) for value in (
            row["article"], row["media_id"], row["url"],
            f"{row['width']}x{row['height']}", row["media_type"], row["alt"],
            "not documented", "LICENSING UNCERTAIN"
        )) + " |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    output.with_suffix(".json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"images": len(rows), "empty_alt": sum(not row["alt"] for row in rows), "missing_license_evidence": len(rows)}))
    print("Contact sheets:", temp / "handytested-phase5-images-1.jpg", temp / "handytested-phase5-images-2.jpg")


def api_media(media_id: int) -> dict:
    status, _, _, body = get(f"{BASE}/wp-json/wp/v2/media/{media_id}?_fields=id,source_url,alt_text,caption,description,media_details,mime_type")
    if status != 200:
        raise RuntimeError(f"Media {media_id}: HTTP {status}")
    return json.loads(body)


if __name__ == "__main__":
    main()
