from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

SITEMAP_NAMESPACE = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
DEFAULT_INDEX_FILE = "articles.xml"


def parse_sitemap_index(index_path: Path) -> list[str]:
    tree = ET.parse(index_path)
    root = tree.getroot()

    sitemap_urls = []
    for loc in root.findall("sm:sitemap/sm:loc", SITEMAP_NAMESPACE):
        if loc.text:
            sitemap_urls.append(loc.text.strip())

    return sitemap_urls


def extract_urls_from_sitemap(xml_path: Path) -> list[str]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    urls = []
    for loc in root.findall("sm:url/sm:loc", SITEMAP_NAMESPACE):
        if loc.text:
            urls.append(loc.text.strip())

    return urls


def download_file(url: str, destination: Path, timeout: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=timeout) as response:
        destination.write_bytes(response.read())


def build_output_name(sitemap_url: str) -> str:
    file_name = Path(urlparse(sitemap_url).path).name
    if not file_name:
        raise ValueError(f"Cannot determine file name from URL: {sitemap_url}")
    return file_name


def iter_sitemaps_with_progress(sitemap_urls: list[str]):
    if tqdm is None:
        return sitemap_urls

    return tqdm(sitemap_urls, desc="Processing sitemaps", unit="sitemap")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download all sitemap files listed in a sitemap index XML and extract URLs from each one."
    )
    parser.add_argument(
        "index_file",
        nargs="?",
        default=DEFAULT_INDEX_FILE,
        help="Path to the sitemap index XML file. Defaults to articles.xml in the current directory.",
    )
    parser.add_argument(
        "--xml-dir",
        default="downloaded_sitemaps",
        help="Directory to store downloaded sitemap XML files.",
    )
    parser.add_argument(
        "--txt-dir",
        default="extracted_urls",
        help="Directory to store extracted URL text files.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds for downloading each sitemap.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Redownload XML files and overwrite existing XML/TXT outputs.",
    )
    args = parser.parse_args()

    index_path = Path(args.index_file)
    if not index_path.is_absolute():
        index_path = Path.cwd() / index_path

    if not index_path.exists():
        print(f"Index file not found: {index_path}", file=sys.stderr)
        return 1

    xml_dir = Path(args.xml_dir)
    if not xml_dir.is_absolute():
        xml_dir = index_path.parent / xml_dir

    txt_dir = Path(args.txt_dir)
    if not txt_dir.is_absolute():
        txt_dir = index_path.parent / txt_dir

    try:
        sitemap_urls = parse_sitemap_index(index_path)
    except ET.ParseError as exc:
        print(f"Failed to parse sitemap index XML: {exc}", file=sys.stderr)
        return 1

    if not sitemap_urls:
        print("No sitemap URLs found in the index file.", file=sys.stderr)
        return 1

    xml_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)

    downloaded_count = 0
    extracted_count = 0

    progress = iter_sitemaps_with_progress(sitemap_urls)

    for sitemap_url in progress:
        try:
            sitemap_name = build_output_name(sitemap_url)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            continue

        xml_output_path = xml_dir / sitemap_name
        txt_output_path = txt_dir / f"{Path(sitemap_name).stem}.txt"

        if tqdm is not None:
            progress.set_postfix_str(sitemap_name)

        try:
            if args.overwrite or not xml_output_path.exists():
                print(f"Downloading {sitemap_url} -> {xml_output_path}")
                download_file(sitemap_url, xml_output_path, args.timeout)
                downloaded_count += 1
            else:
                print(f"Skipping existing XML: {xml_output_path}")

            if args.overwrite or not txt_output_path.exists():
                urls = extract_urls_from_sitemap(xml_output_path)
                txt_output_path.write_text("\n".join(urls), encoding="utf-8")
                print(f"Extracted {len(urls)} URLs -> {txt_output_path}")
                extracted_count += 1
            else:
                print(f"Skipping existing TXT: {txt_output_path}")
        except ET.ParseError as exc:
            print(f"Failed to parse sitemap XML {xml_output_path}: {exc}", file=sys.stderr)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"Failed to download {sitemap_url}: {exc}", file=sys.stderr)
        except OSError as exc:
            print(f"File write error for {sitemap_name}: {exc}", file=sys.stderr)

    print(
        f"Done. Found {len(sitemap_urls)} sitemaps, downloaded {downloaded_count}, extracted {extracted_count}.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
