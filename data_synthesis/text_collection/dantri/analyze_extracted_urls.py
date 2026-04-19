from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_INPUT_DIR = "extracted_urls"


@dataclass
class AnalysisResult:
    input_dir: str
    file_count: int
    total_urls: int
    unique_urls: int
    duplicate_urls: int
    urls_per_file: dict[str, int]
    urls_per_sitemap_month: dict[str, int]
    category_counts: dict[str, int]
    top_files: list[dict[str, int | str]]
    top_categories: list[dict[str, int | str]]


def read_urls_from_txt(file_path: Path) -> list[str]:
    return [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def extract_category(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "root"
    parts = path.split("/")
    return parts[0] if parts[0] else "root"


def analyze_directory(input_dir: Path, top_n: int) -> AnalysisResult:
    txt_files = sorted(input_dir.glob("Article-*.txt"))

    urls_per_file: dict[str, int] = {}
    sitemap_month_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    all_urls: list[str] = []

    for txt_file in txt_files:
        urls = read_urls_from_txt(txt_file)
        urls_per_file[txt_file.name] = len(urls)
        sitemap_month_counter[txt_file.stem] = len(urls)
        all_urls.extend(urls)

        for url in urls:
            category_counter[extract_category(url)] += 1

    total_urls = len(all_urls)
    unique_urls = len(set(all_urls))
    duplicate_urls = total_urls - unique_urls

    top_files = [
        {"file": file_name, "count": count}
        for file_name, count in sorted(urls_per_file.items(), key=lambda item: item[1], reverse=True)[:top_n]
    ]
    top_categories = [
        {"category": category, "count": count}
        for category, count in category_counter.most_common(top_n)
    ]

    return AnalysisResult(
        input_dir=str(input_dir),
        file_count=len(txt_files),
        total_urls=total_urls,
        unique_urls=unique_urls,
        duplicate_urls=duplicate_urls,
        urls_per_file=urls_per_file,
        urls_per_sitemap_month=dict(sitemap_month_counter),
        category_counts=dict(category_counter),
        top_files=top_files,
        top_categories=top_categories,
    )


def print_summary(result: AnalysisResult, top_n: int) -> None:
    print(f"Input directory     : {result.input_dir}")
    print(f"Sitemap txt files   : {result.file_count}")
    print(f"Total URLs          : {result.total_urls}")
    print(f"Unique URLs         : {result.unique_urls}")
    print(f"Duplicate URLs      : {result.duplicate_urls}")
    print()

    print(f"Top {top_n} sitemap files by URL count:")
    for item in result.top_files:
        print(f"  {item['file']}: {item['count']}")
    print()

    print(f"Top {top_n} categories:")
    for item in result.top_categories:
        print(f"  {item['category']}: {item['count']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze extracted Dantri URL text files.")
    parser.add_argument(
        "input_dir",
        nargs="?",
        default=DEFAULT_INPUT_DIR,
        help="Directory containing extracted Article-*.txt files.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top items to show in the summary.",
    )
    parser.add_argument(
        "--json-output",
        help="Optional path to save the full analysis result as JSON.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_absolute():
        input_dir = Path.cwd() / input_dir

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    result = analyze_directory(input_dir, args.top)
    print_summary(result, args.top)

    if args.json_output:
        json_output = Path(args.json_output)
        if not json_output.is_absolute():
            json_output = Path.cwd() / json_output
        json_output.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print(f"Saved JSON analysis to: {json_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
