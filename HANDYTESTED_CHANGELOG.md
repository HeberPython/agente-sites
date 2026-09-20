# HandyTested changelog

## 2026-09-19: audit and first editorial safeguards

### Before

- Automated HandyTested reviews published directly; the scheduled promo workflow could publish without editorial review.
- Generated copy in several scripts encouraged or allowed hands-on language, ratings and price claims with no supporting records.
- Portal page content included an H1 in addition to Astra's page title.
- No repeatable public inventory existed. The live site has 38 posts, with 33 testing-language matches, 24 titles containing 2025, 34 bodies containing dollar amounts, and 247 tagged Amazon search links.

### After in repository

- `pub_ht_pro.py` and `pub_ht_once.py`: default new posts to draft, reject a set of explicit first-hand testing phrases, revise prompts/disclosures and remove requested invented ratings.
- `agente_sites.py`: HandyTested-specific draft default and research-led review prompt; other sites keep their existing publication status.
- `.github/workflows/handytested-amazon-promos.yml`: scheduled promotional posts default to draft; an explicit manual dispatch can still select publish.
- `setup_handytested_portal.py`: research methodology/disclosure source copy clarified and redundant page H1s removed from source.
- `setup_handytested.py`: legacy setup copy no longer asserts undocumented credentials or hands-on testing.
- `update_ht_product_links.py`: managed block copy identifies its destination as Amazon search results and asks readers to confirm the exact model.
- `handytested_public_audit.py`: read-only inventory of all public posts, pages, categories and content risk flags.
- `handytested_trust_page_patch.py` and `.github/workflows/handytested-trust-pages.yml`: narrow dry-run/apply path for five existing trust pages, with backup artifact on apply.
- `HANDYTESTED_AUDIT.md` and `HANDYTESTED_IMPROVEMENT_PLAN.md`: baseline and phased release gates.

### Manual action required

- The code/workflow and five trust-page corrections are deployed. Review backup artifacts before any further page rewrite; they are retained for 30 days.
- Review unsupported claims and commercial figures in the 38 existing posts. Verify each Amazon product and exact SiteStripe/ASIN link before replacing search URLs.
- Inspect Rank Math sitemap cache/indexability: public REST lists 38 published posts but post sitemap listed 35, omitting the latest post.
- Check Pinterest OAuth callback usage before removing the demo page from navigation/sitemap or adding `noindex`.
- Check Search Console, analytics, AdSense, media licensing and Core Web Vitals in the respective admin tools.

### Open issues

No mass edit of existing article claims, prices, titles or links was performed. No homepage redesign was made in this slice. These require editorial verification, browser QA and a controlled release. The full ordered work is in `HANDYTESTED_IMPROVEMENT_PLAN.md`.

### Live trust-page release

The first release updated `about`, `deals`, `how-we-review`, `editorial-policy` and `affiliate-disclosure` using the narrow workflow. Original content is stored in workflow run `35473146922` as `handytested-trust-pages-backup`. A nested H1 in `deals` required a follow-up. Run `35473274600` failed before any write because the runner network was unreachable; run `35473361461` then corrected `deals` and saved its previous content as another backup artifact. All five pages were verified with one H1 in public HTML; the methodology copy and exact Amazon Associate statement were also verified.

## 2026-09-20: Phase 2 homepage and navigation release

- Added a WordPress-native `core/latest-posts` block to the homepage. Its six guides are rendered on each request, so new posts do not depend on the old snapshot in `setup_handytested_portal.py`.
- Released a compact photo-backed hero, research-led trust strip, curated guide cards, populated category links, value guidance, methodology/search, and an editorial homepage footer with the exact Amazon Associate statement. No product prices, ratings, ASINs, or existing affiliate destinations were changed.
- Updated the existing primary menu and assigned it to the mobile menu location. The public page-list fallback, including Pinterest Connect Demo, no longer appears in mobile navigation. The OAuth callback page itself remains untouched.
- Added a centralized CSS source and a footer widget, but the current Astra footer builder does not render that registered widget area. Consequently the global article/category/footer styles are **not live**; the homepage includes its own style and footer. This is an open admin/configuration item, not a completed site-wide redesign.
- WordPress backups are in GitHub Actions run `35526924808` (`handytested-phase2-backup`) and homepage refresh run `35527192479` (same artifact name), retained for 30 days. WordPress revisions also remain available.
- Rechecked Rank Math sitemap: 38 published posts, 35 sitemap URLs, five published URLs missing and two unpublished promotion URLs still listed. Rank Math `clear_transients` returned success in run `35527294565` but did not change the sitemap. Do not treat this as resolved.
- Mobile browser QA at 320, 375, 768, 1280 and 1920 px found one H1 and no horizontal page overflow on home, a sample article and Tools category. An AdSense auto-ad overlay and large reserved ad space were observed; no ad settings were changed without account-level review.
- Full evidence, remaining scope, and the 38-article editorial queue are in `HANDYTESTED_PHASE2_REPORT.md`.

## 2026-09-20: Phase 3 inventory and first sourced article correction

- Created `handytested_sources/` with a public pre-release snapshot and 38 distinct article screening worksheets. These are risk inventories, not completed factual reviews. The 37 untouched posts remain blocked pending manufacturer/product and claim verification.
- Added `handytested_editorial_validator.py` and focused tests to flag first-hand language, prices, ratings, dated titles, disclosure, source records, product evidence, Amazon links/tags, body H1 and unsupported Product/Review schema. Existing generators remain draft-first.
- Confirmed against DeWalt's official product page that DCE530B is a heat gun, not the paint sprayer recommended in the published guide. Manufacturer material also supports the identity/features of Wagner FLEXiO 590 and Graco TrueCoat 360 Dual Speed 26D281; RYOBI P650's airbrush description was not supported.
- Rewrote only the paint-sprayer guide, replacing the old Top 5/under-$300/2025 title and unsupported tests, fixed prices and star ratings with a documented two-model comparison, safety context, explicit affiliate disclosure and three relevant internal links. Its original slug/canonical and Amazon tag remain. Search destinations are still temporary, not verified direct product links.
- Dry-run: [35529644640](https://github.com/HeberPython/agente-sites/actions/runs/35529644640). Published release and original-post backup: [35529668323](https://github.com/HeberPython/agente-sites/actions/runs/35529668323), artifact ID `10610538486`, retained 30 days. WordPress/Rank Math and public HTML checks passed. Mobile/desktop layout checks at 320/375/768/1280/1920 px passed for this article, with the table scrolling internally on narrow screens.
- The sitemap still has 35 URLs for 38 public posts (5 absent, 2 stale). Global Astra CSS/footer, Pinterest diagnostics and AdSense Auto ads remain open; no unverified theme or account settings were changed. Exact statuses and the 38-row queue are in `HANDYTESTED_PHASE3_REPORT.md`.
- A fresh public crawl confirmed 242 tagged Amazon search links after the paint-guide reduction from seven to two. No direct Amazon product URL was introduced without a verified listing.
- Added a deliberate publication gate to `pub_ht_pro.py`, `pub_ht_once.py`, the HandyTested branch of `agente_sites.py`, and `handytested_amazon_promo_agent.py`. Draft creation is unchanged; explicit publish now requires a versioned primary-source record, named matching products and editorial approval. Ten focused/unit tests pass.
- Applied `noindex, follow` to the Pinterest callback page using Rank Math without modifying its shortcode or URL. [Dry-run 35530079199](https://github.com/HeberPython/agente-sites/actions/runs/35530079199) and [apply 35530111606](https://github.com/HeberPython/agente-sites/actions/runs/35530111606) passed; backup artifact ID `10611230994`. The page remains in the stale page sitemap, and public diagnostics/token prefix still require plugin/admin work.
## 2026-09-20: Phase 4 editorial releases (interim)

- Researched, rewrote and published all seven remaining P0 guides: heat guns, multimeters, smart home hubs, earbuds under $100, drill presses, random orbital sanders and non-contact voltage testers. Each has a source record, exact Amazon Associate disclosure, revision-guarded dry-run/apply workflow, original-post backup, focused tests and public metadata/content checks.
- Continued directly into P1 and published the pet-hair robot-vacuum guide, replacing its dated lineup and removing a non-durable under-$300 title promise. Eight of the 37 Phase 4 articles are complete; 29 remain pending, not actually blocked.
- Removed invented hands-on results, unsupported ratings/fixed article prices and mismatched model descriptions. Retained only exact-model tagged Amazon search links while direct product listings remain unverified.
- A transient related-guide timeout caused the first sander apply to fail and roll back. After a successful restoration dry-run, the corrected workflow published it; release and backup runs are recorded in `HANDYTESTED_PHASE4_CHECKPOINT.md`.
- Mobile comparison tables scroll inside their wrappers. AdSense auto-ad iframe hosts still cause page-wide overflow in sampled mobile article views; no AdSense account setting was changed. Image-rights checks and global site issues remain open. Full interim status is in `HANDYTESTED_PHASE4_REPORT.md`.
- Published the indoor hydroponics guide (P1, post 185) after removing Click & Grow's Smart Soil system from the hydroponic lineup and declining to assert current AeroGarden stock. Three manufacturer-documented systems replace the old picks. Dry-run [35536983815](https://github.com/HeberPython/agente-sites/actions/runs/35536983815) and apply/backup [35536998302](https://github.com/HeberPython/agente-sites/actions/runs/35536998302) passed; public HTTP 200 and workflow title/canonical/meta/content checks passed. Nine of 37 are complete, 28 pending. Next: portable outdoor grills.
- Published portable outdoor grills (P1, post 183), replacing the discontinued Cuisinart and uncertain stand-up/griddle lineup with exact Coleman tabletop and Weber charcoal models, including CPSC carbon-monoxide guidance. Dry-run [35538065630](https://github.com/HeberPython/agente-sites/actions/runs/35538065630), apply and original-post backup [35538082575](https://github.com/HeberPython/agente-sites/actions/runs/35538082575) passed; public HTTP 200. Ten of 37 complete, 27 pending. Next: electric lawn mowers.
- Published electric lawn mowers (P1, post 181), distinguishing the Greenworks 25322 battery/charger kit from BLACK+DECKER BEMW472BH corded and removing unsupported old budget/model claims. Initial apply [35538345755](https://github.com/HeberPython/agente-sites/actions/runs/35538345755) received HTTP 403 before any write; repeat dry-run [35538372442](https://github.com/HeberPython/agente-sites/actions/runs/35538372442) and apply/backup [35538395880](https://github.com/HeberPython/agente-sites/actions/runs/35538395880) passed. Public HTTP 200. Eleven of 37 complete, 26 pending. Next: earbuds under $300.
- Published premium wireless earbuds (P1, post 179) with current Apple, Samsung and Bose generations, compatibility restrictions and attributed battery claims. Dry-run [35538606677](https://github.com/HeberPython/agente-sites/actions/runs/35538606677) and apply/backup [35538622066](https://github.com/HeberPython/agente-sites/actions/runs/35538622066) passed; public HTTP 200. Twelve of 37 complete, 25 pending. Next: high-performance blenders.
# Phase 4 blender release (2026-09-20)

Published the researched smoothie-blender rewrite for post 175 after focused tests, [dry-run 35538884487](https://github.com/HeberPython/agente-sites/actions/runs/35538884487), and [apply 35538909594](https://github.com/HeberPython/agente-sites/actions/runs/35538909594) with original-post backup. Public article and both related guides returned HTTP 200. The release retained Vitamix E310, Breville BBL620 and Ninja BN701 with manufacturer evidence; it did not invent hands-on performance, prices, ASINs or exact direct product links. Phase 4 stands at 13/37, with smart-home automation next.
# Phase 4 smart-home automation release (2026-09-20)

Published the smart-home automation rewrite for post 173 after manufacturer verification, local tests, [dry-run 35539248856](https://github.com/HeberPython/agente-sites/actions/runs/35539248856) and [apply 35539266719](https://github.com/HeberPython/agente-sites/actions/runs/35539266719) with original-post backup and live-public verification. Four products now have distinct use cases and installation/compatibility limits. Phase 4 stands at 14/37, with kitchen gadgets next.
