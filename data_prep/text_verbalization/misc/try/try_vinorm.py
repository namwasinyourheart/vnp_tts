import sys
from vinorm import TTSnorm

SAMPLE_INPUTS = [
    "Tôi có 25 quyển sách.",
    "Kết quả là 3.14.",
    "Đây là lần thứ 2 tôi đến đây.",
    "Nhiệt độ từ 20-30 độ.",
    "Số tài khoản là 123456789.",
    "Sự kiện diễn ra năm 2024.",
    "Sinh nhật tôi là 01-05-2000.",
    "Hẹn gặp lúc 7h45.",
    "Tôi nghỉ vào chủ nhật.",
    "Doanh thu quý II tăng mạnh."
]

def get_inputs():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return SAMPLE_INPUTS

def main():
    texts = get_inputs()
    print("\n===== soe-vinorm Normalization =====\n")
    for inp in texts:
        out = TTSnorm(inp)
        print(f"Input:    {inp}")
        print(f"Output:   {out}")
        print("-"*60)

if __name__ == "__main__":
    main()
