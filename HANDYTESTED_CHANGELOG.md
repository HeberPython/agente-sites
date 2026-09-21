# HandyTested changelog

## 2026-09-21: Phase 5 technical and site-consistency releases (in progress)

- Homepage Top Picks / all 38 posts: stale excerpts and card copy replaced with current research-led WordPress titles/excerpts; guarded [dry-run 35658793524](https://github.com/HeberPython/agente-sites/actions/runs/35658793524), [apply 35658847655](https://github.com/HeberPython/agente-sites/actions/runs/35658847655), backup `10666459030`; public REST, homepage and archive checked.
- Eight populated category archives: generic descriptions replaced with concise task-specific copy without slug changes; [dry-run 35660220801](https://github.com/HeberPython/agente-sites/actions/runs/35660220801), [apply 35660264309](https://github.com/HeberPython/agente-sites/actions/runs/35660264309), backup `10666616174`; public category REST and archive checked.
- `/deals/` and home/menu/footer labels: false live-deal framing and two links to unpublished 404 promotions removed; Value Picks now links six published guides; [dry-run 35660636389](https://github.com/HeberPython/agente-sites/actions/runs/35660636389), [apply 35660671838](https://github.com/HeberPython/agente-sites/actions/runs/35660671838), backup `10667262340`; public Deals/home checked.
- Homepage Top Picks image links: three unnamed links now have article-title accessible names; [dry-run 35661308021](https://github.com/HeberPython/agente-sites/actions/runs/35661308021), [apply 35661341192](https://github.com/HeberPython/agente-sites/actions/runs/35661341192), backup `10667698317`; public browser check found zero unnamed home links.
- Homepage Rank Math SEO title/description: outdated Amazon Deals promise replaced with research-led buying-guide/value-picks copy, self-canonical retained; [dry-run 35661632683](https://github.com/HeberPython/agente-sites/actions/runs/35661632683), [apply 35661655709](https://github.com/HeberPython/agente-sites/actions/runs/35661655709), backup `10667387621`; public metadata checked.
- Seventeen relevant featured-image media records: empty alt changed to literal visual descriptions without implying exact model; [dry-run 35661952413](https://github.com/HeberPython/agente-sites/actions/runs/35661952413), [apply 35662002618](https://github.com/HeberPython/agente-sites/actions/runs/35662002618), backup `10667764458`; all 17 public media records checked. Eleven mismatched/uncertain images retain blank alt pending valid replacement or identification.
- Read-only audits: 57-URL baseline, Rank Math sitemap discrepancy (38 published, 35 XML, five missing/two stale), 111 tagged Amazon search destinations, 81 article-body internal links, 38 image/rights records, structured data, browser/AdSense lab samples and overlapping content intents. No direct ASIN or invented price was added. `HANDYTESTED_PHASE5_REPORT.md` and checkpoint list remaining work and precise private-admin actions; Phase 5 is not yet complete.
- Sitewide read-only GET crawl after publication: 57 source documents and 57 unique internal destinations, all returned HTTP 200; the author archive redirects to home. Initial HEAD 500 responses were method-specific false alarms, not broken links. No artificial internal links were added for four no-incoming-body-link articles because other article bodies had no natural topical mention.
- Read-only Rank Math/WP REST diagnostic [run 35662985539](https://github.com/HeberPython/agente-sites/actions/runs/35662985539): five missing-sitemap posts are published, two stale XML URLs are drafts, and Rank Math-specific metadata is not exposed by REST. No sitemap setting or URL was altered.
- External citation [audit run 35663175793](https://github.com/HeberPython/agente-sites/actions/runs/35663175793), artifact `10668331670`: 164 URLs, 141 HTTP 200, four 404, one 400, 14 HTTP 403 and four network errors. The 403/network cases are inconclusive, not removed.
- Five narrow source repairs: Heat Guns post 56, Cordless Drills post 20, Cordless Brad Nailers post 143, Cordless Circular Saws post 59 and Stud Finders post 44 now cite exact-model official pages/manuals instead of four 404 DEWALT PDFs and one Zircon URL that led to generic content. Dry-runs: `35663629941`, `35663961836`, `35664161121`, `35664239512`, `35664519210`. Apply runs: `35663666632`, `35664117291`, `35664189404`, `35664268982`, `35664552610`. Backups: `10668605462`, `10667883639`, `10668626065`, `10667913924`, `10668966322`. The first batch hit 503 after post 56 and its rollback was unavailable; public REST showed post 56 correct and others unchanged, then the remaining posts were completed individually. A separate 403 for post 20 occurred before any write and its retry succeeded. All five final public posts retain disclosure and omit the old URLs. Source records updated; no product, Amazon link or commercial claim changed.

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
# Phase 4 kitchen gadgets release (2026-09-20)

Published the kitchen-gadgets rewrite for post 171 after manufacturer and USDA research, local tests, [dry-run 35539514318](https://github.com/HeberPython/agente-sites/actions/runs/35539514318), and [apply 35539528239](https://github.com/HeberPython/agente-sites/actions/runs/35539528239) with original-post backup. Public article and related guides returned HTTP 200. The new article removes the discontinued TOA-60 and mistaken BN701 Smart Torque claim; it compares three precise products by job without invented testing or prices. Phase 4 stands at 15/37, smart-home devices next.
# Phase 4 smart-home devices release (2026-09-20)

Published post 168 after manufacturer research, local tests, repeat [dry-run 35539810069](https://github.com/HeberPython/agente-sites/actions/runs/35539810069) and [apply 35539826998](https://github.com/HeberPython/agente-sites/actions/runs/35539826998) with original-post backup and live verification. Initial dry-run 35539742700 failed on runner network before any write. The article now distinguishes Ring subscription, ecobee wiring and Kasa Matter feature limits; no invented price or ASIN. Phase 4 stands at 16/37, with outdoor furniture kits next.

# Phase 4 outdoor-furniture release (2026-09-20)

Published post 164 after exact-model manufacturer research, local tests, [dry-run 35541625044](https://github.com/HeberPython/agente-sites/actions/runs/35541625044), and [apply 35541640533](https://github.com/HeberPython/agente-sites/actions/runs/35541640533) with original-post backup artifact `handytested-phase4-outdoor-furniture-backup`. Public article returned HTTP 200 and the release verified metadata, disclosure and links. The revised guide distinguishes the 2x4 Basics chair/table bracket kits (lumber sold separately) from Keter's preformed Solana bench, without a fixed under-$300 promise or invented testing. Phase 4 stands at 17/37, with cordless impact wrenches next.

# Phase 4 impact-wrench release (2026-09-20)

Published post 159 after manufacturer/manual research, 12 local tests, [dry-run 35543522171](https://github.com/HeberPython/agente-sites/actions/runs/35543522171), and [apply 35543543637](https://github.com/HeberPython/agente-sites/actions/runs/35543543637) with original-post backup artifact ID `10615269178`. Public metadata/content checks and independent HTTP 200 passed. Corrected the LGC120 garden-cultivator misidentification, removed invented runtime/torque and compared DCF921B, 2962-20 and P262 with final-torque safety guidance. Phase 4 stands at 18/37; projectors are next.

# Phase 4 projector release (2026-09-20)

Published post 156 after primary manufacturer research and 12 local tests. Initial [dry-run 35543915267](https://github.com/HeberPython/agente-sites/actions/runs/35543915267) passed; [apply 35543934833](https://github.com/HeberPython/agente-sites/actions/runs/35543934833) failed with HTTP 403 on the first WordPress read before backup or write. Repeat [dry-run 35543961192](https://github.com/HeberPython/agente-sites/actions/runs/35543961192) and [apply 35543972541](https://github.com/HeberPython/agente-sites/actions/runs/35543972541) passed with original-post backup artifact `10615309833`, public content/metadata checks and independent HTTP 200. The guide now separates native resolution, ANSI/ISO brightness and real streaming requirements for Yaber Pro V9, Epson CO-W01 and ViewSonic PA503S, without a fixed under-$300 promise. Phase 4 stands at 19/37; ergonomic office chairs are next.

# Phase 4 ergonomic-office-chair release (2026-09-20)

Published post 150 after manufacturer and OSHA research, 12 local tests, [dry-run 35545740963](https://github.com/HeberPython/agente-sites/actions/runs/35545740963) and [apply 35545757765](https://github.com/HeberPython/agente-sites/actions/runs/35545757765) with original-post backup artifact `10616072522`. The workflow verified public title, description, canonical, one H1, disclosure, exact-model tagged searches and two related links; independent HTTP 200 passed. Removed the unsupported Sayl under-$300 recommendation and generic variants; compared SIHOO M18, FlexiSpot OC3B and an exact HON Ignition 2.0 configuration without invented pain or productivity benefits. Phase 4 stands at 20/37; pet-owner carpet cleaners are next.

# Phase 4 pet-carpet-cleaner release (2026-09-20)

Published post 146 after manufacturer/EPA research, 12 local tests, [dry-run 35546003390](https://github.com/HeberPython/agente-sites/actions/runs/35546003390) and [apply 35546015997](https://github.com/HeberPython/agente-sites/actions/runs/35546015997) with original-post backup artifact `10616453355`. Public metadata/content and independent HTTP 200 passed. The revision distinguishes BISSELL 3353 spot cleaning, Hoover FH55000V compact extraction and BISSELL 3432 whole-room extraction; it removes a dry vacuum from the category and avoids fabricated performance, drying-time and pet-safety assurances. Phase 4 stands at 21/37; cordless nail guns are next.

# Phase 4 cordless-brad-nailer release (2026-09-20)

Published post 143 after manufacturer/manual and OSHA research, 12 local tests, [dry-run 35546209971](https://github.com/HeberPython/agente-sites/actions/runs/35546209971) and [apply 35546221316](https://github.com/HeberPython/agente-sites/actions/runs/35546221316) with original-post backup artifact `10615903508`. Public metadata/content and independent HTTP 200 passed. The guide now compares exact DEWALT DCN680B, RYOBI P321 and CRAFTSMAN CMCN618C1 packages, removes a pneumatic tool and discontinued P320, and treats brad-nailer safety without invented runtime or fixed-price promises. Phase 4 stands at 22/37; camping gear is next.

# Phase 4 car-camping release (2026-09-21)

Published post 141 after manufacturer/NPS research and 12 local tests. [Dry-run 35546444398](https://github.com/HeberPython/agente-sites/actions/runs/35546444398) passed; first [apply 35546460184](https://github.com/HeberPython/agente-sites/actions/runs/35546460184) received HTTP 403 on the first WordPress read, before backup or write. Repeat [dry-run 35546487498](https://github.com/HeberPython/agente-sites/actions/runs/35546487498) and [apply 35546505034](https://github.com/HeberPython/agente-sites/actions/runs/35546505034) passed, backup artifact `10615739044`, public metadata/content and independent HTTP 200. The corrected guide covers three exact products by task, removes the incomplete fixed-budget kit implication, and explains TETON comfort-label and stove CO risks. Phase 4 stands at 23/37; kitchen appliances are next.

# Phase 4 kitchen-appliance release (2026-09-21)

Published post 138 after manufacturer research and 12 local tests. [Dry-run 35546898756](https://github.com/HeberPython/agente-sites/actions/runs/35546898756) and [apply 35546917645](https://github.com/HeberPython/agente-sites/actions/runs/35546917645) passed with original-post backup artifact `10616449755`, public metadata/content checks and independent HTTP 200. The rewrite compares exact Instant Pot Duo Plus 6QT WhisperQuiet, Ninja BN701 and Hamilton Beach FlexBrew Trio 49916G, removes the fixed-price promise, duplicate blender and archived brewer, and makes no hands-on or direct-ASIN claim. Phase 4 stands at 24/37; smart-home security cameras are next.

# Phase 4 security-camera release (2026-09-21)

Published post 136 after Ring, Blink and Arlo primary-source research and 12 local tests. [Dry-run 35547241569](https://github.com/HeberPython/agente-sites/actions/runs/35547241569) passed; first [apply 35547264516](https://github.com/HeberPython/agente-sites/actions/runs/35547264516) failed with network unreachable on the initial WordPress read, before backup or write. Repeat [dry-run 35547338374](https://github.com/HeberPython/agente-sites/actions/runs/35547338374) and [apply 35547356902](https://github.com/HeberPython/agente-sites/actions/runs/35547356902) passed, backup artifact `10617260543`, public metadata/content checks and independent HTTP 200. Revised copy explains paid recording, Blink module/local-storage requirements, Arlo generation and privacy without a fixed price or untested safety assurance. Phase 4 stands at 25/37; home DIY tool sets are next.

# Phase 4 home-tool-set release (2026-09-21)

Published post 90 after manufacturer research and 12 local tests. [Dry-run 35614956018](https://github.com/HeberPython/agente-sites/actions/runs/35614956018) and [apply 35614990780](https://github.com/HeberPython/agente-sites/actions/runs/35614990780) passed with original-post backup artifact `10645916262`, public metadata/content checks and independent HTTP 200. The rewrite compares BLACK+DECKER BDPK70284C1AEV, DEWALT DCK240C2 and CRAFTSMAN CMMT45306 by project type, removing fabricated hands-on tests, ratings, runtime, generic variants and fixed price ranges. Phase 4 stands at 26/37; smart TVs are next.

# Phase 4 smart-TV release (2026-09-21)

Published post 78 after Amazon, Hisense and Roku primary-source research and 12 local tests. [Dry-run 35619627634](https://github.com/HeberPython/agente-sites/actions/runs/35619627634) and [apply 35619680160](https://github.com/HeberPython/agente-sites/actions/runs/35619680160) passed with original-post backup artifact `10647178474`, public metadata/content checks and independent HTTP 200. The rewrite compares exact Amazon Fire TV 4-Series 4K50N402, Hisense 50A6N and Roku Select Series 50R4C5 models by platform and inputs, removing stale products, fabricated tests, ratings, fixed prices and unsupported gaming assurances. Phase 4 stands at 27/37; noise-canceling headphones are next.

# Phase 4 ANC-headphones release (2026-09-21)

Published post 72 after Sony, Bose and soundcore primary-source research and 12 local tests. Initial [dry-run 35623685309](https://github.com/HeberPython/agente-sites/actions/runs/35623685309) passed; first [apply 35623750726](https://github.com/HeberPython/agente-sites/actions/runs/35623750726) received HTTP 403 on the initial WordPress read before backup or write. Repeat [dry-run 35623819822](https://github.com/HeberPython/agente-sites/actions/runs/35623819822) and [apply 35623876339](https://github.com/HeberPython/agente-sites/actions/runs/35623876339) passed with backup artifact `10651035244`, public metadata/content checks and independent HTTP 200. The rewrite compares Sony WH-1000XM6, Bose QuietComfort Headphones and soundcore Space One Pro A3062 without invented listening tests, ratings, fixed prices or unqualified battery claims. Phase 4 stands at 28/37; laser levels are next.

# Phase 4 laser-level release (2026-09-21)

Published post 31 after Bosch, DEWALT and BLACK+DECKER primary-source research and 12 local tests. Initial [dry-run 35627963754](https://github.com/HeberPython/agente-sites/actions/runs/35627963754) passed; first [apply 35628018668](https://github.com/HeberPython/agente-sites/actions/runs/35628018668) received HTTP 403 on the initial WordPress read before backup or write. Repeat [dry-run 35628091696](https://github.com/HeberPython/agente-sites/actions/runs/35628091696) and [apply 35628150257](https://github.com/HeberPython/agente-sites/actions/runs/35628150257) passed with backup artifact `10652824486`, public metadata/content checks and independent HTTP 200. The rewrite separates Bosch GLL50-20, DEWALT DW088CG and BLACK+DECKER BDL220S by actual layout role without fabricated tests, ratings, fixed prices or conflated detector range. Phase 4 stands at 29/37; oscillating multi-tools are next.

# Phase 4 oscillating multi-tool release (2026-09-21)

Published post 28 after DEWALT, BLACK+DECKER and WEN primary-source research and 12 local tests. [Dry-run 35632830657](https://github.com/HeberPython/agente-sites/actions/runs/35632830657) and [apply 35632974267](https://github.com/HeberPython/agente-sites/actions/runs/35632974267) passed with original-post backup artifact `10654957209`, public metadata/content checks and independent HTTP 200. The rewrite compares DCS356B, BD200MTB and WEN 2312 by power source and package, removing fabricated hands-on testing, ratings, fixed prices and stale or misidentified models. Phase 4 stands at 30/37; cordless ratchets are next.

# Phase 4 cordless-ratchet release (2026-09-21)

Published post 84 after DEWALT, Milwaukee and CRAFTSMAN primary-source research and 12 local tests. [Dry-run 35634004487](https://github.com/HeberPython/agente-sites/actions/runs/35634004487) and [apply 35634133101](https://github.com/HeberPython/agente-sites/actions/runs/35634133101) passed with original-post backup artifact `10655742537`, public metadata/content checks and independent HTTP 200. The rewrite compares DCF513B, 2457-21 and CMCF930B by actual battery platform and package, removing generic models, unsupported Sunex 4970, ratings, fixed prices and unverified durability claims. Phase 4 stands at 31/37; electric screwdrivers are next.

# Phase 4 electric-screwdriver release (2026-09-21)

Published post 81 after SKIL, BLACK+DECKER and WORX primary-source research and 12 local tests. [Dry-run 35638198516](https://github.com/HeberPython/agente-sites/actions/runs/35638198516) and [apply 35638300625](https://github.com/HeberPython/agente-sites/actions/runs/35638300625) passed with original-post backup artifact `10657530788`, public metadata/content checks and independent HTTP 200. The rewrite compares exact 4V screwdrivers by control, charging and package, removes drill/drivers, ratings and fixed prices, and states that SKIL's circuit sensor does not prove de-energization. Phase 4 stands at 32/37; digital torque wrenches are next.

# Phase 4 digital-torque-wrench release (2026-09-21)

Published post 62 after GEARWRENCH, ACDelco and CRAFTSMAN primary-source research and 12 local tests. Initial [dry-run 35639356323](https://github.com/HeberPython/agente-sites/actions/runs/35639356323) received HTTP 403 on the initial WordPress read before backup or write. Repeat [dry-run 35639422114](https://github.com/HeberPython/agente-sites/actions/runs/35639422114) and [apply 35639478118](https://github.com/HeberPython/agente-sites/actions/runs/35639478118) passed with original-post backup artifact `10657009494`, public metadata/content checks and independent HTTP 200. The rewrite compares 85076, ARM601-3 and CMMT99435 by range, accuracy conditions and alerts, removing generic models, ratings, fixed prices and the unsupported five-under-$100 framing. Phase 4 stands at 33/37; cordless circular saws are next.

# Phase 4 cordless-circular-saw release (2026-09-21)

Published post 59 after DEWALT, SKIL, Makita and manufacturer-manual research and 12 local tests. [Dry-run 35644507631](https://github.com/HeberPython/agente-sites/actions/runs/35644507631) and [apply 35644560930](https://github.com/HeberPython/agente-sites/actions/runs/35644560930) passed with original-post backup artifact `10660230583`, public metadata/content checks and independent HTTP 200. The rewrite compares DCS565B, CR6413B-11 and XSS02Z by package, platform and blade capacity, removing fixed prices, ratings, mixed package assumptions and the unsupported under-$150 promise. Phase 4 stands at 34/37; rotary tools are next.

# Phase 4 rotary-tool release (2026-09-21)

Published post 47 after Dremel and WEN primary-source research and 12 local tests. [Dry-run 35645629734](https://github.com/HeberPython/agente-sites/actions/runs/35645629734) and [apply 35645682838](https://github.com/HeberPython/agente-sites/actions/runs/35645682838) passed with original-post backup artifact `10659883475`, public metadata/content checks and independent HTTP 200. The rewrite compares Dremel 3000-1/25, WEN 2305 and Dremel Stylo+ 2050-15 by workload and package, removes fabricated hands-on testing, ratings, fixed prices and unsupported WEN figures, and discloses the Dremel 3000 source/version speed discrepancy. Phase 4 stands at 35/37; stud finders are next.

# Phase 4 stud-finder release (2026-09-21)

Published post 44 after Franklin, Zircon and CRAFTSMAN primary-source research and 12 local tests. Initial [dry-run 35649804562](https://github.com/HeberPython/agente-sites/actions/runs/35649804562) passed; first [apply 35649863861](https://github.com/HeberPython/agente-sites/actions/runs/35649863861) failed from runner network unavailability on the initial WordPress read, before any backup/write. Repeat [dry-run 35650031295](https://github.com/HeberPython/agente-sites/actions/runs/35650031295) and [apply 35650069460](https://github.com/HeberPython/agente-sites/actions/runs/35650069460) passed with original-post backup artifact `10661213547`, public metadata/content checks and independent HTTP 200. The rewrite compares M90, e50 and CMHT77621 without fabricated testing, ratings, fixed prices or unwarranted wiring-clearance assurances. Phase 4 stands at 36/37; cordless drills are next.

# Phase 4 cordless-drill release and editorial completion (2026-09-21)

Published post 20 after DEWALT, BLACK+DECKER and CRAFTSMAN primary-source research and 12 local tests. [Dry-run 35650671679](https://github.com/HeberPython/agente-sites/actions/runs/35650671679) and [apply 35650720386](https://github.com/HeberPython/agente-sites/actions/runs/35650720386) passed with original-post backup artifact `10661564235`, public metadata/content checks and independent HTTP 200. The rewrite distinguishes exact kits, removes fixed-price, durability and runtime assertions, and notes the conflicting CRAFTSMAN battery-capacity text. Phase 4 editorial queue is complete at 37/37; image rights, verified direct Amazon links and other cross-cutting items remain separate.
