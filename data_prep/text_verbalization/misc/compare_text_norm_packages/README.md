# Text Normalizer Comparison for Vietnamese

Script để so sánh output của các text normalizer packages cho tiếng Việt.

## Packages được so sánh

1. **soe-vinorm** - https://pypi.org/project/soe-vinorm/
   - Text normalization cho Vietnamese TTS
   
2. **Viphoneme** - https://github.com/v-nhandt21/Viphoneme
   - Vietnamese text to phoneme conversion
   
3. **sea-g2p** - https://github.com/pnnbao97/sea-g2p
   - Southeast Asian Grapheme-to-Phoneme conversion
   
4. **NeMo** - https://github.com/NVIDIA/NeMo-text-processing
   - NVIDIA's text normalization toolkit

## Cài đặt

```bash
pip install -r requirements.txt
```

**Lưu ý:** Một số packages có thể cần cài đặt thêm dependencies:

### NeMo Text Processing
```bash
# Cài đặt NeMo với text processing
pip install nemo_text_processing
```

### Viphoneme
```bash
pip install viphoneme
```

## Sử dụng

### Chạy script so sánh cơ bản

```bash
python compare_normalizers.py
```

Script sẽ:
- Load tất cả normalizers có sẵn
- Chạy test cases mẫu
- In kết quả so sánh ra console
- Lưu kết quả vào file `comparison_results.csv`

### Sử dụng trong code

```python
from compare_normalizers import NormalizerComparison

# Khởi tạo
comparator = NormalizerComparison()

# So sánh một text
result = comparator.compare_single_text("Tôi có 25 quyển sách.")
print(result)

# So sánh nhiều texts
texts = [
    "Ngày 10/2",
    "60 km/h",
    "Giá $1,234.56"
]
comparator.print_comparison(texts, output_file='my_results.csv')
```

## Test Cases

Script bao gồm các test cases cho:

- **Numbers**: Số đếm, số thập phân, số lớn
- **Ordinals**: Số thứ tự
- **Dates**: Ngày tháng năm ở nhiều format khác nhau
- **Time**: Giờ phút
- **Measurements**: Đơn vị đo lường (km/h, Hz, km², độ C)
- **Currency**: Tiền tệ (VNĐ, USD)
- **Ranges**: Khoảng giá trị
- **Mixed content**: Nội dung phức tạp kết hợp nhiều loại
- **Special characters**: Email, ký tự đặc biệt
- **Scientific notation**: Ký hiệu khoa học

## Output

Kết quả sẽ hiển thị:
- Input text gốc
- Output từ mỗi normalizer
- Status (✓ loaded / ✗ failed) cho mỗi package
- File CSV chứa tất cả kết quả để phân tích

## Xử lý lỗi

Script được thiết kế để:
- Tiếp tục chạy ngay cả khi một số packages không cài đặt được
- Hiển thị rõ ràng package nào đã load thành công
- Capture và hiển thị errors từ từng normalizer

## Mở rộng

Để thêm test cases mới, chỉnh sửa function `get_test_cases()` trong `compare_normalizers.py`:

```python
def get_test_cases() -> List[str]:
    return [
        "Test case của bạn",
        # ... thêm cases khác
    ]
```
