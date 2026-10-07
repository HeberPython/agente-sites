#!/usr/bin/env python3

import json
import os
import sys
from datetime import date, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)

SITE_URL = "https://handytested.com/"
GA4_PROPERTY_ID = "539335231"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]


def get_credentials():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not raw:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON nao foi encontrado."
        )

    info = json.loads(raw)

    return service_account.Credentials.from_service_account_info(
        info,
        scopes=SCOPES,
    )


def test_search_console(credentials):
    end_date = date.today() - timedelta(days=3)
    start_date = end_date - timedelta(days=27)

    service = build(
        "searchconsole",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    request = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query", "page"],
        "rowLimit": 10,
        "dataState": "final",
    }

    response = (
        service.searchanalytics()
        .query(siteUrl=SITE_URL, body=request)
        .execute()
    )

    rows = response.get("rows", [])

    print(
        f"GSC_OK periodo={start_date}..{end_date} "
        f"linhas={len(rows)}"
    )

    for row in rows:
        keys = row.get("keys", ["", ""])

        print(
            "GSC_ROW",
            json.dumps(
                {
                    "query": keys[0],
                    "page": keys[1],
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": row.get("ctr", 0),
                    "position": row.get("position", 0),
                },
                ensure_ascii=False,
            ),
        )


def test_ga4(credentials):
    client = BetaAnalyticsDataClient(
        credentials=credentials
    )

    request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        dimensions=[
            Dimension(name="eventName"),
        ],
        metrics=[
            Metric(name="eventCount"),
        ],
        date_ranges=[
            DateRange(
                start_date="28daysAgo",
                end_date="today",
            )
        ],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.EXACT,
                    value="affiliate_click",
                ),
            )
        ),
    )

    response = client.run_report(request)

    total = 0

    for row in response.rows:
        count = int(row.metric_values[0].value or 0)
        total += count

        print(
            "GA4_ROW",
            json.dumps(
                {
                    "event": row.dimension_values[0].value,
                    "eventCount": count,
                }
            ),
        )

    print(
        f"GA4_OK affiliate_click_28d={total}"
    )


def main():
    credentials = get_credentials()

    errors = []

    try:
        test_search_console(credentials)
    except Exception as exc:
        errors.append(
            f"GSC_ERROR {type(exc).__name__}: {exc}"
        )

    try:
        test_ga4(credentials)
    except Exception as exc:
        errors.append(
            f"GA4_ERROR {type(exc).__name__}: {exc}"
        )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)

        return 1

    print("REVENUE_INTELLIGENCE_PROBE_OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
