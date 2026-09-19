# HandyTested audit

Snapshot: 2026-09-19. Sources: repository `main` at `cf0534f`, public WordPress REST API, public HTML, `robots.txt`, Rank Math sitemaps. Reproduce the content inventory with `python handytested_public_audit.py`. This is a public audit: WordPress administrator settings, private traffic data, Amazon earnings, Search Console, AdSense account, and field Core Web Vitals were not available.

## Stack and architecture

- WordPress CMS on `handytested.com`; Astra theme is visible in page source/footer. The repo holds Python automation and GitHub Actions, not the deployed theme/plugin source or database.
- Rank Math is used for SEO metadata and sitemap generation. The portal setup script writes WordPress pages/categories and Rank Math metadata through APIs.
- Nine public pages, 38 published posts, ten categories. No product database or verified ASIN catalog is present.
- The front page is a WordPress static page (`home-page`) built by `setup_handytested_portal.py` using inline HTML/CSS and a snapshot of posts at script run time. New posts do not automatically appear there. The visible homepage still leads with May 2026 content despite newer September posts.
- `pub_ht_pro.py` is scheduled three times weekly; `pub_ht_once.py` is manual. The promo agent checks email on a two-hour schedule. `agente_sites.py` currently schedules other sites, but can target HandyTested when run manually.
- All 38 posts have featured media and a disclosure string. Image licensing, actual alt quality and thumbnail sizing need media-level review. The generator searches Unsplash by topic, so image relevance to the exact recommended model is not established.
- The homepage loads Google Tag Manager and AdSense scripts. The active account IDs, consent setup, placement rules, revenue and mobile layout shift require administrator and browser verification. No AdSense code was removed.

## Findings by severity

### CRITICAL

1. **Unsupported first-hand claims.** Public text in 33/38 posts matches testing language. Several describe specific temperatures, timings, locations or weeks of use. The repository has no test evidence or measurement records. Examples: [heat guns](https://handytested.com/best-heat-guns-for-diy-projects-under-80-in-2025/), [smart home hubs](https://handytested.com/best-smart-home-hubs-under-150-for-2025/), [wireless earbuds](https://handytested.com/best-wireless-earbuds-under-100-for-2025/). Claims require paragraph-level editorial review; a global word replacement would leave unsupported outcomes intact.
2. **Unverified commercial data.** 34/38 posts contain dollar values in body text and 28/38 mention ratings. No current approved price feed or source records are in the repo. Some posts assert exact under-$X positioning and product rankings without dated evidence. The [paint sprayer guide](https://handytested.com/top-5-home-diy-paint-sprayers-under-300-in-2025/) mentions `DeWalt DCE530B` as a paint sprayer, but the model needs product identity verification before recommendation.

### HIGH

3. **Sitemap gap.** `post-sitemap.xml` returned 35 post URLs while REST listed 38 published posts; the latest robot-vacuum post was absent. Rank Math sitemap cache and post indexability need admin inspection. `page-sitemap.xml` includes `/pinterest-connect/`.
4. **Affiliate destination quality.** All 247 observed Amazon links in published posts point to Amazon.com search results (`/s?k=`), with tag `handytested0d-20`; none are verified direct product URLs. A search may contain other models and sponsored results. Direct SiteStripe or verified-ASIN links should replace product-specific CTAs after catalog review. Do not invent ASINs or assume commission attribution from browser URL appearance alone.
5. **Public technical page.** `Pinterest Connect Demo` is linked from the main WordPress page list and appears in the sitemap. It exposes account/board diagnostics and a token prefix in the UI. Confirm OAuth callback dependencies before restricting access, hiding the page from navigation, or adding `noindex`.
6. **Stale editorial signals.** 24/38 published titles contain 2025 even though all 38 posts were published in 2026. Re-research models and claims before changing titles; preserve slugs unless a redirect is planned.
7. **Disclosure wording.** Existing pages and post headers use varying third-person statements. Amazon's [official disclosure guidance](https://affiliate-program.amazon.com/help/node/topic/GHQNZAU6669EZS98) requires the exact statement “As an Amazon Associate I earn from qualifying purchases.” Display it clearly with affiliate links and site identity.

### MEDIUM

8. **Homepage freshness and navigation.** The front page is generated once and currently omits newer articles. Navigation has Home, Electronics, Tools, DIY, About plus a public page list; Best Picks, Compare, Learn, Deals are not coherent top-level journeys yet.
9. **Trust and heading hierarchy.** Five institutional pages (`about`, `deals`, `how-we-review`, `editorial-policy`, `affiliate-disclosure`) currently have two H1s (Astra title plus content title). The methodology page previously implied undocumented hands-on work. Author expertise and corrections need verifiable records. About/Contact/Privacy exist; Terms was not among public pages.
10. **Article UX.** Existing comparison tables and affiliate blocks need 320px mobile verification. Inline card styling and search-result CTAs are inconsistent. Some generated tables include fixed prices and ratings that lack source records.
11. **Taxonomy.** `amazon-deals` and `blog` have zero published posts; `tools` has 14 while `office-gear` has one. Category landing pages are largely archives, not curated editorial hubs.

### LOW / UNVERIFIED

12. **SEO HTML sweep.** All 47 public URLs (nine pages, 38 posts) returned canonical, meta description, Open Graph title and JSON-LD in the source scan. All posts had one H1; five institutional pages had two. Rank Math supplies robots and sitemaps. Presence of JSON-LD does not establish semantic correctness; breadcrumbs, pagination, alt text, redirects and duplicate content remain to be inspected.
13. **Performance.** Homepage HTML was about 139 KB in a single fetch and loads AdSense/GTM. No mobile/desktop field LCP, CLS, INP or lab run was available; no numerical performance claim is made.

## Public inventory

Flags: `Y` means the public body matched a testing phrase (T), contains dollar amounts (P), or title contains 2025 (Y). Some matches are generic disclosure text, while others assert detailed first-hand measurements; both need editorial review. All 38 contain Amazon search links.

| Article slug | Category | Y | T | P |
|---|---|:---:|:---:|:---:|
| best-robot-vacuums-for-pet-hair-under-300 | cleaning | | Y | Y |
| best-indoor-hydroponic-gardening-systems-under-300 | diy | | Y | Y |
| best-portable-outdoor-grills-under-300-for-2025 | outdoor | Y | Y | Y |
| best-electric-lawn-mowers-under-300-for-2025 | tools | Y | Y | Y |
| best-wireless-earbuds-under-300-for-2025 | electronics | Y | Y | Y |
| best-high-performance-blenders-for-home-smoothies | kitchen | | Y | |
| top-smart-home-automation-devices-under-300-for-2025 | smart-home | Y | Y | |
| best-kitchen-gadgets-under-300-for-modern-chefs | kitchen | | Y | Y |
| best-smart-home-devices-under-300-for-2025 | smart-home | Y | Y | Y |
| best-diy-outdoor-furniture-kits-under-300-for-2025 | diy | Y | Y | Y |
| best-cordless-impact-wrenches-under-300-for-2025 | tools | Y | Y | |
| best-projectors-under-300-for-home-entertainment | electronics | | Y | Y |
| top-5-ergonomic-office-chairs-under-300-for-comfort | office-gear | | Y | Y |
| best-carpet-cleaners-for-pet-owners-in-2025 | cleaning | Y | Y | |
| best-cordless-nail-guns-under-300-for-diy-projects | diy | | Y | Y |
| best-camping-gear-under-300-for-outdoor-adventures | outdoor | | Y | Y |
| best-kitchen-appliances-under-300-for-home-chefs | kitchen | | Y | Y |
| best-smart-home-security-cameras-under-300-for-2025 | smart-home | Y | Y | Y |
| best-home-diy-tool-sets-for-under-300-in-2025 | tools | Y | Y | Y |
| top-5-home-diy-paint-sprayers-under-300-in-2025 | tools | Y | Y | Y |
| best-cordless-ratchets-for-diy-mechanics-in-2025 | tools | Y | | Y |
| best-electric-screwdrivers-for-diy-projects-in-2025 | tools | Y | | Y |
| best-smart-tvs-under-300-for-2025-viewing-experience | electronics | Y | Y | Y |
| best-noise-canceling-headphones-under-300-for-2025 | electronics | Y | Y | Y |
| best-home-drill-presses-under-300-for-diy-enthusiasts | diy | | Y | Y |
| top-5-digital-torque-wrenches-under-100-for-accurate-torque | tools | | | Y |
| best-cordless-circular-saws-under-150-for-diy-projects | tools | | | Y |
| best-heat-guns-for-diy-projects-under-80-in-2025 | diy | Y | Y | Y |
| best-multimeters-under-50-for-home-electricians-2025 | electronics | Y | Y | Y |
| best-voltage-testers-for-home-electrical-work-2025 | tools | Y | Y | Y |
| best-rotary-tools-under-50-for-diy-projects-2025 | tools | Y | Y | Y |
| best-stud-finders-under-50-for-home-projects-2025 | tools | Y | Y | Y |
| best-smart-home-hubs-under-150-for-2025 | electronics | Y | Y | Y |
| best-random-orbital-sanders-for-diy-projects-2025 | diy | Y | Y | Y |
| best-laser-levels-for-diy-home-projects-under-60 | tools | | Y | Y |
| best-oscillating-multi-tools-under-75-for-2025 | tools | Y | Y | Y |
| best-wireless-earbuds-under-100-for-2025 | electronics | Y | Y | Y |
| best-cordless-drills-under-100 | tools | | | Y |

Public pages: `/`, `/about/`, `/contact/`, `/privacy-policy/`, `/affiliate-disclosure/`, `/editorial-policy/`, `/how-we-review/`, `/deals/`, `/pinterest-connect/`.

Category counts: tools 14, electronics 7, diy 6, smart-home 3, kitchen 3, cleaning 2, outdoor 2, office-gear 1, amazon-deals 0, blog 0.

## Business and opportunity

Position HandyTested as research-led product discovery for the existing US Amazon program. Keep existing URLs and categories while adding editorial journeys: Best Picks, Compare, Learn, Deals. Best first clusters from current coverage: drills/sanders/paint tools, electrical measurement, smart home. Highest-value future tools: Paint Coverage Calculator (paint guides), Battery Runtime Calculator (cordless tools), then Torque Converter; wire gauge requires extra safety review. Do not publish empty cluster pages.

## Access-dependent checks

Inspect Rank Math sitemap cache and post indexability, Google Search Console coverage, GA4/GTM events, AdSense placements and policy center, mobile Core Web Vitals, image media licenses/alt text, and Pinterest OAuth implementation in WordPress. These cannot be concluded from the repo/public API alone.
