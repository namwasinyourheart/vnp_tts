import os
import sys
from functools import lru_cache
from pathlib import Path
from time import perf_counter

SCRIPT_START = perf_counter()

SAMPLE_INPUTS = [
    # FREE
    "thập niên XVI",
    "Năm học 2025-2026",
    "TB/UBKT",
    "17- TB/UBKT, 17-TB/UBKT, ATO, UBKT",
    "NASA",
    "ngày 7/4 và 8/4, chiều 7/4 và 8/4, 4/14, ngày 4/104",
    "9/4 và 10/4, tháng 4/2026 và 5/2026",
    "ngày 7/4 và 8/4, 9/4 và 10/4",
    "còn nhiều nữa...",
    "Vn-Index",
    "Khối ngoại tiếp tục gây áp lực lên tâm lý chung khi bán ròng khoảng 1.185 tỷ đồng. Hai cổ phiếu bị xả hàng nhiều nhất là FPT (gần 524 tỷ đồng) và VHM (gần 463 tỷ đồng). Trong khi đó, nhà đầu tư nước ngoài mua ròng mạnh ở VIC (gần 465 tỷ đồng) và SSI (hơn 235 tỷ đồng).",
    # """Tổng thống Trump nói thỏa thuận hòa bình giữa Washington và Tehran đang "rất gần", thêm rằng Iran đã đồng ý bàn giao kho uranium làm giàu.""",
    "45km 45 km 4kg 4 kg",
    
    "86B-066",
    "cac-ngan-hang-o-at-giam-lai-suat-huy-dong-lai-suat-cho-vay-co-giam-20260413155555546.",
    "vinamilk@vinamilk.com.vn",
    "+ km135+450 % 1&2",
    "Km153+450 và Km156+985 QL18",
    "123456789012345678901234567890, ",
    "12345678, 12345678917258, 12,345,678",
    "29 – A1 123.45, 29 - A1 123.45",
    "2026, 4, 04, 0042948",
    "DH-2026-04-001",
    "thế kỷ của đức vua",
    "thế kỷ V của đức vua, nhà V",
    "thế kỷ ix của đức vua",
    "Nghị định 100/2019/NĐ-CP, Nghị định 04/2018/NĐ-CP",
    "Thông tư liên tịch 01/2017/TTLT-VKSNDTC-TANDTC-BCA-BTP, Thông tư 64/2017, công văn số 06/TTg-QHQT",
    # '''Tại Thông tư số 146/2017/TT-BTC, có hiệu lực thi hành kể từ ngày 12/02/2018, Bộ Tài chính hướng dẫn về quản lý, giám sát việc thu thuế đối với hoạt động kinh doanh casino quy định tại Nghị định số 03/2017/NĐ-CP ngày 16/01/2017 của Chính phủ''',
#     """Hai tháng sau hai người này bị khởi tố về tội trộm cắp tài sản nhưng VKS không đồng ý vì chưa đủ căn cứ xác định hai người này phạm tội với vai trò đồng phạm.
# Tháng 10-2016, VKSND TP ban hành cáo trạng truy tố bà Hoa tội trộm cắp tài sản theo khoản 4 Điều 138 BLHS 1999 (hình phạt từ 12 năm đến tù chung thân).""",
#     """Theo thống kê của Phòng CSGT (PC67, Công an TP.Đà Nẵng), từ ngày 1.1.2016 đến hết tháng 1.2018, PC67 gửi 13.479 lượt thông báo đến chủ phương tiện vi phạm luật Giao thông đường bộ.
# Đến nay còn 5.199 trường hợp chưa đến giải quyết, chiếm 38,5%.
# Đối với 8.280 trường hợp đến làm việc, qua phân tích lỗi, cơ quan chức năng đã lập biên bản 7.184 trường hợp, chuyển kho bạc hơn 9 tỉ đồng, tước giấy phép lái xe (có thời hạn) 2.107 trường hợp.""",
# "PC67",
# "Tại nạn xảy ra ở Km153+450, QL18, Quảng Nam. số nhà A25, và K129",
# """Một số ngân hàng ghi nhận mức giảm sâu hơn. LPBank khi cắt giảm từ 0,4 đến 1 điểm %/năm ở các kỳ hạn 6-36 tháng, đặc biệt kỳ hạn dài 36-60 tháng giảm tới 1 điểm %/năm. Eximbank cũng giảm 0,5 điểm%/năm với các kỳ hạn dài 18-36 tháng, đưa lãi suất cao nhất xuống còn khoảng 5,2-5,5%/năm, thấp hơn đáng kể so với mặt bằng chung trước đó""",
"2A, K12, A2B, 2A3, Km153+450, QL18, NTPA, 7h45, 20H45 20h45 thế kỷ XX khóa XIV",
"ngày 20/1 ngày 20/01/1998 từ 1/7 2/9" ,
# "Vụ việc đã khiến giao thông tại đây ùn tắc nhẹ Như Tiền Phong đã đưa tin, ngày 20/1 đại diện Sở GTVT TP Cần Thơ đã thông báo công văn của Bộ GTVT thống nhất miễn, giảm giá cho 972 phương tiện thuộc xã Tân Phú Thạnh, thị trấn Cái Tắc (thuộc tỉnh Hậu Giang) và 1.023 phương tiện thuộc các phường Ba Láng, phường Lê Bình, phường Thường Thạnh (quận Cái Răng, TP.Cần Thơ) khi qua trạm BOT Cần Thơ Phụng Hiệp.",
# "Công ty CP BOT Biên Cương sẽ cấp thẻ ưu tiên (tạm thới 3 tháng) để giảm giá dịch vụ sử dụng đường bộ đối với các chủ phương tiện có hộ khẩu ở TP Cẩm Phả.",
"Km153+450 và Km156+985 QL18",
# "Tuy nhiên, trong dịp Tết Nguyên Đán Mậu Tuất, từ 14-20.2.2018 (tức từ 30 đến hết mồng 5 Tết), sẽ miễn phí vé cho tất cả các phương tiện qua trạm thu phí QL 18, đoạn Hạ Long- Mông Dương.",
# "Trong giao dịch giấy viết tay về việc chuyển nhượng QSD đất giữa anh Tiến và gia đình bà Huệ tuy không đề cập đến thửa đất số 53 (nay là thửa đất số 44), tờ bản đồ số 26 nhưng gia đình bà Huệ lại thể hiện trên giấy viết tay là trên đất có nhà 3 tầng .",
# """Luật sư Phạm Thị Bích Hảo, Giám đốc Công ty luật TNHH Đức An trả lời bạn như sau: Theo thông tin bạn cung cấp gia đình có mảnh đất nông nghiệp mang tên bố bạn.
# Nếu quyền sử dụng đất có trong thới kỳ hôn nhân thì là tài sản chung vợ chồng nếu không có căn cứ chứng minh đó là tài sản riêng.
# Khi bố bạn mất không để lại di chúc, di sản bố bạn để lại là 1/2 quyền sử dụng đất, mẹ bạn 1/2 quyền sử dụng đất.""",
"Bộ GD&ĐT",
'Bán ô tô không phải thông báo với công an Đây là nội dung đáng chú ý quy định tại Thông tư 64/2017/TT-BCA sửa đổi, bổ sung một số điều của Thông tư 15/2014/TT-BCA về đăng ký xe, có hiệu lực từ ngày 12/2/2018.',
'Ảnh: Hoàng Yến Tháng 6-2016, CQĐT kết luận điều tra vụ án nhưng VKSND TP yêu cầu điều tra bổ sung làm rõ hành vi của hai người môi giới thế chấp xe là Huỳnh Thị Thu Thủy và Huỳnh Khắc Đáng, nếu đủ căn cứ thì khởi tố hình sự.',

"UBND TP.HCM ban hành công văn",


"20-60 trẻ/hộ, 20-60",
"1-4/7/2006, 1-4/7, 4-7/2009, 31/12/2004",
"1-4.7.2006, 1-4.7, 4-7.2009, 31.12.2004",
"24/6/1967 - 24/6/2017",
'quý III/2017, quý 3/2017, quý III-2017, Quý III.2017 QUÝ IV-2017',
'mức 3 triệu đồng/tháng/người/xã',
"chiều cao 1,84m, 1,84 m",
"quãng đường dài 50,25km, 50,25km 50.25km 50.25 km 12.34",
"lãi suất 5%/tháng, 100.000 đồng/lượt",
"mức lương cơ sở/trẻ/tháng",        
"giao/nhận",
    "32,4%, 0,73%, 0,989%, 14,9492% 14,949 15,9595",
    "32.4%, 0.73%, 0.989%, 14.9492%",
    "32,4% 32.4% 32.4 % 32,4 %",
    "0,73m2, 0,73 m2, 0,73 %, 0,73%, 0,73 kg",
    "0.73m2, 0.73 m2, 0.73 %, 0.73%, 0.73 kg, 0,73, 3.14, 3.145, 3,14, 3,145, 1,000,000, 1.000.000",

    # SENTENCES
    "Từ năm 2017 đến nay, PC67 trích xuất 49.704 trường hợp vi phạm nhưng mới chỉ xử phạt được 16.106 trường hợp (đạt tỷ lệ 32,4%).",
    
    # "1/1/2005, Tháng 5/2016, tháng 4-2016, tháng 7.2017 "
    "Tháng 10-2016, VKSND TP ban hành cáo trạng truy tố bà Hoa tội trộm cắp tài sản theo khoản 4 Điều 138 BLHS 1999 (hình phạt từ 12 năm đến tù chung thân)",
    # "Số liệu được công bố hồi cuối tuần trước cho thấy lạm phát Mỹ đạt 1,4% trong tháng 5 so với cách đây một năm, dước mức mục tiêu của Fed là 2%.",
    # "Công trình Pắc-Beng có công suất thiết kế 912 MW, điện lượng 4,765 GWh, chủ yếu xuất khẩu sang Thái Lan (90%).", # YES

    # MEASURE

    # "Từ 2-3 đến 10-3-2026 nhiệt độ đạt từ 7-10 độ.",
    # "giá nhà dao động 45-55 triệu đồng/m2, 50 - 60 tỷ",
    # "Từ 2-3 đến 10-3-2026, nhiệt độ đạt từ 7-10, khoảng 2-5g, 5-6ft 15-18kg 7-9 kg",
    # "Chạy quá tốc độ quy định trên 35 km/h bị phạt 7-8 triệu 7-8 tỷ 7-8 nghìn 7-8 chiếc.",
    # "kế toán trưởng Công ty 1-5",
    # "TN&MT, PL&XH",
    # "1,000,000, 1,000,000 đồng",
    # "20-30, 20-30 tỷ đồng",
    # "4-5/2026, từ 2-7/12 từ 2-7.12",
    # "từ 24/1-6/2",
    # "114 234",
    # "1,000,000,000, 5.152.525.252",
    # '0,73 phần trăm, 0,44%, 0.73%, 2-4%, 50%',

    # "0.73 USD, 0,73 tỷ đồng",
    # "0,73",
    # "3.14",
    # "3,14",
    # "0.73, 0,73, 3.14, 3.145, 3,14, 3,145, 1,000,000, 1.000.000",
    # 'Việt Nam-Campuchia, Việt Nam - Campuchia 24/6/1967 - 24/6/2017',
    # "0.73, 0,73, 3.14, 3.145, 3,14, 3,145, 1,000,000, 1.000.000, 418m2, 5.503m2, 73,5m2, 2.482.000",

    # DATE
    "1-4/7/2006, 1-4/7, 4-7/2009, 31/12/2004",
    # "từ 14-20/2/2026, giá xăng tăng 5.000 đồng/lít",
    # "lãi suất 5%/tháng, 100.000 đồng/lượt",
    "từ 14-20.2.2018 , từ 14-20/2/2018  tháng 11-2013",
    "đến trước 1/7/2014, trước 2/7, sau 3/8",
    # "Có hiệu lực từ 1/2, 1/2 quyền sử dụng đất",
    # "Sinh nhật tôi là 01-05-2000.",
    "4-5/2026, từ 2-7/12 từ 2-7.12",
    
    "Kết quả là 3.14.",
    "Đây là lần thứ 2 tôi đến đây.",
    
    "Số tài khoản là 123456789.",
    "Sự kiện diễn ra năm 2024.",
    
    "Hẹn gặp lúc 7h45.",
    "Tôi nghỉ vào chủ nhật.",
    "Doanh thu quý II tăng mạnh.",
    'Ông Nguyễn Duy Ngọc sinh năm 1964, quê ở Hưng Yên. Ông có trình độ chuyên môn Thạc sĩ Luật, là Ủy viên Trung ương Đảng khóa XIII, XIV; Ủy viên Bộ Chính trị khóa XIII, XIV.',
    # 'khóa XIII, XIV, XX;',
    # 'khóa XIII, XIV, XX'
]

# SAMPLE_INPUTS = [
#     "Giá cổ phiếu tăng từ $0.000045 lên $1,234.5678 trong 3.5×10^6 giao dịch.",
#     "I don't know why",
#     "Mã này là 192.16.2"
# ]

SCRIPT_DIR = Path(__file__).resolve().parent
TEXT_VERBALIZATION_DIR = SCRIPT_DIR.parent.parent
TENO_ROOT = TEXT_VERBALIZATION_DIR / "teno"
TENO_CACHE_DIR = SCRIPT_DIR / ".teno_cache"
TENO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

if str(TENO_ROOT) not in sys.path:
    sys.path.insert(0, str(TENO_ROOT))

import teno as teno_pkg

sys.modules.setdefault("nemo_text_processing", teno_pkg)

from teno.text_normalization.normalize import Normalizer

AFTER_TENO_IMPORT = perf_counter()

def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

@lru_cache(maxsize=None)
def get_normalizer(lang: str = "vi") -> Normalizer:
    overwrite_cache = env_flag("TENO_OVERWRITE_CACHE", default=False)
    print(f"[Teno cache] cache_dir={TENO_CACHE_DIR} overwrite_cache={overwrite_cache}")
    return Normalizer(
        input_case="cased",
        lang=lang,
        cache_dir=str(TENO_CACHE_DIR),
        overwrite_cache=overwrite_cache,
    )

def get_inputs():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return SAMPLE_INPUTS

def teno_normalize(text: str, lang: str = "vi") -> str:
    try:
        normalizer = get_normalizer(lang=lang)
        return normalizer.normalize(text)
    except Exception as e:
        return f"[ERROR: {e}]"

def teno_normalize_batch(texts, lang: str = "vi"):
    try:
        normalizer = get_normalizer(lang=lang)
        return normalizer.normalize_list(texts)
    except Exception:
        return [teno_normalize(text, lang=lang) for text in texts]

def main():
    main_start = perf_counter()
    texts = get_inputs()

    init_start = perf_counter()
    normalizer = get_normalizer(lang="vi")
    init_end = perf_counter()

    first_output = ""
    first_text_time = 0.0
    if texts:
        first_start = perf_counter()
        first_output = normalizer.normalize(texts[0])
        first_text_time = perf_counter() - first_start

    remaining_inputs = texts[1:] if len(texts) > 1 else []
    remaining_outputs = []
    remaining_time = 0.0
    if remaining_inputs:
        remaining_start = perf_counter()
        remaining_outputs = normalizer.normalize_list(remaining_inputs)
        remaining_time = perf_counter() - remaining_start

    outputs = [first_output] + remaining_outputs if texts else []
    total_main_time = perf_counter() - main_start

    print("\n===== Teno Normalization (Python API, Vietnamese) =====\n")
    print("Timing:")
    print(f"- Startup to Teno import: {AFTER_TENO_IMPORT - SCRIPT_START:.3f}s")
    print(f"- Startup to main(): {main_start - SCRIPT_START:.3f}s")
    print(f"- Normalizer init: {init_end - init_start:.3f}s")
    if texts:
        print(f"- First text normalize: {first_text_time:.3f}s")
    if remaining_inputs:
        print(f"- Remaining {len(remaining_inputs)} texts (batch): {remaining_time:.3f}s")
    print(f"- Total in main(): {total_main_time:.3f}s")
    print()

    for inp, out in zip(texts, outputs):
        print(f"Input:    {inp}")
        print(f"Output:   {out}")
        print("-"*60)

if __name__ == "__main__":
    main()


# rm -rf /home/nampv1/projects/tts/vnp_tts/data_prep/text_verbalization/misc/try/.teno_cache
# python /home/nampv1/projects/tts/vnp_tts/data_prep/text_verbalization/misc/try/<script_name>.py