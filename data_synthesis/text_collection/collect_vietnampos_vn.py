sentence = "Điển hình, [PVcomBank](https://dantri.com.vn/chu-de/pvcombank-ngan-hang-tmcp-dai-chung-viet-nam-4220.htm) đang áp dụng lãi suất đặc biệt 10%/năm cho kỳ hạn 12-13 tháng khi gửi tiền tại quầy, với điều kiện duy trì số dư tối thiểu 2.000 tỷ đồng."

sentence = """### [Loạt "ông lớn" ngân hàng tăng lãi suất: Gửi tiền ở đâu lời nhất?](https://dantri.com.vn/kinh-doanh/loat-ong-lon-ngan-hang-tang-lai-suat-gui-tien-o-dau-loi-nhat-20260320101245753.htm)"""

sentence = """
# [![Loạt điều hòa Casper 9000 BTU hạ giá sâu còn 4 triệu đồng đầu hè 2026](https://cdnphoto.dantri.com.vn/jUmvzfesEGuDdWNUGgkkP937tIw=/2026/03/09/loat-dieu-hoa-casper-9000-btu-ha-gia-sau-con-4-trieu-dong-dau-he-2026jpg-1773029897466.jpg)](https://websosanh.vn/tin-tuc/loat-dieu-hoa-casper-9000-btu-ha-gia-sau-con-4-trieu-dong-dau-he-2026-c41-2026030211290657.htm)[Loạt điều hòa Casper 9000 BTU hạ giá sâu còn 4 triệu đồng đầu hè 2026](https://websosanh.vn/tin-tuc/loat-dieu-hoa-casper-9000-btu-ha-gia-sau-con-4-trieu-dong-dau-he-2026-c41-2026030211290657.htm)
"""

# remove_markdown_links
# [text](url) -> text

import re
from typing import Iterable, Union


_MD_PARENS_URL = r"\((?:[^()]|\([^)]*\))*\)"


def clean_markdown(text: str):
    # match: [![TEXT](img)](link)[TEXT](link) -> keep 1 TEXT
    duplicate_pattern = rf"\[\!\[([^\]]+)\]{_MD_PARENS_URL}\]{_MD_PARENS_URL}\[\1\]{_MD_PARENS_URL}"
    text = re.sub(duplicate_pattern, r"\1", text)

    # remove image: ![alt](url) - handle data URLs with nested parentheses
    text = re.sub(rf"\!\[[^\]]*\]{_MD_PARENS_URL}", " ", text)
    
    # remove link nhưng giữ text: [text](url) - handle nested parentheses
    text = re.sub(rf"\[([^\]]+)\]{_MD_PARENS_URL}", r"\1", text)
    
    # normalize space
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def process(text: str):
    return clean_markdown(text)


def process_article(text: str, extract_main_only: bool = True, 
                    start_marker: str = None, #r'^#+\s*'
                    # end_marker: Union[str, Iterable[str]] = r'Bình luận\s*\(\d+\)'
                    end_marker: str = None,
                    skip_patterns: Union[str, Iterable[str], None] = None,
) -> str:
    """
    Extract and process main article content from heading to comment section.
    
    Args:
        text: Full markdown text
        extract_main_only: If True, extract only from heading to end_marker
        start_marker: Regex pattern for article start (default: heading lines)
        end_marker: Regex pattern for article end (default: Bình luận (n))
        skip_patterns: Regex pattern(s) for lines to drop from output
    
    Returns:
        Cleaned article text
    """
    if not extract_main_only:
        return process(text)

    def _normalize_pattern(pattern: str) -> str:
        p = pattern.strip()
        if len(p) >= 3 and (p.startswith("r'" ) or p.startswith('r"')) and p[-1] == p[1]:
            return p[2:-1]
        if len(p) >= 2 and ((p[0] == "'" and p[-1] == "'") or (p[0] == '"' and p[-1] == '"')):
            return p[1:-1]
        return p

    if end_marker is None:
        end_markers = []
    elif isinstance(end_marker, str):
        end_markers = [_normalize_pattern(end_marker)]
    else:
        end_markers = [_normalize_pattern(m) for m in end_marker]

    if skip_patterns is None:
        skip_list = []
    elif isinstance(skip_patterns, str):
        skip_list = [_normalize_pattern(skip_patterns)]
    else:
        skip_list = [_normalize_pattern(p) for p in skip_patterns]
    
    lines = text.strip().split('\n')
    result_lines = []
    in_article = False
    
    for line in lines:
        stripped = line.strip()
        cleaned = process(line)
        
        # Check for end marker on both raw and cleaned text
        if any(re.search(m, stripped) or re.search(m, cleaned) for m in end_markers):
            break
        
        # Check for start marker (heading with #)
        if not in_article:
            if start_marker is None or re.search(start_marker, stripped):
                in_article = True
        
        if in_article and cleaned:
            if skip_list and any(re.search(p, cleaned) for p in skip_list):
                continue
            result_lines.append(cleaned)
    
    return '\n\n'.join(result_lines)


# Example usage:
# full_text = results.markdown
# article = process_article(full_text, extract_main_only=True)
# print(article)

