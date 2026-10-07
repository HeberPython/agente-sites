# HandyTested Revenue Intelligence

Status: Phase 1 architecture approved
Date: 2026-10-07

## Mission
Replace the decision-support functions currently supplied by GSC Wizard with a HandyTested-owned, revenue-first data layer. The system must optimize for qualified US Amazon affiliate traffic and commissions, not raw pageviews or article count.

## Decision chain
Search demand -> query/page opportunity -> HandyTested visit -> affiliate_click -> Amazon -> commission signal.

## Data sources

### Google Search Console API
Collect settled search-performance data for handytested.com:
- date
- query
- page
- country
- device
- clicks
- impressions
- CTR
- average position

Primary filters: United States + commercial/buyer-intent queries.

### Google Analytics Data API (GA4)
Property: 539335231
Collect:
- landing page
- page path
- source/medium and default channel group
- country/device
- sessions/users
- outbound_link_click
- affiliate_click

`affiliate_click` is a micro-conversion only. It MUST NOT be reported as an Amazon sale or commission.

### Bing Webmaster REST API
Collect:
- rank/traffic stats
- keyword/query details
- page details
- crawl/indexing signals where useful

Prefer REST. Do not build new dependencies on retired legacy SOAP/POX interfaces.

### WordPress / HandyTested
Join search opportunities to existing published articles, categories, and affiliate-link coverage. Never create or publish an article solely because a keyword exists.

### Amazon Associates
Amazon remains the authority for ordered items, shipped items and commissions. Search/GA data cannot infer a sale.

## Storage
Persist raw snapshots so HandyTested owns its history beyond upstream retention windows.

Proposed repository-independent schema:
- gsc_daily
- gsc_query_page_daily
- ga4_page_daily
- ga4_affiliate_click_daily
- bing_query_daily
- opportunity_scores
- ingestion_runs

Do not commit OAuth tokens, service-account JSON, API keys, refresh tokens, passwords, or other secrets to GitHub. Runtime credentials belong in GitHub Actions Secrets or another secret store.

## Opportunity scoring
The Opportunity Radar should prioritize:
1. US buyer intent.
2. Existing pages in striking distance (especially positions 5-20).
3. Meaningful impressions/demand trend.
4. CTR gap relative to position and intent.
5. Evidence of affiliate clicks when traffic exists.
6. Real Amazon product coverage and commercial fit.
7. Low cannibalization risk.

Possible actions:
- OPTIMIZE_EXISTING
- CREATE_NEW_CONTENT
- IMPROVE_AFFILIATE_PATH
- WATCH
- IGNORE

A new article requires a production gate: demand evidence + commercial SERP + multiple real products + differentiation from existing content + likely affiliate value + low cannibalization.

## Paint-sprayer control cluster
Track price bands $100, $150, $200, $250, $300, $400, $500, $600 plus relevant HVLP, airless, cabinet, furniture and DIY variants. The existing $300 cluster is the control because HandyTested already has Google evidence for it.

## Automation cadence
- Daily: collect settled source data and append/upsert snapshots.
- Weekly Friday: Opportunity Radar evaluates material changes.
- Notify only on a materially new/high-confidence commercial opportunity.
- Revenue Agent automatic publishing remains gated/manual until an opportunity passes the production gate.

## Phase plan
Phase 1: architecture + safe collectors + local validation.
Phase 2: configure Google credentials and validate GSC + GA4 reads.
Phase 3: configure/validate Bing REST access.
Phase 4: persistent storage and historical backfill where available.
Phase 5: revenue scoring, weekly report, and Opportunity Radar integration.
Phase 6: optional Amazon reporting integration if a supported, compliant data source becomes available.

## Security rules
- Read-only scopes by default.
- Least privilege.
- No credentials in source control or logs.
- No synthetic affiliate clicks, self-purchases, simulated conversions or artificial traffic.
- No unsupported claims that an Amazon purchase occurred.

## Immediate credential requirements
Google: a Google Cloud project with Search Console API and Google Analytics Data API enabled, then authentication that has read access to the HandyTested GSC property and GA4 property 539335231. Service-account or user OAuth authentication can be used where appropriate.

Bing: API access can use OAuth 2.0 (preferred for delegated access) or an API key. The existing GSC Wizard Bing key must not be assumed retrievable from GSC Wizard; configure a HandyTested-owned credential separately when Phase 3 begins.
