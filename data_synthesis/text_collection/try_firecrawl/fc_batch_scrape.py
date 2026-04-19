from firecrawl import Firecrawl
from rich import print
import json

app = Firecrawl(api_key="fc-c8a4be9f60b64d7e91bf83b144ee5d6b")

url1 = "https://vietnampost.vn/vi/hoat-dong-nganh/buu-dien-thanh-pho-ha-noi-to-chuc-thanh-cong-hoi-nghi-nguoi-lao-dong-nam-2026"
url2 = "https://dantri.com.vn/kinh-doanh/vn-index-tang-gan-12-diem-co-phieu-vingroup-dan-dat-thi-truong-20260331155900368.htm"

urls = [
    url1,
    url2
]

job = app.batch_scrape(
    urls,
    formats=["markdown"],  # Hoặc ["html", "rawHtml", "screenshot"]
    # poll_interval=2,       # Kiểm tra status mỗi 2s
    # wait_timeout=120       # Timeout 120s
    # maxConcurrency=10,
)

# print(job)
all_results = [doc.model_dump() for doc in job.data]


with open(r"E:\projects\vnp_tts\data_synthesis\text_collection\try_firecrawl\all_results_sync.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)
print("Đã lưu JSON: all_results.json")

# print(job.status, job.completed, job.total)