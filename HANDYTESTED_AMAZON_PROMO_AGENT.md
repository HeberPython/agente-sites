# HandyTested Amazon Promo Agent

This agent turns Amazon Associates promo emails sent to
`promoassociados@handytested.com` into HandyTested editorial drafts.

## What It Does

1. Reads unread emails from `promoassociados@handytested.com` by IMAP.
2. Extracts the campaign theme, product categories, buyer angle, and useful links.
3. Converts the promotion into an English HandyTested buying guide/review article.
4. Uses Amazon.com affiliate search links with tag `amazonrev089f-20`.
5. Publishes to WordPress as `draft` by default.
6. Marks the email as seen only after processing.
7. Sends a Telegram summary when it creates posts.

## Required GitHub Secrets

- `OPENAI_API_KEY`
- `HT_WP_PASS`
- `PROMO_EMAIL_PASS`

Optional:

- `OPENAI_MODEL`
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`

## Workflow

Workflow file:

`.github/workflows/handytested-amazon-promos.yml`

Schedule:

Daily at 10:30 America/Sao_Paulo. It only acts on unread promo emails, so daily
runs are safer than waiting a full week and missing time-sensitive campaigns.

Manual run:

Use GitHub Actions > HandyTested Amazon Promo Agent > Run workflow. Keep
`post_status` as `draft` while calibrating. Change to `publish` only after the
draft quality is consistently good.

## Editorial Rules

- Never copy Amazon email text directly.
- Never reuse Amazon promo images from the email.
- Do not mention exact prices or discount percentages unless supplied live by
  Amazon tooling.
- Keep the affiliate disclosure at the top.
- Use `rel="nofollow sponsored noopener"` on Amazon links.
- Default to Amazon.com because HandyTested targets US buyers.

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
