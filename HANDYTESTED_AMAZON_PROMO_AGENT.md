# HandyTested Amazon Promo Agent

This agent turns Amazon Associates promo emails sent or forwarded to
`promoassociados@handytested.com` into HandyTested editorial drafts.

## What It Does

1. Reads unread emails from `promoassociados@handytested.com` by IMAP.
2. Extracts the campaign theme, product categories, buyer angle, and useful links.
3. Converts the promotion into an English HandyTested buying guide/review article.
4. Uses Amazon.com affiliate search links with tag `amazonrev089f-20`.
5. Assigns the post to `Amazon Deals` plus the relevant buyer category.
6. Publishes to WordPress as `draft` by default.
7. Detects whether the campaign is seasonal/time-sensitive and stores an
   internal expiration marker in the post.
8. Moves expired published promo posts back to `draft` automatically.
9. Marks the email as seen only after processing.
10. Sends a Telegram summary when it creates or expires posts.

## Required GitHub Secrets

- `OPENAI_API_KEY`
- `HT_WP_PASS`
- `PROMO_EMAIL_PASS`

Optional:

- `OPENAI_MODEL`
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`
- `PROMO_DEFAULT_EXPIRATION_DAYS`
- `PROMO_EXPIRE_PUBLISHED_POSTS`

## Workflow

Workflow file:

`.github/workflows/handytested-amazon-promos.yml`

Schedule:

Daily at 10:30 America/Sao_Paulo. It only acts on unread promo emails, so daily
runs are safer than waiting a full week and missing time-sensitive campaigns.
It also checks for expired promotional posts on every run, even when there are
no new emails.

## Email Intake

The current intake flow is manual forwarding:

1. Amazon sends a promo/campaign email to the main inbox.
2. Forward only the useful Associates promo emails to
   `promoassociados@handytested.com`.
3. Leave the forwarded email unread in that mailbox.
4. The agent reads the forwarded content, including the original Amazon email
   text and links, then creates a HandyTested draft.

This is safer than giving the agent access to a personal inbox because it only
sees the curated promotion emails that should become content.

Manual run:

Use GitHub Actions > HandyTested Amazon Promo Agent > Run workflow. Keep
`post_status` as `draft` while calibrating. Change to `publish` only after the
draft quality is consistently good.

## Editorial Rules

- Never copy Amazon email text directly.
- Never reuse Amazon promo images from the email.
- Do not mention exact prices or discount percentages unless supplied live by
  Amazon tooling.
- Treat seasonal Amazon campaigns as editorial signals first. Prefer evergreen
  buyer-guidance titles instead of date-heavy promo titles.
- Tag promo posts with `deal` and `promo-email`; add `seasonal` when the
  campaign has a deadline. Pinterest ignores these tags.
- Detect explicit campaign deadlines. If a campaign has an end date, the agent
  stores an internal expiration marker and can move the post back to draft after
  the promo ends.
- If a campaign is clearly temporary but no end date is explicit, the default
  expiration window is 21 days unless `PROMO_DEFAULT_EXPIRATION_DAYS` overrides it.
- Keep the affiliate disclosure at the top.
- Use `rel="nofollow sponsored noopener"` on Amazon links.
- Default to Amazon.com because HandyTested targets US buyers.

## Expiration Behavior

Time-sensitive posts receive an invisible HTML comment like:

```html
<!-- handytested-promo-agent: {"expires_on":"2026-06-08", ...} -->
```

On each run, the agent fetches published posts, finds that marker, and changes
expired posts to `draft`. This removes stale campaign pages from the public blog
without deleting the content.

## Local Test With A Saved Email

Save an `.eml` or `.txt` email, then run:

```powershell
$env:OPENAI_API_KEY="..."
$env:HT_WP_PASS="..."
$env:PROMO_EMAIL_PASS="not-used-for-sample"
$env:PROMO_SAMPLE_EMAIL_FILE="C:\path\to\sample.eml"
$env:PROMO_POST_STATUS="draft"
python .\handytested_amazon_promo_agent.py
```

The sample mode skips IMAP and does not mark any real email as seen.
