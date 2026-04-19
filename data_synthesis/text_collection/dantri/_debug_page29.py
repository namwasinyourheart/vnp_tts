import re, os
from urllib.request import Request, urlopen

ARTICLE_PAT = re.compile(r"/[^\"\'\s<>]+-(20\d{6})\d*\.htm", re.I)
OUT = r"E:\projects\vnp_tts\data_synthesis\text_collection\dantri\dbg.txt"

try:
    lines = []
    for page in [28, 29, 30]:
        url = f"https://dantri.com.vn/thoi-su/from/2026-04-10/to/2026-04-19/trang-{page}.htm"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urlopen(req, timeout=30).read()
        html = raw.decode("utf-8", "replace")
        dates = ARTICLE_PAT.findall(html)
        inrange = [d for d in dates if 20260410 <= int(d) <= 20260419]
        lines.append(f"PAGE {page}")
        lines.append(f"  raw_bytes={len(raw)}")
        lines.append(f"  html_len={len(html)}")
        lines.append(f"  has_article_tag={'<article' in html.lower()}")
        lines.append(f"  has_015E53={'015E53' in html}")
        lines.append(f"  total_date_urls={len(dates)}")
        lines.append(f"  inrange_date_urls={len(inrange)}")
        for needle in ["10/4/2026", "19/4/2026", "category-timeline_page"]:
            idx = html.find(needle)
            lines.append(f"  find('{needle}')={idx}")
            if idx >= 0:
                snip = html[max(0,idx-80):idx+80].replace("\n", " ")
                lines.append(f"  snippet={snip}")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
except Exception as e:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(f"ERROR: {e}")
