from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_urls(xml_path: Path) -> list[str]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []

    for loc in root.findall("sm:url/sm:loc", namespace):
        if loc.text:
            urls.append(loc.text.strip())

    return urls


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract all URLs from a sitemap XML file.")
    parser.add_argument(
        "xml_file",
        nargs="?",
        help="Path to the XML file.",
    )
    parser.add_argument(
        "--xml-file",
        dest="xml_file_flag",
        help="Path to the XML file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output text file. If omitted, URLs are printed to stdout.",
    )
    args = parser.parse_args()

    xml_file = args.xml_file_flag or args.xml_file or "Article-2026-01-01.xml"
    xml_path = Path(xml_file)
    if not xml_path.is_absolute():
        xml_path = Path.cwd() / xml_path

    if not xml_path.exists():
        print(f"File not found: {xml_path}", file=sys.stderr)
        return 1

    try:
        urls = extract_urls(xml_path)
    except ET.ParseError as exc:
        print(f"XML parse error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path.write_text("\n".join(urls), encoding="utf-8")
        print(f"Extracted {len(urls)} URLs to {output_path}")
        return 0

    for url in urls:
        print(url)

    print(f"Total URLs: {len(urls)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
