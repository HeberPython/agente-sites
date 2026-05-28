# HandyTested Portal Upgrade

HandyTested is being shaped as a review portal, not just a chronological blog.
The model is closer to BestReviews: category hubs, trust pages, deal guidance,
and stricter automation rules.

## WordPress Structure

Pages created or updated:

- `/` - portal-style home page
- `/deals/` - Amazon deal guidance page
- `/how-we-review/` - review methodology
- `/editorial-policy/` - editorial standards
- `/affiliate-disclosure/` - affiliate transparency
- `/about/` - updated site positioning

Categories:

- `electronics`
- `tools`
- `diy`
- `smart-home`
- `kitchen`
- `outdoor`
- `cleaning`
- `office-gear`
- `amazon-deals`

Operational tags:

- `evergreen`
- `pinterest-safe`
- `review-guide`
- `deal`
- `promo-email`
- `seasonal`

## Automation Rules

### HandyTested PRO

The evergreen review agent now:

- ensures categories and review tags exist
- can publish into broader BestReviews-style categories
- uses a stronger review structure: quick verdict, comparison table, top picks,
  evaluation criteria, pros/cons, buying guide, and FAQ
- avoids fake hands-on claims unless testing is verified
- avoids fixed prices and live discount claims
- tags evergreen reviews with `evergreen`, `pinterest-safe`, and `review-guide`

### Amazon Promo Agent

The promo email agent now:

- assigns promo posts to `amazon-deals` plus the relevant buyer category
- tags promo posts with `deal` and `promo-email`
- adds `seasonal` when the campaign has a deadline
- stores an invisible expiration marker in time-sensitive posts
- moves expired published posts back to `draft`

### Pinterest and Reddit

The social agents now:

- skips posts tagged `deal`, `promo-email`, or `seasonal`
- fetch extra recent posts so they can still find evergreen content to share
- support the expanded category set with dedicated Pinterest boards and
  subreddit mappings where possible

This keeps social distribution focused on durable review content instead of
short-lived Amazon campaigns.

## API Impact

- Amazon: no new PA API dependency. Links still use the affiliate tag
  `amazonrev089f-20`. The scripts still avoid fixed prices and Amazon images.
- Pinterest: safer because seasonal posts are excluded.
- Google/Search/AdSense: stronger trust pages, clearer site architecture, and
  reduced stale-promo risk.
- WordPress REST API: used for idempotent setup, pages, categories, tags, and
  post publishing.

## Setup Script

Run only when structure needs to be recreated or updated:

```powershell
$env:HT_WP_PASS="..."
python .\setup_handytested_portal.py
```

The script is idempotent and updates existing pages/terms instead of duplicating
them.
