# HandyTested Phase 5 interim report (2026-09-21)

**Status: in progress.** This is an execution ledger, not a declaration that Phase 5 is complete. Phase 4's 37 articles and the earlier Paint Sprayers correction were not rewritten. The 38 existing slugs were preserved. Public changes below had guarded dry-runs, backups and live checks; private-console tasks are separately identified.

## Executive summary

The 38 stale excerpts, homepage Top Picks, inaccurate Deals presentation, eight populated category descriptions, homepage search metadata, three unnamed homepage image links and 17 safe image alt texts have been corrected. The largest unresolved technical defect is Rank Math's post sitemap: 38 published/indexable posts versus 35 listed URLs, including five omissions and two unpublished promotion URLs. No unverified Amazon ASIN or price was introduced.

## Baseline and evidence

`HANDYTESTED_PHASE5_BASELINE.md` and `.json` contain the pre-change 57-URL crawl (38 posts, nine pages, ten categories), HTTP, canonical, titles, H1, indexability, sitemap and modification dates. `HANDYTESTED_PHASE5_AMAZON.md`, `HANDYTESTED_PHASE5_INTERNAL_LINKS.md`, `HANDYTESTED_PHASE5_IMAGES.md` and `HANDYTESTED_PHASE5_CANNIBALIZATION.md` carry the focused inventories. Indexable here means public HTTP 200 without observed noindex; it does not prove Google indexing. Sitemap status was independently rechecked after releases and was unchanged.

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
- Post sitemap: 35 URLs. Missing: `/best-robot-vacuums-for-pet-hair-under-300/`, `/best-indoor-hydroponic-gardening-systems-under-300/`, `/best-portable-outdoor-grills-under-300-for-2025/`, `/best-electric-lawn-mowers-under-300-for-2025/`, `/best-wireless-earbuds-under-300-for-2025/`.
- Post sitemap contains two unpublished promotion URLs: `/top-father-s-day-gifts-for-2026-great-deals-and-ideas-2026-07-31/` and `/discover-the-best-amazon-deals-this-summer-2026-08-05/`.
- Page sitemap includes `/pinterest-connect/` despite its `noindex, follow`. Category sitemap includes empty `amazon-deals` despite noindex. Empty `blog` is noindex and absent from sitemap.
- `robots.txt` publicly returns 200, allows normal crawling and references `https://handytested.com/sitemap_index.xml`.
- Cache-busted sitemap requests still show the same discrepancy. The previous Rank Math transient-clear attempt failed; there is no established safe settings API in this project. Do not change slugs, canonical or plugin files to force inclusion. WordPress admin action is documented below.
- JSON-LD scripts parse on all 57 baseline pages: 38 BlogPosting, 56 BreadcrumbList and supporting Organization/WebSite/ImageObject/WebPage/Person/CollectionPage types. No observed Product, Review, rating, price or offer schema. No fabricated review schema was added.

## Search index

Live HTML on sampled Random Orbital Sanders, Stud Finders, Paint Sprayers and Cordless Drills was corrected and includes the affiliate disclosure. Public search results still surfaced stale snippets/cached older versions for some posts; that is not evidence the current article reverted. Search Console access is not connected. Prioritized URL Inspection: home; the five missing-sitemap posts above; Random Orbital Sanders, Stud Finders, Cordless Drills and Laser Levels; Tools/Electronics/Smart Home categories; About, Editorial Policy and Affiliate Disclosure. Inspect current canonical/indexing, resolve sitemap first, submit the sitemap and request recrawl only through Search Console's supported controls.

## Amazon, CTAs and disclosure

The Phase 4 baseline had 109 tagged searches; the current public 38-post inventory has **111** tagged Amazon.com search links including Paint Sprayers. All inspected search URLs contain `handytested0d-20`; zero direct listings/ASINs were verified or introduced. Searches are exact-model discovery destinations, not guaranteed product pages or availability checks. The catalog's `SEARCH VERIFIED` state means syntax/tag/US destination only. Three additional Amazon-owned URLs serve as manufacturer/support citations. CTA copy avoids false urgency and price claims; 111 product CTAs point to search results. The exact Amazon Associate disclosure remains in all articles and on the home, Deals and disclosure page. Direct links require confirmed exact US listings through permitted Amazon tools; SiteStripe/account access is not established in this environment.

## Images

All 38 featured images were visually reviewed via contact sheets. Eleven are plainly mismatched/misleading or need subject verification, detailed in the image inventory. Source/license evidence is not documented for any of the 38; no ownership claim was made and no image was replaced. Twenty-eight had empty media alt at baseline; 17 clearly describable images now have public descriptive alt, leaving 11 without guessed descriptions. Most audited originals are 1080px JPEG; this is not proof of optimized delivery. Replacement requires a documented permitted source/license and correct subject; media cannot be copied arbitrarily from Amazon or search results.

## Internal links and content intent

The article-body inventory finds 81 contextual internal links, 34 unique targets and zero broken article-body targets. Four articles have no incoming article-body link: electric lawn mowers, hydroponic gardens, rotary tools and ergonomic office chairs. Theme/category navigation is excluded from that definition. The two Deals-page 404 links were removed. The seven high-overlap articles in earbuds, smart home and kitchen were reviewed by title, excerpt and intro; their audience/primary intent is distinct, so no merge or redirect is warranted. Add links only at an actually relevant paragraph, with a guarded post revision/backup. Full sitewide and external-manufacturer link crawl remains to be completed.

## Categories, archives and discovery

Eight populated category descriptions were published and publicly checked. Empty `amazon-deals` and `blog` remain noindex; their sitemap treatment differs as noted above. Home, article, Tools category and search views were browser-checked at 320, 375, 768, 1280 and 1920 px. Search and category archives loaded; a complete pagination/author/date/tag archive decision remains pending. Deals no longer implies a verified discount feed. No fake newsletter form was added.

## Pinterest

Anonymous `/pinterest-connect/` returns 200 with `noindex, follow`; the OAuth connect control remains and the URL was preserved. Anonymous HTML checked did not expose the historic `pina_` token prefix or board IDs. This does **not** establish that the authenticated diagnostic view is safe. The page remains in the page sitemap and the plugin/callback configuration is private. Do not remove the page or callback until its OAuth dependency is checked in WordPress/Pinterest admin.

## AdSense and performance

At 320px mobile, an intermittent AdSense Auto Ads insertion inside a latest-posts list produced an `aswift_3` iframe extending to x=489px in one reproduction (document scrollWidth 489). Other reloads did not overflow. This points to a third-party placement, but site/container contribution still needs repeatable diagnosis. No cross-origin iframe manipulation, concealment or blanket AdSense disable was applied.

Playwright lab observations, one unthrottled run per template, **not field Core Web Vitals or Lighthouse scores**:

| Template | 375px TTFB/FCP/LCP/CLS | 1280px TTFB/FCP/LCP/CLS |
|---|---|---|
| Home | 248/508/508 ms / 0.172 | 188/432/432 ms / 0.088 |
| Cordless Drills (Tools) | 144/368/368 ms / 0.430 | 166/576/576 ms / 0.216 |
| Smart Home Hubs | 138/384/384 ms / 0.431 | 136/296/296 ms / 0.215 |
| Premium Earbuds | 137/368/368 ms / 0.430 | 132/296/344 ms / 0.220 |
| Tools category | 139/628/680 ms / 0.427 | 170/404/404 ms / 0.213 |

CLS came from PerformanceObserver buffered after load; cause is not proven. INP was not measurable from these visits. PageSpeed Insights request returned 429, so no PSI/CrUX field dataset is claimed. One GA `gtag/js` and one AdSense script were observed; no public `gtm.js` was observed in samples. Avoid duplicate tag installation. Further resource/image/CLS attribution and a safe site-owned fix are pending.

## Accessibility and Astra

The home now has named Top Picks image links. Sampled pages have one H1 and skip links; comparison tables scroll within their own container on narrow screens. Screen-reader, full keyboard, contrast, mobile menu and focus tests remain incomplete. Astra's active footer builder still does not render the prepared widget; a supported Customizer/footer configuration is preferable to changing untracked theme files. No claim of full accessibility compliance is made.

## Analytics and future product data

Existing GA and AdSense script presence was checked, but conversion events, actual collection, consent and GTM/Analytics account settings were not verified. Do not add `affiliate_click`, `amazon_click`, search or category events before identifying the existing data layer to avoid duplicate telemetry; never send PII. For future PA-API integration, maintain exact model-to-ASIN mapping, permitted API price/availability source, retrieval timestamp/cache, failure fallback to verified search, region and tracking ID, and obey API terms/limits. No PA-API credentials are present in this release and no scraping integration was created.

## Manual admin actions

1. **WordPress > Rank Math SEO > Sitemap Settings:** inspect post exclusions/robots, adjust the supported Links Per Sitemap control and save; then **Settings > Permalinks > Save Changes** without changing URL structure, clear server/CDN sitemap cache, and compare the 38 public posts with the regenerated post sitemap. Check the five missing posts and remove two unpublished promo URLs from XML. Also exclude noindex Pinterest and empty amazon-deals category from their sitemaps if Rank Math settings support it. See [Rank Math cache guidance](https://rankmath.com/kb/exclude-sitemaps-from-caching/). Avoid direct DB edits.
2. **Google Search Console > Sitemaps and URL Inspection:** verify `sitemap_index.xml`, inspect the prioritized URLs above, compare selected canonical and coverage, submit the corrected sitemap and request supported recrawl where warranted. Stale snippets alone are not a reason to rewrite current copy.
3. **WordPress > Plugins/Pages and Pinterest Developer app > Redirect URIs:** check the callback dependency for `/pinterest-connect/`, inspect authenticated diagnostic output for token prefixes/board data, disable or gate diagnostics, and keep `noindex` while excluding the technical page from XML. Never paste tokens into reports.
4. **AdSense > Ads > By site > HandyTested > Auto ads settings:** inspect in-page/in-feed placement and mobile preview at 320px; adjust a problematic Auto Ads format/placement in account controls if the overflow is reproducible. Preserve compliant ad visibility; do not CSS-hide the iframe.
5. **WordPress > Appearance > Customize > Footer Builder / Additional CSS:** activate the existing footer area and test home/article/category/search/trust pages across widths. Do not edit the untracked Astra archive or installer.
6. **Amazon Associates > SiteStripe:** validate exact US model/listing and tracking ID individually before any search-to-direct link conversion. No account credentials or ASINs should be placed in the repository.
7. **Media owner/editor:** provide documented licenses or owned replacement media for the mismatched featured images; verify rights before upload or replacement.

## Remaining risks and next execution

Sitemap/Rank Math inconsistency, stale Google index, 11 image/alt exceptions and 38 undocumented licenses, no verified direct Amazon listings, intermittent AdSense overflow, unverified field CWV/INP, incomplete sitewide/external-link and accessibility audit, and unverified analytics events remain. See `HANDYTESTED_PHASE5_CHECKPOINT.md` for the exact continuation. No public content is left in a partially applied batch.
