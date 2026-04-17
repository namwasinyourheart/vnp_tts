from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

import requests


def _post_json(url: str, payload: dict, timeout_s: float) -> dict:
    resp = requests.post(url, json=payload, timeout=timeout_s)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        detail = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"HTTP {resp.status_code} calling {url}: {detail}") from exc
    return resp.json()


def normalize_text(base_url: str, text: str, lang: str = "vi", timeout_s: float = 60.0) -> str:
    url = base_url.rstrip("/") + "/text-verbalization"
    data = _post_json(url, {"text": text, "lang": lang}, timeout_s=timeout_s)
    if "normalized_text" not in data:
        raise RuntimeError(f"Unexpected response from {url}: {data}")
    return str(data["normalized_text"])


def normalize_batch(base_url: str, texts: List[str], lang: str = "vi", timeout_s: float = 300.0) -> List[str]:
    url = base_url.rstrip("/") + "/text-verbalization/batch"
    data = _post_json(url, {"texts": texts, "lang": lang}, timeout_s=timeout_s)
    if "normalized_texts" not in data:
        raise RuntimeError(f"Unexpected response from {url}: {data}")
    out = data["normalized_texts"]
    if not isinstance(out, list):
        raise RuntimeError(f"Unexpected response from {url}: {data}")
    return [str(x) for x in out]


def _read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Client for Text Verbalization API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base url")
    parser.add_argument("--lang", default="vi", help="Language code")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout (seconds)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Single input text")
    group.add_argument("--texts", nargs="+", help="Multiple input texts")
    group.add_argument("--file", help="Read inputs from a UTF-8 text file (1 input per line)")
    group.add_argument(
        "--stdin",
        action="store_true",
        help="Read a single input text from stdin (recommended for long text or quotes)",
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Use batch endpoint when multiple inputs are provided",
    )
    parser.add_argument("--json", action="store_true", help="Print raw JSON to stdout")

    args = parser.parse_args(argv)

    if args.text is not None:
        out = normalize_text(args.base_url, args.text, lang=args.lang, timeout_s=args.timeout)
        if args.json:
            sys.stdout.write(json.dumps({"normalized_text": out}, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(out + "\n")
        return 0

    if args.stdin:
        text = sys.stdin.read()
        out = normalize_text(args.base_url, text, lang=args.lang, timeout_s=args.timeout)
        if args.json:
            sys.stdout.write(json.dumps({"normalized_text": out}, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(out + "\n")
        return 0

    if args.file is not None:
        inputs = [x for x in _read_lines(args.file) if x.strip()]
    else:
        inputs = args.texts or []

    if not inputs:
        raise RuntimeError("No input texts provided")

    if args.batch or len(inputs) > 1:
        outs = normalize_batch(args.base_url, inputs, lang=args.lang, timeout_s=max(args.timeout, 60.0))
        if args.json:
            sys.stdout.write(json.dumps({"normalized_texts": outs}, ensure_ascii=False) + "\n")
        else:
            for line in outs:
                sys.stdout.write(line + "\n")
        return 0

    out = normalize_text(args.base_url, inputs[0], lang=args.lang, timeout_s=args.timeout)
    if args.json:
        sys.stdout.write(json.dumps({"normalized_text": out}, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# Example Usage
# python /home/nampv1/projects/tts/vnp_tts/data_prep/text_verbalization/app/client.py \
#   --text "2/9"

# python .../app/client.py \
#   --texts "2/9" "ngày 2/9" "45km" \
#   --batch


# python .../app/client.py \
#   --file inputs.txt \
#   --batch

# python /home/nampv1/projects/tts/vnp_tts/data_prep/text_verbalization/app/client.py --stdin <<'EOF'
# VN-Index đóng cửa ở sát 1.820 điểm, tăng hơn 19 điểm so với hôm qua. Tuy nhiên, thị trường có tới 213 cổ phiếu bị nhuộm đỏ, cao gấp đôi so với bên tăng giá. Điều này cho thấy chứng khoán hôm nay rơi vào trạng thái "xanh vỏ, đỏ lòng" và chỉ số chung chỉ được hỗ trợ bởi một số nhóm cổ phiếu nhất định.
# EOF