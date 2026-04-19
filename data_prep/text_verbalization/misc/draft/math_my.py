import re

from number import read_vietnamese_number


# =======================
# Math symbol sound map
# =======================

MATH_SYMBOL_SOUND_MAP = {
    "+": "cộng",
    "×": "nhân",
    "x": "nhân",
    "*": "nhân",
    "÷": "chia",
    "/": "chia",
    "=": "bằng",
    ">": "lớn hơn",
    "<": "nhỏ hơn",
    ">=": "lớn hơn hoặc bằng",
    "<=": "nhỏ hơn hoặc bằng",
    "≠": "không bằng",
}

# =======================
# Regex
# =======================

NO_SPACE_RANGE_RE = re.compile(r"(\d+)-(\d+)")
MATH_RE = re.compile(r"(>=|<=|≠|>|<|=|\+|−|-|×|x|\*|÷|/)")

# =======================
# Core
# =======================

def verbalize_range_core(a: int, b: int) -> str:
    if b > a:
        return f"{read_vietnamese_number(a)} đến {read_vietnamese_number(b)}"
    return f"{read_vietnamese_number(a)} {read_vietnamese_number(b)}"

def verbalize_math_symbol(symbol: str) -> str:
    return MATH_SYMBOL_SOUND_MAP.get(symbol, symbol)

# =======================
# Sentence-level API
# =======================

def verbalize_math_sentence(sentence: str) -> str:
    # 1. Handle no-space numeric ranges first (A-B => đến)
    output = sentence
    for m in reversed(list(NO_SPACE_RANGE_RE.finditer(output))):
        a, b = int(m.group(1)), int(m.group(2))
        spoken = verbalize_range_core(a, b)
        output = output[:m.start()] + spoken + output[m.end():]

    # 2. Handle remaining math symbols (space-separated '-' => trừ)
    tokens = output.split()
    result = []

    for tok in tokens:
        if tok in MATH_SYMBOL_SOUND_MAP:
            result.append(verbalize_math_symbol(tok))
        elif tok in {"-", "−"}:
            result.append("trừ")
        else:
            result.append(tok)

    return " ".join(result)

# =======================
# Tests
# =======================

if __name__ == "__main__":
    tests = [
        "example@gmail.com",
        "3 + 5 = 8",
        "10 - 3 = 7",
        "Giai đoạn 2020-2023 tăng trưởng tốt",
        "10-8",
        "2-3",
        "x - y",
        "a <= b",

    ]

    for t in tests:
        print("IN :", t)
        print("OUT:", verbalize_math_sentence(t))
        print("-" * 50)
