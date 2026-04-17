import re

def add_punctuation_pause(text: str) -> list:
    """
    Mô phỏng cách CosyVoice3 xử lý dấu câu và đánh dấu nhịp ngắt
    Trả về: văn bản đã tách đoạn + thời lượng ngắt gợi ý (đơn vị: mili giây)
    """

    pause_map = {
        ',': 250,
        '.': 600,
        '?': 700,
        '!': 700,
        ';': 400,
        ':': 350
    }

    segments = re.split('([,。?!;:])', text)
    result = []

    for i in range(0, len(segments)-1, 2):
        content = segments[i].strip()
        punct = segments[i+1] if i+1 < len(segments) else ''

        if content:
            duration = pause_map.get(punct, 0)
            result.append({
                "text": content + punct,
                "pause_ms": duration
            })

    return result


# Ví dụ sử dụng
input_text = "Hôm nay thời tiết khá đẹp, chúng ta đi công viên nhé! Bạn thấy thế nào?"
segments = add_punctuation_pause(input_text)

for seg in segments:
    print(f"[{seg['text']}] -> thêm {seg['pause_ms']}ms ngắt")