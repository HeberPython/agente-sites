# HandyTested Phase 5 checkpoint (2026-09-21)

**PHASE 5 AUTOMATED WORK COMPLETE — MANUAL ADMIN ACTIONS REQUIRED.** Phase 5 as a whole is not complete: sitemap, AdSense account settings, Astra Customizer, Pinterest diagnostics, analytics business events and media rights still need private controls or owner evidence. Phase 4's 37 posts plus Paint Sprayers are complete and must not be redone without a concrete public regression. No batch is left partly applied. Preserve unrelated untracked user files `astra.zip`, `astra_theme/`, `ht_install_astra.php`.

## Completed automatically

- Public 57-URL baseline and focused Amazon, internal-link, image and intent inventories. See `HANDYTESTED_PHASE5_REPORT.md` and companion Phase 5 documents.
- 38 excerpts/current homepage Top Picks; eight category descriptions; honest Value Picks page/labels; home SEO; named Top Picks image links; 17 safe featured-image alt texts.
- Public sitemap recheck: 38 published posts versus 35 sitemap URLs, five missing and two stale unpublished entries. Cache-busted XML unchanged; no unsupported Rank Math edit made.
- 111 current tagged Amazon.com search URLs audited for destination/tag; zero verified direct ASIN links. No fabricated prices, ratings or availability.
- Sampled responsive, schema, robots, disclosure, indexability, Pinterest anonymous view and unthrottled lab performance. Intermittent 320px AdSense iframe overflow reproduced once.
- Earbuds, smart-home and kitchen intent overlaps reviewed; no unsupported merge/redirect.
- Sitewide internal GET crawl: 57 source documents and 57 distinct internal destinations, all HTTP 200; author archive redirects to home. HEAD is unreliable (many false 500 responses). No natural cross-article mentions for the four no-incoming-body-link topics, so no forced links.
- Authenticated read-only sitemap check: five missing posts are published, two stale entries are drafts, Rank Math-specific metadata not exposed by WP REST; run `35662985539`.
- External citations: 164 unique URLs checked in read-only run `35663175793` (artifact `10668331670`); five confirmed stale/misdirected citations replaced and independently verified in posts 56, 20, 143, 59 and 44. Fourteen 403 and four network failures are inconclusive, not broken.
- Final read-only comparison rechecked 38 posts, 35 sitemap URLs with unchanged five missing/two extra, 111 correctly tagged Amazon searches, all 38 article disclosures and zero direct product links. Search is noindex; Tools page 2 is self-canonical with distinct posts but repeats page 1 metadata; the actual author link and a sampled date archive redirect home.
- Public template check: home has both custom and Astra footers, other sampled templates only Astra; 517-byte global custom CSS lacks home styling. At 320px a fresh home reload had no horizontal overflow; the earlier AdSense overflow remains intermittent. Mobile keyboard sample showed visible focus and working menu toggle/`aria-expanded`. GA `gtag/js` and AdSense script remain single-instance in sample; event delivery unverified.
- Targeted computed-color sample found article/footer orange text links at about 3.99:1 on white; a darker candidate `#c23b0a` measures 5.35:1 on white but requires full background/state QA and native Customizer publication. Other sampled home/nav/body colors passed 4.5:1. This is not a full WCAG audit.
- Follow-up CLS source instrumentation: 300-380px `google-auto-placed` top ad inserts between Astra header and `#content`, causing the major 0.1-0.39 lab shifts across home/articles/category. One correct Smart Home Hubs 320px load shifted 0.329; another with no top ad shifted zero. Smaller shifts remain unattributed, but no site-owned rule was proven responsible for major CLS.
- AdSense mobile: 24 reloads across home, Cordless Drills, Smart Home Hubs and Tools at 320/375px did not reproduce prior document scrollWidth 489. Auto Ads did enter a 720px comparison-table row in Cordless Drills and extend past the viewport, but the table's own `overflow-x:auto` contained it; no CSS concealment applied. Ad-intent links and a vignette were also observed.
- Contrast mapped to site custom CSS global orange: normal article/footer links and pagination are 3.99:1 on white (3.79:1 on `#f9f9f9`), including white text on orange active page; hovered CTA `#c73208` passes on white. A candidate `#c23b0a` passes on light backgrounds but fails as text on dark footer; scoped Customizer work required. Home embedded CTA/footer styles pass in samples.
- Analytics: one Site Kit `gtag/js`, a sampled GA4 `page_view` request accepted HTTP 204, no public `gtm.js`, and no requested `affiliate_click`, `amazon_click`, `search_use` or `category_click` event in sampled inline code/dataLayer. No duplicate tag or unvalidated business event added.
- Targeted 25-combination browser QA at 320/375/768/1280/1920px (home, Cordless Drills, Tools category, search, How We Review): no document-level overflow, one H1, parseable sampled JSON-LD, one GA and AdSense loader each; self-canonicals on publishable pages, article disclosure/CTA and internal table scroll intact. Search is noindex with no canonical in sample. This was not a new 57-URL crawl.

## Published, validated and backups

| Change | Dry-run | Apply run | Backup artifact ID | Independent check |
|---|---:|---:|---:|---|
| Excerpts and Top Picks | 35658793524 | 35658847655 | 10666459030 | REST/home/archive |
| Populated category descriptions | 35660220801 | 35660264309 | 10666616174 | category REST/archive |
| Deals to Value Picks, home/menu/footer labels | 35660636389 | 35660671838 | 10667262340 | Deals/home public HTML |
| Homepage image-link names | 35661308021 | 35661341192 | 10667698317 | browser accessibility-name check |
| Homepage SEO | 35661632683 | 35661655709 | 10667387621 | public title/description/canonical |
| 17 descriptive media alt texts | 35661952413 | 35662002618 | 10667764458 | 17/17 public WP media API |
| Heat-gun citation, post 56 | 35663629941 | 35663666632 | 10668605462 | public post REST after runner 503 |
| Cordless-drill citation, post 20 | 35663961836 | 35664117291 | 10667883639 | public post REST |
| Brad-nailer citation, post 143 | 35664161121 | 35664189404 | 10668626065 | public post REST |
| Circular-saw citation, post 59 | 35664239512 | 35664268982 | 10667913924 | public post REST |
| Zircon e50 citation, post 44 | 35664519210 | 35664552610 | 10668966322 | public post REST |

## Next exact action

**With WordPress admin access, inspect Rank Math SEO > Sitemap Settings > General exclusions and affected post robots/canonical, refresh through the supported Links Per Sitemap and Permalinks saves, clear sitemap cache, then compare live XML against all 38 published posts.** Do not mark this resolved until the five missing posts appear, the two draft URLs disappear, and Pinterest/empty amazon-deals sitemap treatment is verified. After that perform Search Console inspection, AdSense placement changes, Astra/footer/contrast correction, Pinterest diagnostic check, GA4 event instrumentation/validation, Amazon SiteStripe verification and licensed image replacements in the priority order below. Every public admin change needs a before-state backup and live QA. No remaining safe automated edit is established with current REST/browser access; do not invent one. Do not re-run the healthy 57-URL crawl or five citation repairs absent a regression.

## Manual admin actions, not global blockers

1. **MANUAL RANK MATH ACTION REQUIRED:** WordPress Rank Math Sitemap Settings/Permalinks and server/CDN cache; reconcile five missing/two stale post URLs and noindex Pinterest/empty amazon-deals entries. Details and exact slugs in the report. The public REST lists a Rank Math `updateSettings` write route but exposes no read schema for the current sitemap values; no undocumented write was made.
2. **MANUAL SEARCH CONSOLE ACTION REQUIRED:** inspect corrected sitemap, home, five missing posts, four stale-index candidates, three main categories and three trust pages in the report's order.
3. **MANUAL ADSENSE ACTION REQUIRED:** Ads > By site > HandyTested > Edit; preview/exclude top banner placement and comparison-table area; review Ad intents text links and Vignette overlay. Re-measure after account changes. Do not CSS-hide ads.
4. **MANUAL ASTRA ACTION REQUIRED:** Appearance > Customize > Footer Builder/Additional CSS; one consistent footer and scoped contrast correction. Back up current settings and test light/dark states. Do not edit untracked theme files.
5. **MANUAL PINTEREST ACTION REQUIRED:** confirm OAuth redirect/callback dependency and gate authenticated token/board diagnostics; keep noindex and remove from sitemap via supported setting.
6. **MANUAL ANALYTICS VALIDATION REQUIRED:** use existing Site Kit tag and approved sitewide hook for four business events, then GA4 DebugView/Realtime; one sampled page_view request is not proof of account reports.
7. **MANUAL AMAZON SITESTRIPE ACTION REQUIRED:** exact US listing verification before replacing any of 111 correctly tagged searches.
8. **LICENSE/REPLACEMENT REQUIRED:** document rights and source appropriate replacements for 11 problematic/uncertain featured images; do not invent alt or license.

## Validated and unresolved

Validated: the previous guarded releases and backups in the table; final REST/XML and Amazon/disclosure comparison; targeted viewport/CLS/contrast/analytics browser QA. No new public write or backup was needed for the latest read-only diagnostics. The sitemap inconsistency is still live. Eleven media alt values remain blank pending accurate images, all 38 media licenses are undocumented, and 18 external citation responses remain inconclusive (not declared broken). The 320px document overflow was not reproduced in 24 new reloads; in-table ad placement and top-ad CLS were. A single unthrottled lab run is not field CWV; INP, full accessibility, orange-link/pagination contrast, account analytics events and Astra footer remain unresolved. Sitewide internal GET link status has been audited. Do not call the entire Phase 5 complete until admin actions are validated publicly.
