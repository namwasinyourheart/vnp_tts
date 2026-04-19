"""
Script to compare output of various Vietnamese text normalizer packages:
1. soe-vinorm: https://pypi.org/project/soe-vinorm/
2. vinorm: https://pypi.org/project/vinorm/
3. sea-g2p: https://github.com/pnnbao97/sea-g2p
4. Teno: local Vietnamese-only fork under ../../teno
"""

import sys
import os
from functools import lru_cache
from typing import List, Dict, Optional
import pandas as pd
from tabulate import tabulate


def preprocess_text(text: str) -> str:
    """Preprocess text before normalization"""
    # Add any preprocessing steps here if needed
    
    text = text.replace("–", "-").replace("—", "-")  # Replace em and en dash with hyphen
    
    return text


class NormalizerComparison:
    def __init__(self):
        self.normalizers = {}
        self.load_normalizers()

    def preprocess(self, text: str) -> str:
        """Preprocess text before normalization"""
        return preprocess_text(text)
    
    def load_normalizers(self):
        """Load all available normalizers"""
        
        # 1. Load soe-vinorm
        try:
            from soe_vinorm import SoeNormalizer
            soe_normalizer = SoeNormalizer()
            self.normalizers['soe_vinorm'] = {
                'func': lambda text: soe_normalizer.normalize(text),
                'name': 'soe-vinorm',
                'loaded': True
            }
            print("✓ Loaded soe-vinorm")
        except ImportError as e:
            self.normalizers['soe_vinorm'] = {
                'func': None,
                'name': 'soe-vinorm',
                'loaded': False,
                'error': str(e)
            }
            print(f"✗ Failed to load soe-vinorm: {e}")
        
        # 2. Load vinorm
        try:
            from vinorm import TTSnorm
            self.normalizers['vinorm'] = {
                'func': lambda text: TTSnorm(text),
                'name': 'vinorm',
                'loaded': True
            }
            print("✓ Loaded vinorm")
        except ImportError as e:
            self.normalizers['vinorm'] = {
                'func': None,
                'name': 'vinorm',
                'loaded': False,
                'error': str(e)
            }
            print(f"✗ Failed to load vinorm: {e}")
        
        # 3. Load sea-g2p
        try:
            from sea_g2p import Normalizer
            sea_normalizer = Normalizer(lang="vi")
            self.normalizers['sea_g2p'] = {
                'func': lambda text: sea_normalizer.normalize([text])[0] if isinstance(text, str) else sea_normalizer.normalize(text),
                'name': 'sea-g2p',
                'loaded': True
            }
            print("✓ Loaded sea-g2p")
        except ImportError as e:
            self.normalizers['sea_g2p'] = {
                'func': None,
                'name': 'sea-g2p',
                'loaded': False,
                'error': str(e)
            }
            print(f"✗ Failed to load sea-g2p: {e}")
        
        # 4. Load Teno (in-process with cache)
        try:
            teno_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../teno')
            )
            teno_cache_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '.teno_cache')
            )
            os.makedirs(teno_cache_dir, exist_ok=True)

            if teno_root not in sys.path:
                sys.path.insert(0, teno_root)

            import teno as teno_pkg

            sys.modules.setdefault("nemo_text_processing", teno_pkg)

            from teno.text_normalization.normalize import Normalizer as TenoNormalizer

            @lru_cache(maxsize=None)
            def get_teno_normalizer(lang: str = "vi") -> TenoNormalizer:
                return TenoNormalizer(
                    input_case="cased",
                    lang=lang,
                    cache_dir=teno_cache_dir,
                    overwrite_cache=False,
                )

            def teno_normalize(text: str, lang: str = "vi") -> str:
                return get_teno_normalizer(lang=lang).normalize(text)

            self.normalizers['teno'] = {
                'func': teno_normalize,
                'name': 'teno',
                'loaded': True
            }
            print("✓ Loaded teno (Python API, cached)")
        except Exception as e:
            self.normalizers['teno'] = {
                'func': None,
                'name': 'teno',
                'loaded': False,
                'error': str(e)
            }
            print(f"✗ Failed to load teno: {e}")
    
    def normalize_text(self, text: str, normalizer_key: str) -> Optional[str]:
        """Normalize text using specified normalizer"""

        text = self.preprocess(text)
        if normalizer_key not in self.normalizers:
            return None
        
        normalizer = self.normalizers[normalizer_key]
        if not normalizer['loaded']:
            return f"[ERROR: {normalizer.get('error', 'Not loaded')}]"
        
        try:
            result = normalizer['func'](text)
            return result
        except Exception as e:
            return f"[ERROR: {str(e)}]"
    
    def compare_single_text(self, text: str) -> Dict[str, str]:
        """Compare normalization results for a single text"""
        results = {'input': text}
        
        for key, normalizer in self.normalizers.items():
            results[normalizer['name']] = self.normalize_text(text, key)
        
        return results
    
    def compare_multiple_texts(self, texts: List[str]) -> pd.DataFrame:
        """Compare normalization results for multiple texts"""
        all_results = []
        
        for text in texts:
            result = self.compare_single_text(text)
            all_results.append(result)
        
        return pd.DataFrame(all_results)
    
    def print_comparison(self, texts: List[str], output_file: Optional[str] = None):
        """Print comparison results in a readable format"""
        print("\n" + "="*100)
        print("TEXT NORMALIZER COMPARISON")
        print("="*100 + "\n")
        
        for i, text in enumerate(texts, 1):
            print(f"\n{'─'*100}")
            print(f"Test Case {i}: {text}")
            print(f"{'─'*100}")
            
            results = self.compare_single_text(text)
            
            for key, normalizer in self.normalizers.items():
                name = normalizer['name']
                output = results.get(name, "N/A")
                status = "✓" if normalizer['loaded'] else "✗"
                print(f"\n{status} {name:15s}: {output}")
        
        print("\n" + "="*100 + "\n")
        
        # Save to file if specified
        if output_file:
            df = self.compare_multiple_texts(texts)
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"Results saved to: {output_file}")
    
    def get_summary(self) -> str:
        """Get summary of loaded normalizers"""
        loaded = [n['name'] for n in self.normalizers.values() if n['loaded']]
        failed = [n['name'] for n in self.normalizers.values() if not n['loaded']]
        
        summary = f"\nSummary:\n"
        summary += f"  Loaded: {len(loaded)}/{len(self.normalizers)}\n"
        if loaded:
            summary += f"  ✓ {', '.join(loaded)}\n"
        if failed:
            summary += f"  ✗ {', '.join(failed)}\n"
        
        return summary


def get_test_cases() -> List[str]:
    """Get comprehensive test cases for Vietnamese text normalization"""
    return [
        "quý III, năm LVIII, MCMXCIV năm 2025, thế kỷ XIX.",
        # Numbers
        "Tôi có 25 quyển sách.",
        "Kết quả là 3.14.",
        "Số tài khoản là 123456789.",
        
        # Ordinals
        "Đây là lần thứ 2 tôi đến đây.",
        "Tôi học lớp 10A.",
        
        # Dates
        "Sự kiện diễn ra năm 2024.",
        "Sinh nhật tôi là 01-05-2000.",
        "Ngày 10/2",
        
        # Time
        "Hẹn gặp lúc 7h45.",
        "Cuộc họp lúc 14:30.",
        
        # Temperature and measurements
        "Nhiệt độ từ 20-30 độ.",
        "60 km/h",
        "25Hz",
        "26 km²",
        "4.336km²",
        
        # Currency
        "Giá cổ phiếu tăng từ $0.000045 lên $1,234.5678.",
        "Chi phí là 100,000 VNĐ.",
        
        # Ranges
        "abc đến xyz",
        "tỉ lệ 13:00",
        
        # Mixed content
        "Doanh thu quý II tăng mạnh.",
        "Trên cổng thông tin điện tử của Công an TP.HCM.",
        "123,44867 chiếc",
        
        # Email and special characters
        "Hãy gửi email đến support@example.com.",
        
        # Scientific notation
        "3.5×10^6 giao dịch.",
    ]

def get_test_cases() -> List[str]:
    """Get comprehensive test cases for Vietnamese text normalization"""
    return [
        """Tổng thống Trump nói thỏa thuận hòa bình giữa Washington và Tehran đang "rất gần", thêm rằng Iran đã đồng ý bàn giao kho uranium làm giàu.""",
        'mức 3 triệu đồng/tháng/người',
        "giao/nhận, mức lương cơ sở/trẻ/tháng",
        "32,4% 32.4% 32.4 % 32,4 %",
        # sentence
        "Giá vàng giao ngay giảm 0,27% xuống còn 1.241,91 USD/ounce trong khi giá vàng giao trong tháng 8 giảm 3,5 USD xuống còn 1.242,3 USD/ounce.",
        "từ 24/1-6/2",  
        "mức lương cơ sở/trẻ/tháng",

        "Thông tư 64/2017",

        "Bộ Công an vừa ban hành Thông tư 64/2017/TT-BCA sửa đổi",

        # "tháng 4-2016",
        # 'Vào 3/4, Đêm 12/2026, vào 3/4 đội nghiên cứu đã hoàn thành báo cáo với 3/5 mẫu đạt chuẩn',
        # "13/5/2008",
        'từ 12.2.2018 đến 13/5/2008.',

        # "Chuyến thăm của Tổng Bí thư, Chủ tịch nước Tô Lâm và Phu nhân cùng đoàn đại biểu cấp cao Việt Nam diễn ra từ ngày 14 đến ngày 17-4, theo lời mời của Tổng Bí thư, Chủ tịch nước Trung Quốc Tập Cận Bình và Phu nhân.",
        # "Đúng 9h18 ngày 14/4 (giờ địa phương), chuyên cơ chở Tổng Bí thư, Chủ tịch nước Tô Lâm và Phu nhân cùng đoàn đại biểu cấp cao Việt Nam đã hạ cánh xuống Sân bay quốc tế Bắc Kinh, Trung Quốc.",
        'Liên minh Nghị viện thế giới (IPU-152) tại Istanbul, Thổ Nhĩ Kỳ, tiến hành một số hoạt động song phương tại Thổ Nhĩ Kỳ và thăm chính thức Cộng hòa Italy từ ngày 11-17/4/2026.',

        # "NĐ-CP Quyết định 749/QĐ-TTg năm 2020",
        # "Nhận lời mời của Chủ tịch Liên minh Nghị viện thế giới (IPU) Tulia Ackson, Tổng Thư ký IPU Martin Chungong, rạng sáng 11/4, Chủ tịch Quốc hội Trần Thanh Mẫn và Phu nhân cùng Đoàn đại biểu cấp cao Việt Nam đã rời Hà Nội lên đường tham dự Đại hội đồng lần thứ 152 của Liên minh Nghị viện thế giới (IPU-152) tại Istanbul, Thổ Nhĩ Kỳ, tiến hành một số hoạt động song phương tại Thổ Nhĩ Kỳ và thăm chính thức Cộng hòa Italy từ ngày 11-17/4/2026.",


        
        # "Thông tư số 64/2017/TT-BTNMT của Bộ Tài nguyên và Môi trường"
        # "Tuần trước, khi lệnh ngừng bắn mong manh xuất hiện, thị trường chứng khoán đã bật tăng. Chỉ số S&P 500 tăng hơn 3,5%, chứng khoán thị trường mới nổi tăng 7,4%, và bitcoin tăng gần 10%."
        # 'vào 3/4, ngày 1.1 ngày 1/1 ngày 1-1 tháng 12/2024, tháng 12-2024. tháng 12.2024 đội nghiên cứu đã hoàn thành báo cáo với 3/5 mẫu đạt chuẩn., tháng 12/2024, năm 2026 2026 1997 087',
        # 'năm 2024, tháng 12/2024',

        # ABBREVIATION

        # ALPHANUMERIC: chuỗi kết hợp cả chữ cái (alphabet) và chữ số (numeric)
        # "A1, 2B, A2B, 1A2, A1B2C3",
        # "số nhà 25A",

        # TIME
        # "9h, 9h14, 9h14p, 9h14p20s "
        # "09:00, 09:30, 09:30:02 "
        # "7:00 AM, 07:00 PM "
        # "7h–9h, 7h-9h, từ 7h-9h, 07:00–09:00, 07:00-09:00 ",
        # "7h ngày 12/5/2026, 07:00, 12-05-2026, 7 giờ ngày 12 tháng 5 năm 2026",

        # DATE
        "từ 24/1-6/2",
        # "từ 15-17/5",
        "15/5",
        "vào 15/5",
        "ngày 15.5, ngày 15-5",
        "8/4, ngày 8/4, đêm 8/4",
        "8/4 đêm 8/4 8-4 đêm 8-4 8.4",
        # "4/10",
        # "10 5/13",
        # "5/12 6/11 4/10",
        "4/10, 5/13",
        "từ ngày 14-17/4, từ 08/04/2026, từ 8/4, từ 8.4, từ 8-4, từ 12/2026 15-17/5, 15-5, 15/5, 15.5, 15.05, ngày 3-5, ngày 3.5",
        # "sáng 15/05, từ 12/2025, trưa 2/4/2001"
        # "2/2004"
        # "9/5/1994"
        # 'Vào 3/4, vào 3/4 đội nghiên cứu đã hoàn thành báo cáo với 3/5 mẫu đạt chuẩn',
        
        "đêm 5/12, 7/10, 11/11, 5/13 ngày 8/4, sáng 8/4, trưa 12/2025, vào 1/3/2020, 1/4/40, năm 25, 15-5, 15/5, 15.5, 15.0",
      
        # "1/1 2/2 3/3 4/4 5/5 6/6 7/7 8/8 9/9 10/10 11/11 12/12",

        # CARDINAL
        # '2024, 024, 113, 1000007, 1023097, 2071023097',
        # "4, 14, 24, 104, 1004, 1044",
        # "05, 5, 15, 105, 155, 1005, 1055",

        # ROMAN
        # prefix: chương, phần, mục, bài, tập, kỳ, mùa giải/mùa, số, cấp, giai đoạn
        # "quý II, thế kỷ XIV, chương III, phần VII, mục X, bài V, tập XXI",
        # "Vua Louis XIV, Vua Henry VIII, nhà V",
        # "tập V, nhà V"


        # '123, 026, 0913234678',
        # " Quy tắc 1/3 cũng rất hữu ích ",
        # "12/04, ngày 8/9, 07/2026",
        # "12-04, ngày 8-9, 07-2026",
        # "12.04, ngày 8.9, 07.2026",

        # "25:46 8:59",
        # "3/5/2100",
        # "Cuộc họp diễn ra lúc 8:30 ngày 20/10/2024, 01/11/2025",
        # "Hẹn gặp lúc 21:59, 22:35:22, 08:59:07",
        # "Sự kiện tổ chức vào 1/6, 14/5",
        # "Giai đoạn 2020-2023 tăng trưởng tốt hơn 2021-2019",
        # "Ở nhóm Big4, Vietcombank cho biết lợi nhuận trước thuế năm 2025 trên 45.000 tỷ đồng, đạt mức cao nhất lịch sử. Tính đến ngày 31/12/2025, tổng tài sản của ngân hàng này cũng đạt 2,48 triệu tỷ đồng, tăng gần 20% so với cuối năm 2024. Dư nợ cấp tín dụng đối với nền kinh tế đạt khoảng 1,66 triệu tỷ đồng, tăng hơn 15%."
    
    ]


def main():
    """Main function to run comparison"""
    print("Initializing normalizers...\n")
    
    comparator = NormalizerComparison()
    print(comparator.get_summary())
    
    # Get test cases
    test_cases = get_test_cases()
    
    # Run comparison
    comparator.print_comparison(
        test_cases,
        output_file='comparison_results.csv'
    )


if __name__ == "__main__":
    main()
