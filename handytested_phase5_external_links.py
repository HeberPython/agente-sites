"""Read-only check of public non-Amazon citations in current articles."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urldefrag
from urllib.request import Request, urlopen


BASE = "https://handytested.com"
OUTPUT = Path("handytested-phase5-external-links.json")


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.urls.append(href)


def read_json(url: str) -> object:
    with urlopen(Request(url, headers={"User-Agent": "HandyTested citation check"}), timeout=25) as response:
        return json.load(response)


def check(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; HandyTestedCitationAudit/1.0)"})
    try:
        with urlopen(request, timeout=12) as response:
            response.read(256)
            return {"status": response.status, "final_url": response.geturl()}
    except HTTPError as exc:
        return {"status": exc.code, "final_url": exc.geturl()}
    except (URLError, TimeoutError, ValueError) as exc:
        return {"error": type(exc).__name__}


def main() -> None:
    posts = read_json(BASE + "/wp-json/wp/v2/posts?per_page=100&_fields=link,content")
    sources: dict[str, list[str]] = {}
    for post in posts:
        links = Links()
        links.feed(post["content"]["rendered"])
        for href in links.urls:
            url = urldefrag(href).url
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if parsed.scheme not in {"http", "https"} or host in {"handytested.com", "www.handytested.com"} or host.endswith("amazon.com"):
                continue
            sources.setdefault(url, []).append(post["link"])
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(check, url): url for url in sources}
        for job in as_completed(jobs):
            url = jobs[job]
            results.append({"url": url, "sources": sorted(set(sources[url])), **job.result()})
    results.sort(key=lambda row: row["url"])
    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    counts: dict[str, int] = {}
    for row in results:
        code = str(row.get("status", row.get("error", "unknown")))
        counts[code] = counts.get(code, 0) + 1
    print(json.dumps({"articles": len(posts), "citations": len(results), "statuses": counts}, sort_keys=True))
    for row in results:
        if row.get("status") in {404, 410}:
            print(json.dumps({"candidate_broken": row["url"], "status": row["status"], "source": row["sources"][0]}))
    print("403, 429 and network failures are inconclusive, not proof of a broken citation.")


if __name__ == "__main__":
    main()
