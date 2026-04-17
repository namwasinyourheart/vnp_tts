
import re
from typing import Dict, Set, Optional

from utils import load_sound_map
from number import read_vietnamese_number

# Load currency units from the central sound map
CURRENCY_UNIT_MAP = load_sound_map(unit_type='currency')

# Symbol map for currency symbols
SYMBOL_MAP = {
    "$": "đô la",
    "€": "euro",
}

def _get_unit_pattern(units: Set[str]) -> str:
    """Generate a regex pattern for matching units, sorted by length (longest first)
    to ensure longer matches are tried first."""
    return "|".join(re.escape(unit) for unit in sorted(units, key=len, reverse=True))

# Build the regex pattern from the maps
CURRENCY_RE = re.compile(
    rf"""
    (?:  # Match either symbol+number or number+unit
        (?P<symbol>[{'|'.join(re.escape(s) for s in SYMBOL_MAP)}])\s?(?P<num1>\d+(?:[.,]\d+)?)
        |
        (?P<num2>\d+(?:[.,]\d+)?)\s?(?P<unit>(?:{_get_unit_pattern(set(CURRENCY_UNIT_MAP.keys()))}))(?=\s|$)
    )
    """,
    re.IGNORECASE | re.VERBOSE
)



def read_money_number(s: str) -> str:
    s = s.replace(",", ".")
    if "." in s:
        i, f = s.split(".", 1)
        return f"{read_vietnamese_number(int(i))} phẩy " + " ".join(read_vietnamese_number(int(d)) for d in f)
    return read_vietnamese_number(int(s))


def verbalize_currency_core(match: re.Match) -> str:
    if match.group("symbol"):
        num = match.group("num1")
        unit = SYMBOL_MAP[match.group("symbol")]
    else:
        num = match.group("num2")
        unit_key = match.group("unit").lower()
        # Map 'triệu' to 'm' which is already in our map
        if unit_key == 'triệu':
            unit_key = 'm'
        unit = CURRENCY_UNIT_MAP[unit_key]

    num_spoken = read_money_number(num)
    return f"{num_spoken} {unit}"



def verbalize_currency_sentence(sentence: str) -> str:
    output = sentence

    for m in reversed(list(CURRENCY_RE.finditer(sentence))):
        spoken = verbalize_currency_core(m)
        output = output[:m.start()] + spoken + output[m.end():]

    return output


tests = [
    "1.25đ nghìn, 1,3vnđ triệu",
    "Giá là 10.000đ 10k 10 k",
    "Thu nhập 5 triệu một tháng",
    "Phí khoảng 100k",
    "Tổng cộng $50",
    # "Giá vé 1.5 triệu",
    "Lương 300 USD",
]

tests = [
    "Trên cổng thông tin điện tử của Công an TP.HCM (CATP), mục thông tin về phương tiện vi phạm hành chính qua hình ảnh (từ ngày 4.1.2017 - 4.1.2018), có ghi nhận biển số xe, lỗi vi phạm, ngày vi phạm của 34.118 phương tiện (ô tô) chưa nộp phạt",
]

for t in tests:
    print("IN :", t)
    print("OUT:", verbalize_currency_sentence(t))
    print("-" * 40)




