import re
from utils import load_sound_map
from number import read_vietnamese_number
from sound_map import get_units

UNIT_SOUND_MAP = get_units()

MEASURE_RE = re.compile(
    r"""
    (?P<num>\d+(?:[.,]\d+)?)
    \s?
    (?P<unit>km/h|m/s|km2|m2|mm|cm|dm|km|mg|kg|ml|°c|g|l|m|t|c)
    \b
    """,
    re.IGNORECASE | re.VERBOSE
)


def read_measure_number(s: str) -> str:
    s = s.replace(",", ".")
    if "." in s:
        i, f = s.split(".", 1)
        return f"{read_vietnamese_number(int(i))} phẩy " + " ".join(read_vietnamese_number(int(d)) for d in f)
    return read_vietnamese_number(int(s))


def verbalize_measure_core(num: str, unit: str) -> str:
    unit_key = unit.lower()
    unit_spoken = UNIT_SOUND_MAP.get(unit_key)

    if not unit_spoken:
        return f"{num}{unit}"  # fallback, không động vào

    return f"{read_measure_number(num)} {unit_spoken}"



def verbalize_measure_sentence(sentence: str) -> str:
    output = sentence

    for m in reversed(list(MEASURE_RE.finditer(sentence))):
        num = m.group("num")
        unit = m.group("unit")

        spoken = verbalize_measure_core(num, unit)
        output = output[:m.start()] + spoken + output[m.end():]

    return output

if __name__ == "__main__":

    tests = [
        "Chiều dài 10cm, 197.06 dm",
        "Quãng đường 3.5km",
        "Cân nặng 70kg",
        "Dung tích 1.5l",
        "Nhiệt độ 37°C",
        "Diện tích 20m2",
        "Tốc độ 60km/h",
        "Vận tốc 5m/s",
    ]

    for t in tests:
        print("IN :", t)
        print("OUT:", verbalize_measure_sentence(t))
        print("-" * 40)
