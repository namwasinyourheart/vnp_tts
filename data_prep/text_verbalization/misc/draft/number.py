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
