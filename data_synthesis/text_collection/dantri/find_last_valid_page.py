from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TIMELINE_ARTICLE_PATTERN = re.compile(
    r'<article[^>]+data-content-name="category-timeline_page_(\d+)"',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SearchResult:
    last_valid_page: int
    last_valid_url: str


def build_page_url(category_url: str, from_date: str, to_date: str, page_index: int) -> str:
    category = category_url.rstrip("/")
    return f"{category}/from/{from_date}/to/{to_date}/trang-{page_index}.htm"


def fetch_html(url: str, timeout: int = 15) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DanTriPageChecker/1.0",
            "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def has_timeline_articles(html: str, page_index: int) -> bool:
    matches = TIMELINE_ARTICLE_PATTERN.findall(html)
    return str(page_index) in matches


def is_valid_page(
    category_url: str,
    from_date: str,
    to_date: str,
    page_index: int,
    cache: Dict[int, bool],
    timeout: int = 15,
) -> bool:
    if page_index in cache:
        return cache[page_index]

    url = build_page_url(category_url, from_date, to_date, page_index)
    try:
        html = fetch_html(url, timeout=timeout)
        valid = has_timeline_articles(html, page_index)
    except (HTTPError, URLError, TimeoutError):
        valid = False

    cache[page_index] = valid
    return valid


def find_last_valid_page(
    category_url: str,
    from_date: str,
    to_date: str,
    max_page: int = 4096,
    timeout: int = 15,
) -> SearchResult:
    cache: Dict[int, bool] = {}

    if not is_valid_page(category_url, from_date, to_date, 1, cache=cache, timeout=timeout):
        raise ValueError("Trang 1 không hợp lệ cho date range/category đã cho.")

    low = 1
    high = 2

    while high <= max_page and is_valid_page(
        category_url, from_date, to_date, high, cache=cache, timeout=timeout
    ):
        low = high
        high *= 2

    if high > max_page:
        high = max_page + 1

    answer = low
    left = low + 1
    right = high - 1

    while left <= right:
        mid = (left + right) // 2
        if is_valid_page(category_url, from_date, to_date, mid, cache=cache, timeout=timeout):
            answer = mid
            left = mid + 1
        else:
            right = mid - 1

    return SearchResult(
        last_valid_page=answer,
        last_valid_url=build_page_url(category_url, from_date, to_date, answer),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tìm trang index cuối hợp lệ của category Dantri theo date range."
    )
    parser.add_argument(
        "--category-url",
        required=True,
        help="Ví dụ: https://dantri.com.vn/the-gioi",
    )
    parser.add_argument("--from-date", required=True, help="Định dạng YYYY-MM-DD")
    parser.add_argument("--to-date", required=True, help="Định dạng YYYY-MM-DD")
    parser.add_argument("--max-page", type=int, default=4096)
    parser.add_argument("--timeout", type=int, default=15)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = find_last_valid_page(
        category_url=args.category_url,
        from_date=args.from_date,
        to_date=args.to_date,
        max_page=args.max_page,
        timeout=args.timeout,
    )
    print(f"last_valid_page={result.last_valid_page}")
    print(f"last_valid_url={result.last_valid_url}")


if __name__ == "__main__":
    main()

# py -3 data_synthesis\text_collection\dantri\find_last_valid_page.py --category-url https://dantri.com.vn/the-gioi --from-date 2026-04-01 --to-date 2026-04-19