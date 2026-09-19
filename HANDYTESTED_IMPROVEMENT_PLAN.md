# HandyTested improvement plan

Baseline and evidence: [HANDYTESTED_AUDIT.md](HANDYTESTED_AUDIT.md). Preserve existing slugs, taxonomy IDs, Amazon tag `handytested0d-20`, AdSense/GTM integration and published posts unless a reviewed edit is ready. Work in small batches with WordPress revision/backup before writes. Publish only after editorial verification.

| Phase | Work and acceptance gate |
|---|---|
| 1. Critical fixes | Keep AI-generated HandyTested articles in draft; reject first-hand claims in generated HTML. Review all 33 flagged posts paragraph by paragraph, checking measurements, product identity, price and ratings against sources. Correct the most serious product/category errors first. Verify Rank Math sitemap includes all indexable posts. |
| 2. Design system | Introduce shared WordPress styles for typography, spacing, contrast, comparison tables, badges and Amazon CTAs. Test at 320, 375, 768, 1280 and 1920px. Keep Astra template ownership clear. |
| 3. Homepage | Replace static content snapshot with a maintained or dynamic post query. Brand-first headline, top guides, honest deals, categories, comparisons, learning content and methodology. No prices or discounts without a current approved source. |
| 4. Article template | One H1 from theme, short intro, quick picks, responsive comparison, research criteria, buyer fit/tradeoffs, FAQ, related guides, clear disclosure. Remove unsupported lab language. |
| 5. Categories | Keep existing category slugs. Add original introductions and useful guide groupings where inventory warrants it. Avoid empty pages for Compare/Learn/Deals until real articles exist. |
| 6. SEO | Audit every canonical, meta, schema, headings, alt, redirect and sitemap entry. Fix demo page exposure after checking OAuth callback. Refresh dated titles only after re-research; keep slug and canonical stable. Do not manufacture Product/Review ratings or prices in schema. |
| 7. Internal linking | Build manual clusters from current posts: tools/cordless, electrical measurement, smart home and paint. Add a small number of contextual links in both directions after checking relevance. |
| 8. Performance | Measure field and lab LCP/CLS/INP on mobile and desktop. Prioritize image dimensions, compression, font loading and third-party script impact. Retest AdSense revenue/placements before changing ad loading. |
| 9. CRO and affiliate | Verify each model and ASIN on Amazon.com, then create a curated direct-link catalog from SiteStripe. Replace model-specific search CTAs gradually, keep tracking tag, and test destinations. Use “View on Amazon” or “Check Current Price”; no claimed lowest price. |
| 10. Future growth | Add accurate Compare/Learn articles and tools aligned with published clusters. Start with Paint Coverage Calculator and Battery Runtime Calculator, then Torque Converter. Review electrical tools for safety implications before release. |

## First implementation slice

Completed: read-only public inventory; generator language and disclosure tightened; new HandyTested posts default to draft; scheduled promo posts default to draft; portal source avoids duplicate page H1s. The narrow workflow was run, and the five existing trust pages now have one H1. Existing 38 published articles remain unchanged until separately reviewed.

## Editorial review sequence

1. Prioritize content with concrete first-hand numbers: heat guns, multimeters, smart-home hubs, wireless earbuds, paint sprayers, drill presses, sanders and voltage testers. Check every claimed test, measurement, model and URL.
2. For each article, record source URL/date, supported specs, product status, pricing basis, image rights and approved Amazon link. Remove unsupported claims or write a fresh comparison grounded in cited sources.
3. Revisit 24 dated titles. Choose evergreen title only when product lineup remains valid; retain existing slug and update title/meta/body consistently. Use WordPress revisions for rollback.
4. Verify indexation and analytics after each batch. Do not mass replace a year, price, rating or ASIN.

## Release gates

- `python -m py_compile` on changed scripts, workflow YAML parse, `git diff --check`.
- Dry run of the public inventory and validation of generated article drafts before any publication workflow is re-enabled.
- WordPress backup and before/after URL checks for each live page edit.
- Screenshots on 320px and desktop for homepage, one article, category and demo/OAuth flow.
- Search Console sitemap resubmission and follow-up crawl after correcting sitemap generation.
