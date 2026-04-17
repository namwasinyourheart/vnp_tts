import re

try:
    from .datetime import read_vietnamese_number, verbalize_date_core
except ImportError:
    from datetime import read_vietnamese_number, verbalize_date_core


_VINORM_DATE_FULL_RE = re.compile(
    r"(?i)\b([0-3]?\d)\s*[\/\-.]\s*([01]?\d)\s*[\/\-.]\s*([12]\d{3})\b"
)
_VINORM_DATE_DM_CTX_RE = re.compile(
    r"(?i)\b(ngày|sáng|trưa|chiều|tối|đêm|hôm|nay|hai|ba|tư|năm|sáu|bảy|nhật|qua|lúc|từ|đến)\s+([0-3]?\d)\s*[\/\-.]\s*([01]?\d)\b"
)
_VINORM_MONTH_YEAR_RE = re.compile(r"(?i)\btháng\s+([01]?\d)\s*[\/\-.]\s*(\d{4})\b")
_VINORM_DATE_RANGE_1_RE = re.compile(
    r"(?i)\b(từ|ngày)\s+([0-3]?\d)\s*-\s*([0-3]?\d)\s*[.\/]\s*([01]?\d)\b"
)
_VINORM_DATE_RANGE_1B_RE = re.compile(
    r"(?i)\b(từ|ngày)\s+([0-3]?\d)\s*[.\/]\s*([01]?\d)\s*(-|đến)\s*([0-3]?\d)\s*[.\/]\s*([01]?\d)\b"
)
_VINORM_MONTH_RANGE_2A_RE = re.compile(
    r"(?i)\b(từ|tháng)\s+([01]?\d)\s*-\s*([01]?\d)\s*[.\/]\s*([12]\d{3})\b"
)
_VINORM_MONTH_RANGE_2B_RE = re.compile(
    r"(?i)\b(từ|tháng)\s+([01]?\d)\s*[.\/]\s*([12]\d{3})\s*(-|đến)\s*([01]?\d)\s*[.\/]\s*([12]\d{3})\b"
)


def _is_valid_date_components(d: int, m: int, y: int | None = None) -> bool:
    if not (1 <= d <= 31):
        return False
    if not (1 <= m <= 12):
        return False
    if y is not None and y < 0:
        return False
    return True


def normalize_dates_vinorm_style(text: str) -> str:
    def repl_full(match: re.Match):
        d_s, m_s, y_s = match.group(1), match.group(2), match.group(3)
        d, m, y = int(d_s), int(m_s), int(y_s)
        if not _is_valid_date_components(d, m, y):
            return match.group(0)
        spoken = verbalize_date_core(d, m, y, use_mung=True)
        return "ngày " + spoken

    def repl_dm_ctx(match: re.Match):
        kw, d_s, m_s = match.group(1), match.group(2), match.group(3)
        d, m = int(d_s), int(m_s)
        if not _is_valid_date_components(d, m):
            return match.group(0)
        spoken = verbalize_date_core(d, m, None, use_mung=True)
        if kw.lower() == "ngày":
            return "ngày " + spoken
        return kw + " " + spoken

    def repl_month_year(match: re.Match):
        m_s, y_s = match.group(1), match.group(2)
        m, y = int(m_s), int(y_s)
        if not (1 <= m <= 12):
            return match.group(0)
        return f"tháng {read_vietnamese_number(m)} năm {read_vietnamese_number(y)}"

    def repl_range_1(match: re.Match):
        kw, d1_s, d2_s, m_s = match.group(1), match.group(2), match.group(3), match.group(4)
        d1, d2, m = int(d1_s), int(d2_s), int(m_s)
        if not (_is_valid_date_components(d1, m) and _is_valid_date_components(d2, m)):
            return match.group(0)
        left = f"ngày {verbalize_date_core(d1, m, None, use_mung=True)}"
        right = f"ngày {verbalize_date_core(d2, m, None, use_mung=True)}"
        if kw.lower() == "từ":
            return f"từ {left} đến {right}"
        return f"{kw} {read_vietnamese_number(d1)} đến {read_vietnamese_number(d2)} tháng {read_vietnamese_number(m)}"

    def repl_range_1b(match: re.Match):
        kw, d1_s, m1_s, _sep, d2_s, m2_s = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
            match.group(5),
            match.group(6),
        )
        d1, m1, d2, m2 = int(d1_s), int(m1_s), int(d2_s), int(m2_s)
        if not (_is_valid_date_components(d1, m1) and _is_valid_date_components(d2, m2)):
            return match.group(0)
        left = f"ngày {verbalize_date_core(d1, m1, None, use_mung=True)}"
        right = f"ngày {verbalize_date_core(d2, m2, None, use_mung=True)}"
        if kw.lower() == "từ":
            return f"từ {left} đến {right}"
        return f"{kw} {left} đến {right}"

    def repl_month_range_2a(match: re.Match):
        kw, m1_s, m2_s, y_s = match.group(1), match.group(2), match.group(3), match.group(4)
        m1, m2, y = int(m1_s), int(m2_s), int(y_s)
        if not (1 <= m1 <= 12 and 1 <= m2 <= 12):
            return match.group(0)
        left = f"tháng {read_vietnamese_number(m1)} năm {read_vietnamese_number(y)}"
        right = f"tháng {read_vietnamese_number(m2)} năm {read_vietnamese_number(y)}"
        if kw.lower() == "từ":
            return f"từ {left} đến {right}"
        return f"{kw} {read_vietnamese_number(m1)} đến {read_vietnamese_number(m2)} năm {read_vietnamese_number(y)}"

    def repl_month_range_2b(match: re.Match):
        kw, m1_s, y1_s, _sep, m2_s, y2_s = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
            match.group(5),
            match.group(6),
        )
        m1, y1, m2, y2 = int(m1_s), int(y1_s), int(m2_s), int(y2_s)
        if not (1 <= m1 <= 12 and 1 <= m2 <= 12):
            return match.group(0)
        left = f"tháng {read_vietnamese_number(m1)} năm {read_vietnamese_number(y1)}"
        right = f"tháng {read_vietnamese_number(m2)} năm {read_vietnamese_number(y2)}"
        if kw.lower() == "từ":
            return f"từ {left} đến {right}"
        return f"{kw} {left} đến {right}"

    text = _VINORM_MONTH_RANGE_2B_RE.sub(repl_month_range_2b, text)
    text = _VINORM_MONTH_RANGE_2A_RE.sub(repl_month_range_2a, text)
    text = _VINORM_DATE_RANGE_1B_RE.sub(repl_range_1b, text)
    text = _VINORM_DATE_RANGE_1_RE.sub(repl_range_1, text)
    text = _VINORM_MONTH_YEAR_RE.sub(repl_month_year, text)
    text = _VINORM_DATE_DM_CTX_RE.sub(repl_dm_ctx, text)
    text = _VINORM_DATE_FULL_RE.sub(repl_full, text)
    return text

if __name__ == "__main__":
    tests = [
        "2025",
        "Cuộc họp diễn ra lúc 8:30 ngày 20/10/2024, 01/11/2025",
        "Hẹn gặp lúc 21:59, 22:35:22, 08:59:07",
        "Sự kiện tổ chức vào 1/6, 14/5",
        "Giai đoạn 2020-2023 tăng trưởng tốt hơn 2021-2019",
        "Ở nhóm Big4, Vietcombank cho biết lợi nhuận trước thuế năm 2025 trên 45.000 tỷ đồng, đạt mức cao nhất lịch sử. Tính đến ngày 31/12/2025, tổng tài sản của ngân hàng này cũng đạt 2,48 triệu tỷ đồng, tăng gần 20% so với cuối năm 2024. Dư nợ cấp tín dụng đối với nền kinh tế đạt khoảng 1,66 triệu tỷ đồng, tăng hơn 15%."
    ]

    for t in tests:
        print("IN :", t)
        print("OUT:", normalize_dates_vinorm_style(t))
        print("-" * 60)

