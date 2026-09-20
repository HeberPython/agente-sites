# HandyTested Phase 2 Report

Date: 2026-09-20. Baseline: `HANDYTESTED_AUDIT.md`, `HANDYTESTED_IMPROVEMENT_PLAN.md`, `HANDYTESTED_CHANGELOG.md`. This is a partial Phase 2 release, not a claim that every acceptance criterion is complete.

## Executive Summary

The public homepage and desktop/mobile navigation were redesigned and published. Six recent guides now come from WordPress's server-rendered Latest Posts block on every page request. The homepage includes a visible Amazon disclosure and clear paths to guide/category content without fabricated prices or testing claims. The Astra footer widget registered through REST is not rendered by the active footer builder, so site-wide footer and article/category CSS remain incomplete. The Rank Math sitemap mismatch also remains unresolved after a transient flush.

## Architecture Used

WordPress/Astra/Rank Math remain in place. `handytested_phase2.py` uses the existing WordPress REST application credential inside GitHub Actions, with dry-run, object backup and an isolated homepage refresh. `handytested_phase2.css` is the source for the homepage's inline styles and a prepared footer widget. No theme PHP, headless stack, new JS framework, or new product database was added. The native `core/latest-posts` block is dynamic at render time; curated Top Picks are intentionally static editorial selections.

## Files Changed

- `handytested_phase2.py`: homepage renderer, menu/WordPress release, backup, isolated refresh.
- `handytested_phase2.css`: responsive design tokens and homepage components; prepared global selectors are not active site-wide.
- `handytested_phase2_inspect.py`: authenticated, read-only capability inspection.
- `.github/workflows/handytested-phase2.yml`: inspect/dry-run/apply/refresh-home workflow.
- `setup_handytested_portal.py`: future portal runs call the new homepage renderer instead of generating the old post snapshot.
- `test_handytested_phase2.py`: focused offline renderer tests.
- `handytested_sitemap_refresh.py` and `.github/workflows/handytested-sitemap-refresh.yml`: reproduce sitemap mismatch and clear Rank Math transients when explicitly requested.
- `HANDYTESTED_CHANGELOG.md` and this report: release record.

## Homepage Changes

Compact photographic hero using the existing cordless-drill article image, exact requested headline/supporting text, two CTAs, research-led trust strip, three curated Top Picks guides, populated category grid, six dynamic Latest Guides, value/deals guidance, methodology and a functional WordPress search form. No empty category is featured and no fake deal price, discount, newsletter, rating, counter or testimonial was added. Latest Posts currently has no category label in each card because the native block does not expose one; that is a remaining component gap.

## Design System

System font stack, graphite body, restrained amber marker, blue action links/buttons, white/light neutral surfaces, 6px cards, responsive grids, fixed image ratios, visible keyboard focus and 44-46px action height. CSS is centralized in one repository file. The live site only receives it through homepage content because Astra's active footer builder does not output `footer-widget-1` even though REST reports that sidebar as active.

## Navigation

Primary menu: Home, Best Picks, Tools, DIY, Electronics, Learn, Deals, Search. Best Picks/Search anchor to real homepage sections; Learn points to existing methodology; Deals points to the real guidance page. The same menu is assigned to `mobile_menu`, replacing Astra's public page-list fallback. Pinterest Connect Demo is absent from visible mobile navigation. Search submits to the native WordPress `?s=` endpoint. On mobile the Search link lives in the menu, not as a separate header icon.

## Categories

The homepage links only to seven categories with published content. The original WordPress archive templates/descriptions and archive H1s remain. Full category landing redesign was not safely possible from the exposed REST surfaces because Astra theme/global CSS configuration is not exposed; the prepared CSS has not become global.

## Article UX

No existing article body, title, price, rating, ASIN, or URL was rewritten. A sample article retained one H1 and no horizontal page overflow at tested widths. Existing disclosure language in that sample is not the exact Amazon-required sentence and contains a hands-on implication; its paragraph requires editorial review. Site-wide comparison-table CSS and Related Guides are prepared as selectors but **not deployed** to article templates. No false claim of completion is made.

## Mobile Improvements

Homepage card/category grids collapse to two then one column; hero text and CTAs wrap; footer links collapse; desktop menu switches to Astra's mobile toggle. Fresh page loads at 320, 375, 768, 1280 and 1920 px yielded document scroll width no greater than viewport width on homepage, sample article and Tools category (15 checks). Mobile menu was opened and visually checked. An AdSense auto-ad occupies substantial top-of-page space; it was not moved without account policy/revenue review.

## SEO Changes

The homepage still has one H1, canonical, meta description, Open Graph and JSON-LD in public HTML. Rank Math remains active. No Product/Review ratings/prices or unsupported schema were added. The new menu removes the technical Pinterest page from ordinary navigation but does not change its indexability. Existing article metadata and canonicals were not modified.

## Sitemap Result

Public REST lists 38 published posts. `post-sitemap.xml` has 35 URLs: five published/indexable posts missing and two older, unpublished promotion URLs extra. All five missing pages publicly declare `index, follow` and self-canonical. The authenticated Rank Math `clear_transients` action removed one transient in [run 35527294565](https://github.com/HeberPython/agente-sites/actions/runs/35527294565), but the sitemap remained 35/5/2 immediately afterward. Public response advertises `Cache-Control: no-cache, no-store` and `x-hcdn-cache-status: DYNAMIC`; the underlying cause may be a Rank Math/file/server cache or indexing state not exposed by REST. Requires WordPress admin/hosting inspection, then validation and Search Console resubmission. No URL was forced into the sitemap.

## Pinterest Connect Result

The page remains at `/pinterest-connect/` because it is the configured OAuth redirect and its public content is shortcode-driven. The new mobile menu removes it from ordinary navigation. No `noindex`, sitemap exclusion, shortcode removal, or token-display change was applied without a backup of the plugin/callback implementation and a safe OAuth regression path. Public diagnostics remain an open privacy/SEO task.

## Performance

No new frontend JavaScript, fonts, sliders or video were added. The hero reuses a 1024px WordPress image; cards use WordPress intermediate sizes and declared dimensions. Browser screenshot inspection confirmed populated cards and images. LCP, CLS, INP, Lighthouse and revenue impact: **Not measured**. Large top ad spacing and an automatic ad overlay were visually observed; AdSense configuration should be reviewed before any change.

## Accessibility

Homepage sections use headings, a search label, semantic cards and visible focus rules; image links with adjacent titles use empty decorative alt text. The tested homepage, article and category each had one H1. Keyboard traversal and screen-reader audits: **Not measured**. The auto-ad content is outside our control.

## AdSense Preservation

The existing publisher script/account was not removed or changed. Two ad slots appeared in the browser on tested pages. A third-party automatic overlay obscured part of Latest Guides during desktop QA; investigate in AdSense before adjusting placement, formats or disabling ads.

## Amazon Affiliate Preservation

No existing Amazon destination or tag `handytested0d-20` changed. The homepage footer displays the exact text: "As an Amazon Associate I earn from qualifying purchases." The footer is not global yet; article disclosures need targeted review. Product-specific links still largely lead to Amazon search results and require verified ASIN/SiteStripe work in Phase 3.

## Tests Performed

- `python -m unittest test_handytested_phase2.py`: 2 passed.
- `python -m py_compile` on changed Python files: passed.
- `git diff --check`: passed.
- GitHub Actions dry-run [35526683014](https://github.com/HeberPython/agente-sites/actions/runs/35526683014) and [35526907464](https://github.com/HeberPython/agente-sites/actions/runs/35526907464): passed.
- Live release [35526924808](https://github.com/HeberPython/agente-sites/actions/runs/35526924808) and homepage refresh [35527192479](https://github.com/HeberPython/agente-sites/actions/runs/35527192479): passed; each saved `handytested-phase2-backup` for 30 days. Two earlier apply attempts failed before any backup/write due a transient 403 and timeout; read-only retries were added before successful release.
- Browser QA of home, sample article and Tools category at 320/375/768/1280/1920 px: 15 fresh-load checks, no document-level horizontal overflow, one H1 each. Mobile menu and homepage footer visually inspected. No broad visual regression test suite exists.

## Public URLs Verified

`https://handytested.com/`, `/category/tools/`, `/best-cordless-drills-under-100/`, `/how-we-review/`, `/deals/`, `/pinterest-connect/`, `/post-sitemap.xml`. Native search endpoint was confirmed from the homepage form; a full search-results UX audit remains open.

## Remaining Issues

Site-wide Astra footer/global stylesheet, article template and responsive comparison tables, Related Guides, full category landing redesign, Pinterest noindex/diagnostics, and sitemap correction remain. Latest cards lack category labels. Several existing featured images are generic or mismatched to article products. Existing prices/ratings/testing wording remain unverified. AdSense's mobile top spacing and overlay need review. These are not described as finished work.

## Manual Action Required

1. In WordPress/Astra, expose a footer builder widget area or add the versioned CSS through Additional CSS/child theme, then remove the homepage-only footer fallback to avoid duplication. Verify article/category/table styles and exact disclosure globally before marking Phase 2 complete. The prepared widget is `block-7` in `footer-widget-1`, currently not rendered.
2. Inspect Rank Math Sitemap Settings and any physical/server cache. Flush sitemap cache using the plugin's documented settings flow; verify 38 expected indexable posts and removal of two unpublished promotions, then resubmit in Search Console.
3. Inspect Pinterest OAuth plugin/shortcode, hide diagnostics/token prefix and apply noindex/sitemap exclusion without breaking the callback.
4. Review AdSense auto-ad formats/placements and policy center; the observed overlay overlaps editorial cards. Measure Core Web Vitals and ad revenue before placement changes.
5. Review article disclosures and claims. Preserve WordPress revisions and verify product/ASIN evidence before replacing the existing tagged Amazon searches.

## Recommended Phase 3

Complete the template-level Astra integration first, then run the paragraph-level editorial and product review queue below. Prioritize unsupported first-hand claims, model identity, current product availability and direct Amazon links. Do not merely replace years, prices or ratings globally.

| Priority | Article | Main Issue | Product Verification Needed | Price Review | Testing Claims | Amazon Direct Link Needed | Year Update | Recommended Action |
|---|---|---|---|---|---|---|---|---|
| P0 | best-heat-guns-for-diy-projects-under-80-in-2025 | Specific test and heat/safety claims | Yes | Yes | Yes | Yes | Yes | Verify measurements and safety wording first |
| P0 | best-multimeters-under-50-for-home-electricians-2025 | Electrical safety and test claims | Yes | Yes | Yes | Yes | Yes | Recheck specifications and safety guidance |
| P0 | best-smart-home-hubs-under-150-for-2025 | First-hand claims and compatibility | Yes | Yes | Yes | Yes | Yes | Verify ecosystems and documented use |
| P0 | best-wireless-earbuds-under-100-for-2025 | First-hand audio/battery claims | Yes | Yes | Yes | Yes | Yes | Remove unsupported observations |
| P0 | top-5-home-diy-paint-sprayers-under-300-in-2025 | Possible incorrect product identity | Yes | Yes | Yes | Yes | Yes | Verify each model before recommendation |
| P0 | best-home-drill-presses-under-300-for-diy-enthusiasts | Specific testing/performance assertions | Yes | Yes | Yes | Yes | No | Audit measurements and model status |
| P0 | best-random-orbital-sanders-for-diy-projects-2025 | First-hand finishing claims | Yes | Yes | Yes | Yes | Yes | Verify evidence and rewrite unsupported results |
| P0 | best-voltage-testers-for-home-electrical-work-2025 | Electrical safety/test wording | Yes | Yes | Yes | Yes | Yes | Verify safety ratings and claims |
| P1 | best-robot-vacuums-for-pet-hair-under-300 | Test wording, price and image fit | Yes | Yes | Yes | Yes | No | Review specifications and photo relevance |
| P1 | best-indoor-hydroponic-gardening-systems-under-300 | Test wording, price and image fit | Yes | Yes | Yes | Yes | No | Check products and featured image |
| P1 | best-portable-outdoor-grills-under-300-for-2025 | Test wording, year and image mismatch | Yes | Yes | Yes | Yes | Yes | Correct media after product verification |
| P1 | best-electric-lawn-mowers-under-300-for-2025 | Test wording and seasonal models | Yes | Yes | Yes | Yes | Yes | Verify lineup and price ceiling |
| P1 | best-wireless-earbuds-under-300-for-2025 | Test wording and dated lineup | Yes | Yes | Yes | Yes | Yes | Recheck models and evidence |
| P1 | best-high-performance-blenders-for-home-smoothies | Test wording | Yes | No | Yes | Yes | No | Review performance claims and images |
| P1 | top-smart-home-automation-devices-under-300-for-2025 | Test wording and compatibility | Yes | Yes | Yes | Yes | Yes | Verify products and ecosystem support |
| P1 | best-kitchen-gadgets-under-300-for-modern-chefs | Test wording and price | Yes | Yes | Yes | Yes | No | Recheck model relevance |
| P1 | best-smart-home-devices-under-300-for-2025 | Test wording and dated recommendations | Yes | Yes | Yes | Yes | Yes | Review compatibility and year |
| P1 | best-diy-outdoor-furniture-kits-under-300-for-2025 | Test wording and dated kits | Yes | Yes | Yes | Yes | Yes | Verify products and assembly claims |
| P1 | best-cordless-impact-wrenches-under-300-for-2025 | Test wording and performance | Yes | Yes | Yes | Yes | Yes | Confirm torque specs and products |
| P1 | best-projectors-under-300-for-home-entertainment | Test wording and brightness | Yes | Yes | Yes | Yes | No | Verify measured vs advertised specs |
| P1 | top-5-ergonomic-office-chairs-under-300-for-comfort | Test wording and comfort claims | Yes | Yes | Yes | Yes | No | Check product fit and evidence |
| P1 | best-carpet-cleaners-for-pet-owners-in-2025 | Test wording and year | Yes | Yes | Yes | Yes | Yes | Verify stain-cleaning claims |
| P1 | best-cordless-nail-guns-under-300-for-diy-projects | Safety and test wording | Yes | Yes | Yes | Yes | No | Check specifications and safety copy |
| P1 | best-camping-gear-under-300-for-outdoor-adventures | Test wording and mixed products | Yes | Yes | Yes | Yes | No | Verify each item and category fit |
| P1 | best-kitchen-appliances-under-300-for-home-chefs | Test wording and price | Yes | Yes | Yes | Yes | No | Verify model lineup and source dates |
| P1 | best-smart-home-security-cameras-under-300-for-2025 | Security/privacy and test wording | Yes | Yes | Yes | Yes | Yes | Check privacy and compatibility facts |
| P1 | best-home-diy-tool-sets-for-under-300-in-2025 | Test wording and old year | Yes | Yes | Yes | Yes | Yes | Review product bundle identities |
| P1 | best-smart-tvs-under-300-for-2025-viewing-experience | Test wording and fast-changing lineup | Yes | Yes | Yes | Yes | Yes | Recheck exact TV variants |
| P1 | best-noise-canceling-headphones-under-300-for-2025 | Audio test wording and year | Yes | Yes | Yes | Yes | Yes | Verify feature and battery claims |
| P1 | best-laser-levels-for-diy-home-projects-under-60 | Test wording and accuracy | Yes | Yes | Yes | Yes | No | Verify accuracy specs |
| P1 | best-oscillating-multi-tools-under-75-for-2025 | Test wording and year | Yes | Yes | Yes | Yes | Yes | Recheck blades and compatibility |
| P2 | best-cordless-ratchets-for-diy-mechanics-in-2025 | Price/year; fewer detected test phrases | Yes | Yes | No | Yes | Yes | Verify model list and titles |
| P2 | best-electric-screwdrivers-for-diy-projects-in-2025 | Price/year; fewer detected test phrases | Yes | Yes | No | Yes | Yes | Check exact product variants |
| P2 | top-5-digital-torque-wrenches-under-100-for-accurate-torque | Price and accuracy claims | Yes | Yes | No | Yes | No | Confirm torque range/accuracy |
| P2 | best-cordless-circular-saws-under-150-for-diy-projects | Price and safety | Yes | Yes | No | Yes | No | Verify blade and battery variants |
| P2 | best-rotary-tools-under-50-for-diy-projects-2025 | Test wording, price and year | Yes | Yes | Yes | Yes | Yes | Review claims before retitling |
| P2 | best-stud-finders-under-50-for-home-projects-2025 | Test wording, price and year | Yes | Yes | Yes | Yes | Yes | Verify detection claims |
| P2 | best-cordless-drills-under-100 | Price/ratings and disclosure wording | Yes | Yes | No | Yes | No | Verify ratings, models and disclosure |

The flags are screening indicators from the Phase 1 public audit, not proof that each claim is wrong. The individual editorial pass must verify source records paragraph by paragraph.
