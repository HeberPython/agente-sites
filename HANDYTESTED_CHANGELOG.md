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
