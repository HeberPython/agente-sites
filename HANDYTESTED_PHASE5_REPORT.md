# HandyTested Phase 5 report (2026-09-21)

**PHASE 5 OPERATIONALLY STABLE — PRIMARY POST SITEMAP RECONCILED.** The Rank Math post sitemap now exactly matches all 38 published WordPress posts. This is not a claim that AdSense placement, Astra footer, account analytics or media rights are resolved. Phase 4's 37 articles and the earlier Paint Sprayers correction were not rewritten. The 38 existing slugs were preserved. Public changes below had guarded dry-runs, backups and live checks; private-console tasks are separately identified.

## Executive summary

The 38 stale excerpts, homepage Top Picks, inaccurate Deals presentation, eight populated category descriptions, homepage search metadata, three unnamed homepage image links and 17 safe image alt texts have been corrected. The former Rank Math defect was repaired from 35 sitemap URLs to the exact 38-post published set without Hostinger purge or rewrite flush. No unverified Amazon ASIN or price was introduced.

## Baseline and evidence

`HANDYTESTED_PHASE5_BASELINE.md` and `.json` contain the pre-change 57-URL crawl (38 posts, nine pages, ten categories), HTTP, canonical, titles, H1, indexability, sitemap and modification dates. `HANDYTESTED_PHASE5_AMAZON.md`, `HANDYTESTED_PHASE5_INTERNAL_LINKS.md`, `HANDYTESTED_PHASE5_IMAGES.md` and `HANDYTESTED_PHASE5_CANNIBALIZATION.md` carry the focused inventories. Indexable here means public HTTP 200 without observed noindex; it does not prove Google indexing. The earlier 35-URL sitemap evidence is retained below as diagnosis history; the final repair validation supersedes it.

## Changes published

| Surface | Before | After | Apply run / backup artifact | Live validation |
|---|---|---|---|---|
| All 38 post excerpts and home Top Picks | Outdated claims and copy | Current research-led excerpts; three curated cards draw current WP titles/excerpts | `35658847655` / `10666459030` | REST excerpts, homepage and Tools archive checked |
| Eight populated categories | Thin generic descriptions | Concise task-specific descriptions, no slug changes | `35660264309` / `10666616174` | Public category REST and archive checked |
| `/deals/`, home/menu/footer labels | Unverified deal framing, two links to unpublished 404 posts | Value Picks & Product Discovery and six live guides | `35660671838` / `10667262340` | 404 links absent and new links public |
| Homepage curated image links | Three links without accessible names | Titles supplied as `aria-label` | `35661341192` / `10667698317` | Browser found zero unnamed links on home |
| Homepage SEO | Title/description promised Amazon Deals | Research-led guides and value-picks metadata | `35661655709` / `10667387621` | Public title, description and canonical checked |
| 17 featured-image media records | Empty alt despite visually interpretable images | Literal scene descriptions without guessed model | `35662002618` / `10667764458` | All 17 confirmed by public WP media API |

The corresponding guarded sources and workflows are versioned in this repository. Backups are GitHub Actions artifacts, not proof that underlying rights or platform settings are resolved.

## Homepage and excerpts

Cordless Drills, Random Orbital Sanders and Smart Home Hubs cards were compared with the current WordPress posts and refreshed. Top Picks remains a small curated list by stable slug; title/excerpt/link are fetched from WordPress by the release renderer. Latest Guides uses the WordPress latest-posts block. The old first-hand-testing and deals wording was not found on the checked live home. All 38 excerpts now reflect their corrected articles; card and archive samples were checked. Future content releases still need the homepage release step until cards become runtime-rendered.

## SEO, robots and sitemap

- Public REST: 38 published posts; all 38 crawled as HTTP 200, self-canonical and without observed noindex. No sampled commercial post had a canonical or H1 defect.
- Before repair, the post sitemap had 35 URLs. Missing: `/best-robot-vacuums-for-pet-hair-under-300/`, `/best-indoor-hydroponic-gardening-systems-under-300/`, `/best-portable-outdoor-grills-under-300-for-2025/`, `/best-electric-lawn-mowers-under-300-for-2025/`, `/best-wireless-earbuds-under-300-for-2025/`.
- Before repair, it also contained two draft promotion URLs: `/top-father-s-day-gifts-for-2026-great-deals-and-ideas-2026-07-31/` and `/discover-the-best-amazon-deals-this-summer-2026-08-05/`.
- Page sitemap includes `/pinterest-connect/` despite its `noindex, follow`. Category sitemap includes empty `amazon-deals` despite noindex. Empty `blog` is noindex and absent from sitemap.
- `robots.txt` publicly returns 200, allows normal crawling and references `https://handytested.com/sitemap_index.xml`.
- Cache-busted sitemap requests originally showed the same discrepancy. Read-only SSH/WP-CLI diagnostics then traced the stale generated set to Rank Math's internal sitemap storage and confirmed the supported mechanism in the installed Rank Math 1.0.279 code.
- Authenticated read-only [sitemap diagnostic run 35662985539](https://github.com/HeberPython/agente-sites/actions/runs/35662985539) confirmed all five missing posts are `publish`, both stale XML entries are `draft`, and an included control post is `publish`. Rank Math robots/canonical/exclusion metadata was not exposed through the authenticated WP REST response for any of the eight, so REST cannot distinguish their plugin settings.
- Final public REST/XML comparison on 2026-09-21 again found 38 published posts, 35 post-sitemap URLs, the same five omissions and two extra draft URLs, including with a cache-busting query. All 111 Amazon search links still carry the US tracking tag, all 38 rendered article bodies retain the Associate disclosure, and no direct `/dp/` product link was introduced.
- Repair completed through `HandyTested - Phase 5 Rank Math Post Sitemap Repair` at commit `d83991c`. With all guards passing, it applied `RankMath\Sitemap\Cache::invalidate_storage("post")` and `invalidate_storage("1")`; `rank_math/pre_clear_cache` prevented external cache clearing. The regenerated XML changed hash and now contains exactly the 38 published posts. All five missing guides were added, both draft promotion URLs were removed, and no legitimate published post disappeared. Etapa B (Hostinger/plugin cache purge) and Etapa C (rewrite/permalink flush) were unnecessary. Do not rerun the repair while the sets remain equal.
- JSON-LD scripts parse on all 57 baseline pages: 38 BlogPosting, 56 BreadcrumbList and supporting Organization/WebSite/ImageObject/WebPage/Person/CollectionPage types. No observed Product, Review, rating, price or offer schema. No fabricated review schema was added.

## Search index

Live HTML on sampled Random Orbital Sanders, Stud Finders, Paint Sprayers and Cordless Drills was corrected and includes the affiliate disclosure. Public search results still surfaced stale snippets/cached older versions for some posts; that is not evidence the current article reverted. Search Console access is not connected. Prioritized URL Inspection: home; the five formerly missing-sitemap posts above; Random Orbital Sanders, Stud Finders, Cordless Drills and Laser Levels; Tools/Electronics/Smart Home categories; About, Editorial Policy and Affiliate Disclosure. Submit/revalidate the corrected sitemap and request recrawl only through Search Console's supported controls.

## Amazon, CTAs and disclosure

The Phase 4 baseline had 109 tagged searches; the current public 38-post inventory has **111** tagged Amazon.com search links including Paint Sprayers. All inspected search URLs contain `handytested0d-20`; zero direct listings/ASINs were verified or introduced. Searches are exact-model discovery destinations, not guaranteed product pages or availability checks. The catalog's `SEARCH VERIFIED` state means syntax/tag/US destination only. Three additional Amazon-owned URLs serve as manufacturer/support citations. CTA copy avoids false urgency and price claims; 111 product CTAs point to search results. The exact Amazon Associate disclosure remains in all articles and on the home, Deals and disclosure page. Direct links require confirmed exact US listings through permitted Amazon tools; SiteStripe/account access is not established in this environment.

## Images

All 38 featured images were visually reviewed via contact sheets. Eleven are plainly mismatched/misleading or need subject verification, detailed in the image inventory. Source/license evidence is not documented for any of the 38; no ownership claim was made and no image was replaced. Twenty-eight had empty media alt at baseline; 17 clearly describable images now have public descriptive alt, leaving 11 without guessed descriptions. Most audited originals are 1080px JPEG; this is not proof of optimized delivery. Replacement requires a documented permitted source/license and correct subject; media cannot be copied arbitrarily from Amazon or search results.

## Internal links and content intent

The article-body inventory finds 81 contextual internal links, 34 unique targets and zero broken article-body targets. Four articles have no incoming article-body link: electric lawn mowers, hydroponic gardens, rotary tools and ergonomic office chairs. Theme/category navigation is excluded from that definition. The two Deals-page 404 links were removed. A second public crawl of 57 source documents and 57 deduplicated internal destinations (posts, pages, home, eight categories and search) found **57 GET 200, zero 404**. One author-archive URL returns 200 after redirecting to home; its template/function should be reviewed before adding author links. HEAD returned 500 for many healthy URLs, so GET was used for classification. The seven high-overlap articles in earbuds, smart home and kitchen were reviewed by title, excerpt and intro; their audience/primary intent is distinct, so no merge or redirect is warranted. A direct term check found no natural mention of the four orphan topics in other article bodies; no links were inserted merely to improve a count.

An external-citation crawl of the 38 article bodies ([run 35663175793](https://github.com/HeberPython/agente-sites/actions/runs/35663175793), artifact `10668331670`) tested 164 unique non-Amazon URLs: 141 HTTP 200, four 404, one 400, 14 403 and four network failures. Four outdated DEWALT PDFs and one Zircon manual URL that led to a generic page were replaced with verified official exact-model sources. All five changed posts were independently checked as published with old URL absent, new citation present and disclosure intact. Initial four-post apply run `35663666632` hit 503 after writing the first post and rollback also hit 503; public verification confirmed that post correct and the other three unchanged. The remaining three were completed separately with backups. A separate 403 attempt for post 20 failed before backup/write; its controlled retry succeeded. The 14 HTTP 403 and four network failures remain **inconclusive** due to bot/access restrictions, not declared broken or removed. Public browsing confirmed the 2x4 Basics chair product page still exists; Makita pages timed out in one browsing route. Recheck those sources individually before any further edit.

| Corrected citation | Dry-run / apply run | Backup artifact |
|---|---|---:|
| Heat guns, post 56 (first post of interrupted batch) | `35663629941` / `35663666632` | `10668605462` |
| Cordless Drills, post 20 | `35663961836` / `35664117291` | `10667883639` |
| Cordless Brad Nailers, post 143 | `35664161121` / `35664189404` | `10668626065` |
| Cordless Circular Saws, post 59 | `35664239512` / `35664268982` | `10667913924` |
| Stud Finders, post 44 | `35664519210` / `35664552610` | `10668966322` |

## Categories, archives and discovery

Eight populated category descriptions were published and publicly checked. Empty `amazon-deals` and `blog` remain noindex; their sitemap treatment differs as noted above. Home, article, Tools category and search views were browser-checked at 320, 375, 768, 1280 and 1920 px. Search and category archives loaded. A focused follow-up found search results `noindex, follow` with ten results for `drill`; Tools page 2 has four different posts and a self-canonical but repeats page 1's title and meta description. The actual article author link `/author/editorial-team/` and a sampled date archive redirect to home; an invented `/author/htadmin/` path returns 404 and is not treated as a site link. An absent sample tag archive returns 404/noindex. Broader tag/date policies still need admin review; no global noindex rule was applied. Deals no longer implies a verified discount feed. No fake newsletter form was added.

## Pinterest

Anonymous `/pinterest-connect/` returns 200 with `noindex, follow`; the OAuth connect control remains and the URL was preserved. Anonymous HTML checked did not expose the historic `pina_` token prefix or board IDs. This does **not** establish that the authenticated diagnostic view is safe. The page remains in the page sitemap and the plugin/callback configuration is private. Do not remove the page or callback until its OAuth dependency is checked in WordPress/Pinterest admin.

## AdSense and performance

An earlier 320px visit recorded an intermittent `aswift_3` iframe extending to x=489px and document scrollWidth 489. In 24 new reloads across home, Cordless Drills, the correct Smart Home Hubs article and Tools category at 320/375px, document scrollWidth stayed at 305/360px or less: that page-level overflow was **not reproduced**, not declared fixed. Cordless Drills did reproducibly receive Auto Ads inside a 720px comparison-table row: `google-auto-placed ap_container` / `ins.adsbygoogle` and one `aswift_4` reached x=494-630px at mobile widths. The article's existing table wrapper has `overflow-x:auto` (260/315px client width), so those ad nodes were outside the visible table region without causing document-level overflow in these visits. The placement is Google-created, not a fixed-width site rule; it should be reviewed with AdSense's preview/excluded-areas controls, not clipped or hidden with site CSS. Google also inserted `google-anno` ad-intent links into text and a vignette intercepted a Playwright hover attempt; those are separate Auto Ads formats. No cross-origin iframe manipulation, concealment or blanket AdSense disable was applied.

Playwright lab observations, one unthrottled run per template, **not field Core Web Vitals or Lighthouse scores**:

| Template | 375px TTFB/FCP/LCP/CLS | 1280px TTFB/FCP/LCP/CLS |
|---|---|---|
| Home | 248/508/508 ms / 0.172 | 188/432/432 ms / 0.088 |
| Cordless Drills (Tools) | 144/368/368 ms / 0.430 | 166/576/576 ms / 0.216 |
| Smart Home Hubs | 138/384/384 ms / 0.431 | 136/296/296 ms / 0.215 |
| Premium Earbuds | 137/368/368 ms / 0.430 | 132/296/344 ms / 0.220 |
| Tools category | 139/628/680 ms / 0.427 | 170/404/404 ms / 0.213 |

Follow-up `PerformanceObserver` instrumentation recorded shift sources before and after ad insertion at 320, 375 and 1280px. Large shifts were attributable to late Google Auto Ads at the top of `#page`, between Astra's header and `#content`: a `google-auto-placed` block of 300-380px appeared, and `#content` moved by the same amount. Examples: Cordless Drills 320px, content y=80→405, shift 0.329; Premium Earbuds 375px, y=80→460, shift 0.385; Tools 1280px, y=81→381, shift 0.216; correct Smart Home Hubs 320px, y=80→405, shift 0.329 on one load, versus no top ad and zero shift on another. Home `#top-picks` shifted after top-ad insertion at 375px (0.183) and 1280px (0.103). Some smaller shifts (about 0.002-0.017) affected an in-content paragraph, an archive card or ad element; their individual cause was not proven. This is **third-party top-placement CLS**, not evidence that the article image, font or footer caused the large shifts. Reserving a permanent 300-380px blank region when no ad appears would damage UX, so no speculative CSS was applied. INP was not measurable from these visits. PageSpeed Insights returned 429, so no PSI/CrUX field dataset is claimed.

Targeted final browser QA covered home, Cordless Drills, Tools category, `?s=drill` and How We Review at 320/375/768/1280/1920px (25 page-width combinations): no document-level horizontal overflow; one H1 each; published-page self-canonicals where expected; parseable sampled JSON-LD; one GA script and one AdSense script per page. Search is a noindex archive and had no canonical in that check. The article table scrolls internally and retained its disclosure/CTA. The home still has two footers. This is targeted QA, not a repeat of the healthy 57-URL crawl or proof of field CWV.

## Accessibility and Astra

The home now has named Top Picks image links. Sampled pages have one H1 and skip links; comparison tables scroll within their own container on narrow screens. A 320px keyboard sample reached the skip link, navigation and main-menu toggle with a visible 3px focus outline; Enter expanded the menu and its `aria-expanded` state, and the next Tab reached its first link. A simple DOM-name scan of home, article, Tools category, search and How We Review found no unnamed links/buttons/inputs; this is not a screen-reader or full WCAG audit. Computed-color samples passed 4.5:1 for home hero/nav/footer and article body/nav, but normal-size article links, author links, Astra footer credit and archive pagination use `#e8440a`: **3.99:1 on white**, 3.79:1 on `#f9f9f9`. White text on the orange current-page chip is also 3.99:1. The 517-byte published `#wp-custom-css` explicitly sets `--ast-global-color-0: #e8440a` and orange pagination/hover styles. Hovered article CTA sampled at `#c73208` on white (5.40:1), while normal state fails; focus has a visible dotted outline but retains the normal failing text color. `#c23b0a` would give 5.35:1 on white and 5.08:1 on `#f9f9f9`, but only 2.71:1 as text on the dark `#1d2b33` footer. Do **not** replace a global swatch without scoping/rechecking dark-background states. Home's embedded CTA and dark-footer styles are separate. Public HTML confirms home has both `ht-home-footer` and Astra `site-footer`, while article, category, search and About have only Astra's footer. Astra's active footer builder still does not render the prepared widget. No authenticated WordPress browser tab or supported Customizer CSS write endpoint is available here, so native Customizer/Footer Builder work is manual; the untracked theme files were untouched. No claim of full accessibility compliance is made.

## Analytics and future product data

Google Site Kit emits one sampled `gtag/js` script and `window.dataLayer` contains `set`, `js`, `config`, `gtm.dom` and `gtm.load`; no separate `gtm.js` script was seen. A sampled home visit sent one GA4 `page_view` collection request and received HTTP 204, which proves browser dispatch/acceptance for that visit, **not** account reporting or all-page delivery. Inline source and sampled dataLayer had no `affiliate_click`, `amazon_click`, `search_use` or `category_click` event. AdSense has one loader script in the 25-template QA. Do not add a second tag or claim custom events are received. Sitewide event instrumentation and GA4 DebugView/Realtime validation require the existing Site Kit/WordPress admin integration or an approved sitewide hook; no supported sitewide JavaScript publication route is established through the current REST releases. Never send PII. For future PA-API integration, maintain exact model-to-ASIN mapping, permitted API price/availability source, retrieval timestamp/cache, failure fallback to verified search, region and tracking ID, and obey API terms/limits. No PA-API credentials are present in this release and no scraping integration was created.

## Remaining Phase 5 priorities

- **P0 — none identified.** The published post set, its primary XML discovery surface and existing affiliate integrations are operational.
- **P1 — Search Console:** submit/revalidate the corrected sitemap and inspect the prioritized pages through official controls.
- **P1 — AdSense placement/CLS:** review top and in-table Auto Ads placements with supported account controls, then re-measure; do not hide ads with CSS.
- **P1 — Amazon monetization:** verify exact US listings and `handytested0d-20` in SiteStripe before replacing tagged searches; never guess ASINs.
- **P1 — image rights:** document rights or replace the 11 uncertain/mismatched images with owned or licensed assets; do not infer licenses.
- **P2 — analytics/accessibility/template:** validate the four business events, make scoped WCAG contrast/footer fixes through supported controls, and perform field performance/accessibility follow-up.
- **P2 — discovery/editorial maintenance:** address orphan opportunities, repeated paginated metadata and inconclusive citations only with supporting evidence.
- **P3 — Pinterest/empty taxonomy:** review `/pinterest-connect/` and empty `amazon-deals` sitemap treatment separately later; neither reopens the resolved post-sitemap reconciliation.

## Remaining risks and next execution

The primary Rank Math post-sitemap inconsistency is resolved. Remaining risks are stale Google index signals pending Search Console validation, 11 image/alt exceptions and 38 undocumented licenses, no verified direct Amazon listings, one earlier unreproduced document-level overflow, reproducible AdSense placement in comparison tables and top-of-page CLS, unverified field CWV/INP, inconclusive external 403/network citations, confirmed orange-link/pagination contrast deficits, incomplete full WCAG audit and absent custom analytics events. No site-owned CSS or content rule was proven responsible for the large shifts; no safe supported Customizer/script publication route is available with the current REST access. The sitewide internal GET crawl is complete. See `HANDYTESTED_PHASE5_CHECKPOINT.md` for prioritized continuation. No public content is left in a partially applied batch, and the remaining items do not prevent operational closure of Phase 5.
