from firecrawl import Firecrawl
from rich import print
import time
import json


app = Firecrawl(api_key="fc-c8a4be9f60b64d7e91bf83b144ee5d6b")

url1 = "https://vietnampost.vn/vi/hoat-dong-nganh/buu-dien-thanh-pho-ha-noi-to-chuc-thanh-cong-hoi-nghi-nguoi-lao-dong-nam-2026"
url2 = "https://dantri.com.vn/kinh-doanh/vn-index-tang-gan-12-diem-co-phieu-vingroup-dan-dat-thi-truong-20260331155900368.htm"

urls = [
    url1,
    url2
]

job = app.start_batch_scrape(
    urls, 
    formats=["markdown"],
    # maxConcurrency=10 # batch_size song song
)

print(f"Job ID: {job.id}")  # Dùng để poll
results = []


# Poll status + results
while True:
    status = app.get_batch_scrape_status(job.id)
    print(f"Progress: {status.completed}/{status.total}, Status: {status.status}")
    
    if status.status == "completed":
        # results = status.data  # Full results ở đây!
        all_results = [doc.model_dump() for doc in status.data]
        # print("Results:", results)
        break
    elif status.status in ["failed", "error"]:
        print("Error:", status.error)
        break
    
    time.sleep(2)  # Poll mỗi 2s

with open(r"E:\projects\vnp_tts\data_synthesis\text_collection\try_firecrawl\all_results_async.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)
print("Đã lưu JSON: all_results_async.json")


