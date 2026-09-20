"""Build an evidence-led Phase 3 progress report from the public snapshot."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).parent
SNAPSHOT = ROOT / "handytested_sources" / "public_snapshot.json"
PHASE2 = ROOT / "HANDYTESTED_PHASE2_REPORT.md"
OUTPUT = ROOT / "HANDYTESTED_PHASE3_REPORT.md"
PAINT = "top-5-home-diy-paint-sprayers-under-300-in-2025"


def main() -> None:
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    records = data["records"]
    assert len(records) == 38
    queue = PHASE2.read_text(encoding="utf-8")
    main_issues = {
        slug: issue
        for slug, issue in re.findall(r"^\| P[012] \| ([a-z0-9-]+) \| ([^|]+) \|", queue, re.M)
    }
    sorted_records = sorted(records, key=lambda r: ({"P0": 0, "P1": 1, "P2": 2}[r["priority"]], list(main_issues).index(r["slug"])))
    rows = []
    for record in sorted_records:
        is_paint = record["slug"] == PAINT
        link = f"[{record['slug']}](https://handytested.com/{record['slug']}/)"
        worksheet = f"[record](handytested_sources/{record['slug']}.md)"
        rows.append("| " + " | ".join([
            link, record["priority"], "Yes, source-reviewed" if is_paint else "Screened; blocked",
            "2 identities; retail unverified" if is_paint else "No",
            "Yes" if is_paint else "No", "Yes; ceiling removed" if is_paint else "No",
            "Title/meta/body" if is_paint else "No", "2 tagged searches" if is_paint else f"{len(record['amazon_links'])} tagged searches",
            "Featured; rights pending" if is_paint else "Inventory only; rights pending",
            "3 live links" if is_paint else "Inventory only", "Yes" if is_paint else "No",
            ("DeWalt heat gun removed; " if is_paint else "BLOCKED - product/claim verification required; ") + main_issues.get(record["slug"], "") + f"; {worksheet}",
        ]) + " |")
    baseline_links = sum(len(record["amazon_links"]) for record in records)
    exact_disclosures = sum(record["disclosure_exact"] for record in records)
    report = f"""# HandyTested Phase 3 Report

Date: 2026-09-20. **Partial delivery.** The 38 posts were individually inventoried into versioned worksheets. Only the paint-sprayer article received manufacturer-level source review and a published correction; the other 37 remain **BLOCKED - REQUIRES MANUAL VERIFICATION**. A screening record is not an editorial approval. No mass title, year, price or rating replacement was performed.

## Baseline and Release

- Baseline: {data['checked']}; 38 published posts, 9 pages. The public snapshot preserves each post's original rendered content and date. WordPress revisions remain available.
- Pre-release: 247 Amazon search links; all observed tags were `handytested0d-20`. None was a verified direct product link. Exact Amazon disclosure was absent from all 38 post bodies at baseline ({exact_disclosures}/38 present).
- Paint-sprayer release: [dry-run](https://github.com/HeberPython/agente-sites/actions/runs/35529644640), [apply and backup](https://github.com/HeberPython/agente-sites/actions/runs/35529668323). Artifact `handytested-phase3-paint-backup`, ID `10610538486`, retention 30 days. Only post ID 87 changed. Original title/content/SEO HTML and release metadata are in the artifact.
- WordPress update and Rank Math metadata both succeeded. Public page has one H1, new title/meta, exact disclosure, self-canonical and two tagged Amazon **search** links. Slug is unchanged. The article's 3 new related links returned HTTP 200.
- No changes to the other 37 posts, Astra theme, Pinterest callback, AdSense or Amazon account. No ASINs were fabricated.

## Technical Status

| Area | Status | Evidence / next action |
|---|---|---|
| Global CSS | BLOCKED | Astra footer builder does not render the prepared `footer-widget-1` / `block-7`; public REST has no custom-css route. In WP admin, add versioned CSS via Appearance > Customize > Additional CSS or an existing child-theme mechanism, then test article/category layouts. |
| Global footer | BLOCKED | Homepage-only footer exists; Astra's global builder needs a rendered footer element. Configure footer builder and remove homepage fallback only after global footer shows exact Amazon statement without duplication. |
| Related Guides | PARTIAL | Three contextual links published in paint guide; no global article template for the remaining 37. |
| Responsive tables | PARTIAL | Paint-guide table has internal scrolling at 320/375 px; other articles not globally restyled. |
| Sitemap | BLOCKED | Recheck after release: 38 published vs 35 sitemap URLs, 5 missing and 2 stale extra URLs. Prior Rank Math transient clear did not fix it. Inspect Rank Math sitemap exclusions/indexability and hosting/object cache in WP admin; resave sitemap settings/permalinks if appropriate, recheck XML and resubmit Search Console. |
| Pinterest | PARTIAL | [Noindex release](https://github.com/HeberPython/agente-sites/actions/runs/35530111606) changed only Rank Math robots to `noindex, follow`; callback page still returned 200 and shortcode was unchanged. Backup artifact ID `10611230994`. Page sitemap still lists the URL and public diagnostics/token prefix remain. Need plugin/admin access to hide diagnostics and resolve sitemap cache, then test a fresh OAuth callback. |
| AdSense | PRESERVED / ISSUE | No ad setting changed. Browser QA saw a large reserved top area, ad units interleaved with body text, injected link-like labels and a floating unit near the comparison table. Review Auto ads placements in AdSense before changing. |
| Amazon tag | PRESERVED | 247 baseline searches tagged correctly; paint guide now has 2 (down from 7). A fresh 38-post public audit confirmed {baseline_links - 5} tagged search links. |

Sitemap missing URLs:
1. `https://handytested.com/best-electric-lawn-mowers-under-300-for-2025/`
2. `https://handytested.com/best-indoor-hydroponic-gardening-systems-under-300/`
3. `https://handytested.com/best-portable-outdoor-grills-under-300-for-2025/`
4. `https://handytested.com/best-robot-vacuums-for-pet-hair-under-300/`
5. `https://handytested.com/best-wireless-earbuds-under-300-for-2025/`

Stale sitemap URLs:
1. `https://handytested.com/discover-the-best-amazon-deals-this-summer-2026-08-05/`
2. `https://handytested.com/top-father-s-day-gifts-for-2026-great-deals-and-ideas-2026-07-31/`

## Article Status

`Reviewed` below distinguishes a source-reviewed and published article from an automated screen. `No` means no safe change was made. Every row links to a separate worksheet with title, date, H1, meta, canonical, model candidates, flagged passages, images, links and outstanding verification.

| Article | Priority | Reviewed | Products Verified | Claims Fixed | Price Fixed | SEO Updated | Amazon Links | Images | Internal Links | Published | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Product Evidence

| Product | Article | Model Verified | Manufacturer Source | Amazon Direct Link | Status | Action |
|---|---|---|---|---|---|---|
| Wagner FLEXiO 590 | Paint sprayers | Yes, model/type/features | [Wagner owner manual](https://www.wagnerspraytech.com/wp-content/uploads/2023/10/0529595B_eng.pdf) | No | UNCERTAIN current retail availability | Retained with clearly labeled tagged search; verify exact listing before direct-link replacement |
| Graco TrueCoat 360 Dual Speed 26D281 | Paint sprayers | Yes, model/type/features | [Graco product page](https://www.graco.com/us/en/homeowner/product/26d281.html) | No | ACTIVE on manufacturer site; retail availability unverified | Retained with tagged search; reader instructed to check exact part number |
| DeWalt DCE530B | Paint sprayers | Yes: **heat gun**, not sprayer | [DeWalt product page](https://www.dewalt.com/en-us/product/dce530b/20v-max-cordless-heat-gun-tool-only) | No | WRONG PRODUCT | Removed recommendation, table row and Amazon CTA |
| RYOBI P650 | Paint sprayers | P650 is a sprayer, not the described airbrush | [RYOBI support](https://espanol.ryobitools.com/help-plus/details/33287150656) | No | WRONG DESCRIPTION / exact current retail variant uncertain | Removed until variant and claims verified |

The other product names in `handytested_sources/` are **candidates extracted from Amazon search queries, not verified products**. Manufacturer research and listing checks for all other recommendations are still required. Direct Amazon links: **0 verified**.

## Content and SEO Findings

- Paint guide: removed four unverified price ranges, star ratings, fabricated hands-on narrative, specific unsupported specs and the incorrect DeWalt recommendation. Replaced “Top 5 / under $300 / 2025” title with an evergreen two-model comparison; unchanged old slug retains URL equity. Manufacturer links and article-specific methodology are visible. WordPress modified date changed because substantive content changed.
- All other articles: no claims, prices, ratings, title years, metadata, images or Amazon links were altered. Their worksheet flags are review prompts, not proven errors. A narrower first-hand regex flags {sum(bool(r['claim_passages_requiring_verification']) for r in records)}/38; the earlier broader screen flagged 33/38. This difference is a detection-limit warning, not evidence that the other posts are clear.
- Baseline flags: {sum(bool(r['price_values_detected']) for r in records)}/38 contain dollar values; {sum(bool(r['rating_values_detected']) for r in records)}/38 contain rating markers by this screen; {sum(r['title_has_year'] for r in records)}/38 titles contain a year. The current paint-guide FAQ mentions the old price ceiling only to state it is **not guaranteed**.
- Cannibalization candidates: `best-wireless-earbuds-under-100-for-2025` vs `best-wireless-earbuds-under-300-for-2025` (KEEP SEPARATE only if distinct budget/lineup research supports it); `best-smart-home-hubs-under-150-for-2025` vs the two broad smart-home device posts (REPOSITION candidates). No merge or canonical change was made.
- Images: the 38 featured-media IDs/URLs/alt texts and body image elements are inventoried. Image rights, exact product match, file weight and visual suitability are not proven. No product image was replaced with an unlicensed or mismatched image.
- Schema: JSON-LD was detected on public pages but Product/Review eligibility and field accuracy were not fully audited. No new ratings, prices or availability schema were added.
- Editorial validator `handytested_editorial_validator.py` flags testing language, dollar values, ratings, title years, disclosure, source record, product evidence, Amazon searches/tags, body H1 and Product/Review JSON-LD. It is a gate for explicit first-hand claims and missing evidence, not an autonomous truth detector. `handytested_release_gate.py` is now called by the scheduled/manual HandyTested generators and the Amazon promo agent when `publish` is explicitly requested. It requires a versioned source record with primary URL, matching named products and deliberate approval; drafts and other sites are unaffected.

## Verification

- Python compilation of new scripts: passed. `python -m unittest test_handytested_release_gate.py test_handytested_editorial_validator.py test_handytested_phase2.py`: 10 passed. `git diff --check`: passed before release.
- GitHub Actions dry-run and apply: passed, with public H1/canonical/title/meta/disclosure/tag checks. Applied backup artifact retained 30 days.
- Browser QA on updated article: 320, 375, 768, 1280 and 1920 px. One H1 and document scroll width no greater than viewport at each width. At 320/375 px table width 560 px is contained in an internally scrollable 260/315 px wrapper. Visual inspection at 375 and 1920 confirmed article content; AdSense placement remains a separate issue.
- Three Related Guides destinations returned HTTP 200. Public sitemap gap is unchanged after publication. Pinterest page declares `noindex, follow` but remains in the stale page sitemap. No current Search Console ranking or conversion claim is made.

## Next Controlled Batches

1. In WP/Astra admin, finish global CSS/footer and fix Rank Math sitemap. Preserve OAuth while restricting Pinterest diagnostics; noindex alone does not make the token prefix private. In AdSense, assess the observed overlay and body injections.
2. Research P0 heat guns, multimeters, smart-home hubs, earbuds, drill presses, sanders and voltage testers model by model against current manufacturer manuals. For electrical safety articles, require exact CAT/voltage claims before publication. Keep each article blocked until its own source record and backup pass validation.
3. Then process P1 (23) and P2 (7) as separate backed-up batches. Each publish must verify title/meta/H1/canonical, exact disclosure, links, responsive table, image rights and sitemap entry. No block should be cleared merely by automated flag removal.
4. Obtain direct Amazon product links through a verified listing/SiteStripe path, preserving `handytested0d-20`; do not infer ASINs from search results. Replace the existing search URLs only one verified model at a time.
"""
    OUTPUT.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT}: {len(rows)} article rows, {len(report)} characters")


if __name__ == "__main__":
    main()
