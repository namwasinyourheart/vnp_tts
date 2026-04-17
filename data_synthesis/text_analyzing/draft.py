import re

def extract_emails(text: str):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)

def extract_urls(text: str):
    pattern = r"(https?://[^\s]+|www\.[^\s]+|(?<!@)\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b)"
    urls = re.findall(pattern, text)
    return [u.rstrip(".,;:!?") for u in urls]

def contains_email(text: str) -> bool:
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.search(pattern, text) is not None


def contains_url(text: str) -> bool:
    pattern = r"(https?://[^\s]+|www\.[^\s]+|(?<!@)\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b)"
    return re.search(pattern, text) is not None


import re

ROMAN_REGEX = re.compile(
    r"\bM{0,3}(CM|CD|D?C{0,3})"
    r"(XC|XL|L?X{0,3})"
    r"(IX|IV|V?I{0,3})\b"
)

def extract_roman_numerals(text: str):
    return [m.group() for m in ROMAN_REGEX.finditer(text) if m.group()]

def contains_roman_numeral(text: str) -> bool:
    return re.search(ROMAN_REGEX, text) is not None


import re

def contains_alphanumeric(text: str) -> bool:
    # pattern = r"(?=.*[A-Za-z])(?=.*\d)"
    pattern = r"(?=.*a-zA-ZÀ-ỹ)(?=.*\d)"
    return re.search(pattern, text) is not None

def extract_alphanumeric(text: str):
    # pattern = r"\b(?=\w*[A-Za-z])(?=\w*\d)\w+\b"
    pattern = r"\b(?=\w*[a-zA-ZÀ-ỹ])(?=\w*\d)\w+\b"
    return re.findall(pattern, text)


def contains_percentage(text: str) -> bool:
    return PERCENT_REGEX.search(text) is not None

import re

PERCENT_REGEX = re.compile(r"\b\d+(?:[.,]\d+)?%")

def extract_percentages(text: str):
    return PERCENT_REGEX.findall(text)


import re

DECIMAL_REGEX = re.compile(r"\b-?\d+[.,]\d+\b")

def extract_decimals(text: str):
    return DECIMAL_REGEX.findall(text)

def contains_decimal(text: str) -> bool:
    return DECIMAL_REGEX.search(text) is not None


text = """
Liên hệ: nguyenvana@gmail.com
Website: https://example.com hoặc www.test.vn
Trang khác: abc.vn.
XIV
Ctrl + Z
123a b3, a6a, 100km, đ4 ê1 26d3
Tối ưu 25% vốn
Email: info@dantri.com.vn
1.5, 10.5, -12.34 14,5 1,000,000 32,4% 84B-0023
Theo thống kê của Phòng CSGT (PC67, Công an TP.Đà Nẵng)
5/2014/TT-BCA
từ 2,250 người xuống chỉ còn 1.300 người
0,4 miligam/lít khí thở
Giá SP500 hôm nay là 4.200,5 điểm
"""

emails = extract_emails(text)
urls = extract_urls(text)
roman_numerals = extract_roman_numerals(text)
percentages = extract_percentages(text)
decimals = extract_decimals(text)

print("Emails:", contains_email(text))
print("Emails:", emails)

print("-" * 20)

print("URLs:", contains_url(text))
print("URLs:", urls)

print("-" * 20)

print("Roman numerals:", contains_roman_numeral(text))
print("Roman numerals:", roman_numerals)

print("-" * 20)

print("Alphanumeric:", contains_alphanumeric(text))
print("Alphanumeric:", extract_alphanumeric(text))

print("-" * 20)

print("Percentages:", contains_percentage(text))
print("Percentages:", extract_percentages(text))

print("-" * 20)

print("Decimals:", contains_decimal(text))
print("Decimals:", extract_decimals(text))

