from vinorm import TTSnorm
texts = [
    "Trên cổng thông tin điện tử của Công an TP.HCM (CATP), mục thông tin về phương tiện vi phạm hành chính qua hình ảnh (từ ngày 4.1.2017 - 4.1.2018), có ghi nhận biển số xe, lỗi vi phạm, ngày vi phạm của 34.118 phương tiện (ô tô) chưa nộp phạt.",
    "abc đến xyz",
    "60 km/h 25Hz 34 HZ 26 km², 05km2",
    "4.336km²",
    "Ngày 10/2",
    "ngày 01/05/2000"
]
for written_text in texts:
    print(written_text)
    spoken_text = TTSnorm(written_text)
    print(spoken_text)
    print("\n" + "─"*60)