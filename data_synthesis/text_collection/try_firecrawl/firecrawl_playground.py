# pip install firecrawl-py
from firecrawl import Firecrawl
from rich import print

app = Firecrawl(api_key="fc-c8a4be9f60b64d7e91bf83b144ee5d6b")

# Scrape a website:
url = "https://vietnampost.vn/vi/hoat-dong-nganh/buu-dien-thanh-pho-ha-noi-to-chuc-thanh-cong-hoi-nghi-nguoi-lao-dong-nam-2026"
url = "https://dantri.com.vn/kinh-doanh/vn-index-tang-gan-12-diem-co-phieu-vingroup-dan-dat-thi-truong-20260331155900368.htm"
url = "https://dantri.com.vn/kinh-doanh/chung-khoan-giam-khoi-ngoai-xa-manh-fpt-20260330152313272.htm"

url = "https://dantri.com.vn/kinh-doanh/gia-vang-mieng-dao-chieu-tang-15-trieu-dongluong-20260330092043293.htm"
url = "https://dantri.com.vn/kinh-doanh/lai-dac-biet-cham-moc-10nam-ngan-hang-hut-manh-dong-von-dau-tu-20260330100250359.htm"
url = "https://dantri.com.vn/kinh-doanh/sau-lenh-phong-toa-cua-ong-trump-the-gioi-co-cai-nghien-duoc-hormuz-20260413052024705.htm"

url = "https://dantri.com.vn/kinh-doanh/hsbc-viet-nam-bao-lai-thap-nhat-4-nam-thu-lao-nhan-vien-cao-bat-ngo-20260413152937083.htm"

url = "https://dantri.com.vn/the-gioi/chay-nha-kho-giay-ve-sinh-phuc-vu-50-trieu-nguoi-o-california-my-20260409161355033.htm"

url = 'https://vnexpress.net/ancelotti-xin-y-kien-tong-thong-brazil-ve-viec-goi-neymar-5062873.html'

url = "https://vnexpress.net/ky-an-cau-be-bi-troi-trong-dam-chay-o-can-ho-chung-cu-5063339.html"

# DU LỊCH
url = "https://vnexpress.net/trung-quoc-thi-truong-khach-quoc-te-lon-nhat-cua-du-lich-viet-5062090.html"


# GIÁO DỤC
url = "https://dantri.com.vn/giao-duc/thu-khoa-bac-si-noi-tru-ke-trai-nghiem-dung-8-tieng-moi-ngay-o-phong-kham-20260410162120422.htm"

url = "https://dantri.com.vn/giao-duc/vu-148-tre-nghi-ngo-doc-con-hon-200-em-chua-tro-lai-truong-20260410141209142.htm"

url = "https://vnexpress.net/bau-duc-khong-thieu-tien-khi-dau-tu-20-000-ha-ca-phe-5063556.html"

url = "https://dantri.com.vn/thoi-su/thu-tuong-giao-nhiem-vu-ve-cai-cach-chinh-sach-tien-luong-bao-hiem-xa-hoi-20260417132819321.htm"

# url = "https://vnexpress.net/trung-quoc-thi-truong-khach-quoc-te-lon-nhat-cua-du-lich-viet-5062090.html"

# url = "https://vnexpress.net/can-ho-90-m2-o-tp-hcm-lam-moi-khong-gian-nho-nghe-thuat-thi-giac-hy-lap-5063196.html"

# url = "https://vnexpress.net/tong-bi-thu-chu-tich-nuoc-can-38-trieu-ty-dong-cho-giai-doan-phat-trien-moi-5061727.html"

# url = "https://vnexpress.net/co-phieu-nhom-vingroup-noi-song-5063238.html"

# url = "https://vnexpress.net/lam-dung-do-uong-giai-nhiet-mua-he-gay-hai-than-5062722.html"
# url = "https://vnexpress.net/bac-si-canh-bao-nguy-hiem-chet-nguoi-khi-lam-dung-vitamin-5062411.html"

# url = "https://vnexpress.net/ipad-air-m4-hieu-nang-macbook-tren-may-tinh-bang-5063087.html"

# url = "https://vietnampost.vn/vi/tem-buu-chinh-/buu-chinh-hoang-gia-anh-phat-hanh-tem-ve-bo-phim-chua-te-nhung-chiec-nhan"


# url = "https://vietnampost.vn/vi/hoat-dong-nganh/buu-dien-viet-nam-dong-hanh-cung-sinh-vien-dai-hoc-phuong-dong-tren-hanh-trinh-ket-noi-tri-thuc"

results = app.scrape(
    url,
    only_main_content=True,
    parsers=["pdf"],
)
print(results.metadata)

from collect_vietnampos_vn import process, process_article

if results.html:
    with open("/home/nampv1/projects/tts/vnp_tts/data_synthesis/text_collection/results_html.html", "w", encoding="utf-8") as f:
        f.write(results.html)
    print("Saved results.html -> results_html.html")

# print(results)
text = results.markdown

# print("Markdown:")
# print(text)
# print("=" * 80)

# Option 1: Process line by line (old way)
# lines = re.split(r'\n+', text)
# for line in lines:
#     print(line)
#     print(process(line))
#     print("-" * 80)

# Option 2: Extract main article content only
# article = process_article(text, extract_main_only=True)
# article = process_article(
#     text, 
#     extract_main_only=True,
#     # end_marker=r"Tin liên quan",
#     # end_marker=r'^(Trở lại\s+.+?)\1$'
#     # end_marker = r'####'
#     end_marker=r'^#### .+'
# )

article = process_article(
    text,
    extract_main_only=True,
    # end_marker=r'^#### .+',
    # skip_patterns=[
    #     r'^VNE$',                       # source tag
    #     r'^## .+',                      # duplicate h2 heading
    #     r'^- Chia sẻ bài viết',         # share links
    #     r'^- Ý kiến',                   # comment link
    #     r'^- \d+$',                     # standalone number (comment count)
    #     r'^\d+$',                       # standalone number
    # ],
)

# print(article)