import re


def number_to_vietnamese(n, zero_read="lẻ", four_read="auto"):
    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    tens_words = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi",
                  "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]
    scales = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ", "tỷ tỷ"]

    def read_three_digits(num, is_first_group=False):
        hundred = num // 100
        ten = (num % 100) // 10
        one = num % 10
        parts = []

        # Hàng trăm
        if hundred > 0:
            parts.append(units[hundred] + " trăm")
        elif not is_first_group and num != 0:
            parts.append("không trăm")

        # Hàng chục
        if ten > 1:
            parts.append(tens_words[ten])
        elif ten == 1:
            parts.append("mười")
        else:  # ten == 0
            if one > 0 and (hundred > 0 or not is_first_group):
                parts.append(zero_read)

        # Hàng đơn vị
        if one > 0:
            # chọn đọc "4" theo chế độ four_read
            def read_four(current_ten):
                if four_read == "auto":
                    return "tư" if current_ten >= 2 else "bốn"
                elif four_read == "tư":
                    return "tư"
                else:
                    return "bốn"

            if ten == 0 or ten == 1:
                if one == 5 and ten > 0:
                    parts.append("lăm")
                else:
                    # mặc định lấy từ units (bốn) cho trường hợp ten==0 hoặc ten==1,
                    # nhưng nếu user yêu cầu four_read="tu", cho phép đọc "tư"
                    if one == 4:
                        parts.append(read_four(ten))
                    else:
                        parts.append(units[one])
            else:
                # ten >= 2: xử lý mốt/tư/lăm theo quy tắc
                if one == 1:
                    parts.append("mốt")
                elif one == 4:
                    parts.append(read_four(ten))
                elif one == 5:
                    parts.append("lăm")
                else:
                    parts.append(units[one])

        return " ".join(parts)

    if n == 0:
        return "không"

    s = str(n)
    groups = []
    while s:
        groups.insert(0, int(s[-3:]))
        s = s[:-3]

    words = []
    group_len = len(groups)

    for idx, g in enumerate(groups):
        is_first_group = (idx == 0)
        if g != 0:
            group_words = read_three_digits(g, is_first_group)
            if group_words:
                words.append(group_words)
                scale = scales[group_len - idx - 1]
                if scale:
                    words.append(scale)
    return " ".join(words).strip()


def has_leading_zero(s: str) -> bool:
    return len(s) > 1 and s[0] == "0" and s.isdigit()

def read_vietnamese_number(value: str | int) -> str:
    units = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    s = str(value)

    if isinstance(value, str) and has_leading_zero(s):
        return " ".join(units[int(ch)] for ch in s)

    return number_to_vietnamese(int(s))

# =======================
# Number reading (basic)
# =======================

NUM = {
    0: "không", 1: "một", 2: "hai", 3: "ba", 4: "bốn",
    5: "năm", 6: "sáu", 7: "bảy", 8: "tám", 9: "chín",
    10: "mười"
}


def read_vietnamese_number_1(n: int) -> str:
    if n < 10:
        return NUM[n]
    if n < 20:
        return "mười" if n == 10 else "mười " + NUM[n % 10]
    if n < 100:
        t, o = divmod(n, 10)
        if o == 0:
            return NUM[t] + " mươi"
        if o == 1:
            return NUM[t] + " mươi mốt"
        if o == 5:
            return NUM[t] + " mươi lăm"
        return NUM[t] + " mươi " + NUM[o]
    if n < 1000:
        h, r = divmod(n, 100)
        if r == 0:
            return NUM[h] + " trăm"
        if r < 10:
            return NUM[h] + " trăm lẻ " + read_vietnamese_number(r)
        return NUM[h] + " trăm " + read_vietnamese_number(r)
    if n < 10000:
        th, r = divmod(n, 1000)
        if r == 0:
            return NUM[th] + " nghìn"
        return NUM[th] + " nghìn " + read_vietnamese_number(r)
    return str(n)

# =======================
# Regex & keywords
# =======================

DATE_RE  = re.compile(r"^(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?$")
TIME_RE  = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")
RANGE_RE = re.compile(r"^(\d{4})[–-](\d{4})$")

# Full date pattern (dd/mm/yyyy) - no context required, like vinorm
DATE_FULL_RE = re.compile(r"(?i)\b([0-3]?\d)\s*[\/\-.]\s*([01]?\d)\s*[\/\-.]\s*([12]\d{3})\b")
# Day/Month pattern (dd/mm) without year - no context required
DATE_DM_RE = re.compile(r"(?i)\b([0-3]?\d)\s*[\/\-.]\s*([01]?\d)\b(?![\/\-.]\s*\d)")
# Month/Year pattern (mm/yyyy) without day - no context required
DATE_MY_RE = re.compile(r"(?i)\b([01]?\d)\s*[\/\-.]\s*([12]\d{3})\b")
# Full time pattern (HH:MM or HH:MM:SS) - no context required
TIME_FULL_RE = re.compile(r"(?i)\b(?:2[0-4]|[01]?[0-9])\s*[:h]\s*[0-5][0-9](?:\s*[:\.]?\s*[0-5][0-9])?\b")

DATE_KW = {"ngày", "tháng", "năm", "hôm"}
TIME_KW = {"lúc", "vào", "thời", "giờ", "phút"}

PUNCT = ",.;:?!"

# =======================
# Helpers
# =======================

def split_punct(token: str):
    core = token.strip(PUNCT)
    prefix = token[:len(token) - len(token.lstrip(PUNCT))]
    suffix = token[len(token.rstrip(PUNCT)):]
    return prefix, core, suffix

def get_context(words, idx, window=3):
    prev_w = set(w.lower().strip(PUNCT) for w in words[max(0, idx - window):idx])
    next_w = set(w.lower().strip(PUNCT) for w in words[idx + 1:idx + 1 + window])
    return {
        "date": bool(prev_w & DATE_KW),
        "time": bool(prev_w & TIME_KW or next_w & TIME_KW)
    }

# =======================
# Verbalizer cores
# =======================

def verbalize_date_core(d, m, y=None, use_mung=False):
    if use_mung and 1 <= d <= 10:
        day_part = f"mùng {read_vietnamese_number(d)}"
    else:
        day_part = read_vietnamese_number(d)

    s = f"{day_part} tháng {read_vietnamese_number(m)}"
    if y:
        s += f" năm {read_vietnamese_number(y)}"
    return s

def verbalize_time_core(h, m, s=None):
    if m == 0:
        return f"{read_vietnamese_number(h)} giờ"
    out = f"{read_vietnamese_number(h)} giờ {read_vietnamese_number(m)} phút"
    if s:
        out += f" {read_vietnamese_number(s)} giây"
    return out

def verbalize_range_core(a: int, b: int):
    if b > a:
        return f"{read_vietnamese_number(a)} đến {read_vietnamese_number(b)}"
    else:
        return f"{read_vietnamese_number(a)} {read_vietnamese_number(b)}"


# =======================
# Sentence-level API
# =======================

def verbalize_datetime_sentence(sentence: str) -> str:
    words = sentence.split()
    output_words = words[:]

    for i, w in enumerate(words):
        prefix, core, suffix = split_punct(w)
        ctx = get_context(words, i)

        # ---- DATE (with context keywords) ----
        m = DATE_RE.match(core)
        if m and ctx["date"]:
            d, mo, y = m.groups()
            d, mo = int(d), int(mo)
            y = int(y) if y else None

            spoken = verbalize_date_core(d, mo, y, use_mung=True)

            if (i == 0 or words[i - 1].lower().strip(PUNCT) != "ngày"):
                spoken = "ngày " + spoken

            output_words[i] = prefix + spoken + suffix
            continue

        # ---- DATE (full date dd/mm/yyyy without context) ----
        m = DATE_FULL_RE.match(core)
        if m:
            d, mo, y = m.groups()
            d, mo, y = int(d), int(mo), int(y)
            # Validate date components
            if 1 <= d <= 31 and 1 <= mo <= 12 and y > 0:
                spoken = verbalize_date_core(d, mo, y, use_mung=True)
                spoken = "ngày " + spoken
                output_words[i] = prefix + spoken + suffix
                continue

        # ---- DATE (day/month dd/mm without year, no context required) ----
        m = DATE_DM_RE.match(core)
        if m:
            d_s, m_s = m.groups()
            d, mo = int(d_s), int(m_s)
            # Validate: day 1-31, month 1-12
            if 1 <= d <= 31 and 1 <= mo <= 12:
                spoken = verbalize_date_core(d, mo, None, use_mung=True)
                spoken = "ngày " + spoken
                output_words[i] = prefix + spoken + suffix
                continue

        # ---- DATE (month/year mm/yyyy without day, no context required) ----
        m = DATE_MY_RE.match(core)
        if m:
            m_s, y_s = m.groups()
            mo, y = int(m_s), int(y_s)
            # Validate: month 1-12, year > 0
            if 1 <= mo <= 12 and y > 0:
                spoken = f"tháng {read_vietnamese_number(mo)} năm {read_vietnamese_number(y)}"
                output_words[i] = prefix + spoken + suffix
                continue

        # ---- TIME ----
        m = TIME_RE.match(core)
        if m and ctx["time"]:
            h, mi, s = m.groups()
            spoken = verbalize_time_core(int(h), int(mi), int(s) if s else None)
            output_words[i] = prefix + spoken + suffix
            continue

        # ---- TIME (full time HH:MM or HH:MM:SS without context) ----
        m = TIME_FULL_RE.match(core)
        if m:
            # Parse time from matched string
            time_str = core.lower().replace('h', ':')
            parts = re.split(r'[:\.]', time_str)
            if len(parts) >= 2:
                try:
                    h = int(parts[0])
                    mi = int(parts[1])
                    s = int(parts[2]) if len(parts) > 2 and parts[2] else None
                    if 0 <= h <= 24 and 0 <= mi <= 59 and (s is None or 0 <= s <= 59):
                        spoken = verbalize_time_core(h, mi, s)
                        output_words[i] = prefix + spoken + suffix
                        continue
                except (ValueError, IndexError):
                    pass

        # ---- RANGE ----
        # ---- RANGE (generic number range) ----
        m = RANGE_RE.match(core)
        if m:
            a, b = m.groups()
            a, b = int(a), int(b)

            spoken = verbalize_range_core(a, b)
            if spoken:
                output_words[i] = prefix + spoken + suffix

            continue

    return " ".join(output_words)


# =======================
# Tests
# =======================

if __name__ == "__main__":
    date_tests = [
        "ngày 08/12/2025",
        "3/5/2100", 
        "03/4/2004", 
        "22/4/1994",
        "1/6, 15/7, 03/4, 3/5",
        "ngày 15/05",
        "09/2025, 7/2005, 25/2026",
    ]

    time_tests = [
        "08:59:22, 8:54, 07:25",
        "07:25",
        "25:46",
        "Cuộc họp diễn ra lúc 8:30 ngày 20/10/2024, 01/11/2025",
        "Hẹn gặp lúc 21:59, 22:35:22, 08:59:07",
    ]

    # "Sự kiện tổ chức vào 1/6, 14/5",
    # "Giai đoạn 2020-2023 tăng trưởng tốt hơn 2021-2019",
    # "Ở nhóm Big4, Vietcombank cho biết lợi nhuận trước thuế năm 2025 trên 45.000 tỷ đồng, đạt mức cao nhất lịch sử. Tính đến ngày 31/12/2025, tổng tài sản của ngân hàng này cũng đạt 2,48 triệu tỷ đồng, tăng gần 20% so với cuối năm 2024. Dư nợ cấp tín dụng đối với nền kinh tế đạt khoảng 1,66 triệu tỷ đồng, tăng hơn 15%."

    # for t in date_tests:
    #     print("IN :", t)
    #     print("OUT:", verbalize_datetime_sentence(t))
    #     print("-" * 60)
    
    for t in date_tests:
        print("IN :", t)
        print("OUT:", verbalize_datetime_sentence(t))
        print("-" * 60)
