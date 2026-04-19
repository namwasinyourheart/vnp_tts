import re

import re

# VBQPPL_REGEX = re.compile(
#     r"\b(?P<so>\d{1,4})\/(?:(?P<nam>\d{4})\/)?"
#     r"(?:"
#         # dạng có dấu -
#         r"(?P<loaivanban>NĐ|NQ|QĐ|TT|TTLT|VBHN|CT|CĐ|KL)-"
#         r"(?P<coquan1>CP|TTg|UBTVQH|QH|HĐND|UBND|B(?:CA|QP|TC|YT|GDĐT|KHĐT|NNPTNT|TNMT|LĐTBXH|NV|TP|VHTTDL|TTTT))"
#         r"|"
#         # dạng không có dấu -, ví dụ UBTVQH13
#         r"(?P<coquan2>UBTVQH\d+|QH\d+)"
#     r")\b"
# )

# def extract_vbqppl(text: str):
#     """
#     Trích xuất số và ký hiệu văn bản quy phạm pháp luật từ text.
    
#     Returns:
#         List[dict]: mỗi phần tử gồm so, nam, loaivanban, coquan
#     """
#     results = []
    
#     for match in VBQPPL_REGEX.finditer(text):
#         coquan = match.group("coquan1") or match.group("coquan2")
        
#         results.append({
#             "so": match.group("so"),
#             "nam": match.group("nam"),
#             "loaivanban": match.group("loaivanban"),
#             "coquan": coquan,
#             "full": match.group(0)
#         })
    
    # return results


import re

VBQPPL_REGEX = re.compile(
    r"\b(?P<so>\d{1,4})\/(?:(?P<nam>\d{4})\/)?"
    r"(?:(?P<loaivanban>[A-ZĐ]{1,6})-)?"
    r"(?P<coquan>[A-ZĐ]{2,}(?:\d+)?(?:-[A-ZĐ]{2,}(?:\d+)?)*)\b"
)

def extract_vbqppl(text: str):
    results = []
    
    for match in VBQPPL_REGEX.finditer(text):
        results.append({
            "so": match.group("so"),
            "nam": match.group("nam"),
            "loaivanban": match.group("loaivanban"),
            "coquan": match.group("coquan"),
            "full": match.group(0)
        })
    
    return results



if __name__ == "__main__":
    # text = "Nghị định 123/2023/NĐ-CP"
    text = "Nội dung trong Thông tư 64/2017 đã bỏ quy định"
    text = "Tại Thông tư số 146/2017/TT-BTC, có hiệu lực thi hành kể từ ngày 12/02/2018, Bộ Tài chính hướng dẫn về quản lý, giám sát việc thu thuế đối với hoạt động kinh doanh casino quy định tại Nghị định số 03/2017/NĐ-CP ngày 16/01/2017 của Chính phủ"
    # text = "tại Thông tư 64/2017/TT-BCA sửa đổi"
    # text = "Nghị quyết 1211/2016/UBTVQH13"
    text = "Thông tư liên tịch 01/2017/TTLT-VKSNDTC-TANDTC-BCA-BTP"
    print(extract_vbqppl(text))
