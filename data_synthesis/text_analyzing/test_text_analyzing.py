from text_analyzing import TextAnalyzer, detect_dates_nemo_text
from rich import print

if __name__ == "__main__":
    
    sentence = "Mới đây, Bộ Công an vừa ban hành Thông tư 64/2017/TT-BCA sửa đổi, bổ sung một số điều của thông tư 15/2014/TT-BCA cũ về đăng ký xe."
    sentence = "Quản lý, giám sát thu thuế casino Tại Thông tư số 146/2017/TT-BTC, có hiệu lực thi hành kể từ ngày 12/02/2018, Bộ Tài chính hướng dẫn về quản lý, giám sát việc thu thuế đối với hoạt động kinh doanh casino quy định tại Nghị định số 03/2017/NĐ-CP ngày 16/01/2017 của Chính phủ."
    sentence = "Ra mắt GPT-4"
    sentence = "Chưa làm hết trách nhiệm Theo tiến sĩ Phạm Sanh (chuyên gia lĩnh vực GTVT tại TP.HCM), nhiều nước áp dụng phương tiện kỹ thuật (trong đó có camera - PV) hơn 20 năm nay nhưng đa phần phạt nguội (tức phạt qua camera), ít phạt nóng; phạt nóng đối với những trường hợp nghiêm trọng."
    sentence = "Tháng 8-2014, bị cáo đem xe máy Honda LEAD của cháu ngoại cầm được 10 triệu đồng lấy tiền xài."
    sentence = "Ảnh: Hoàng Yến Tháng 6-2016, CQĐT kết luận điều tra vụ án nhưng VKSND TP yêu cầu điều tra bổ sung làm rõ hành vi của hai người môi giới thế chấp xe là Huỳnh Thị Thu Thủy và Huỳnh Khắc Đáng, nếu đủ căn cứ thì khởi tố hình sự."

    sentence = """64/2017/TT-BCA, _Theo Điều 156 BLDS 2015 Điều 3 Luật Tố tụng hành chính 2015, sự kiện bất khả kháng thường được hiểu là sự kiện xảy ra một cách khách quan mà sức người không thể kháng cự được như những hiện tượng do thiên nhiên gây ra (thiên tai) như lũ lụt, hỏa hoạn, bão, động đất, sóng thần ; hoặc là những hiện tượng xã hội như chiến tranh, bạo loạn, đảo chính, đình công, cấm vận, thay đổi chính sách của Chính phủ Còn trở ngại khách quan là những tình huống, hoàn cảnh khách quan, không do con người mong muốn.
Luật sư VŨ PHI LONG , nguyên Phó Chánh Tòa Hình sự TAND TP.HCM PHƯƠNG LOAN"""
    # sentence = "Cụ thể, thông tư này đã rút gọn dãy ký tự chữ cái trên biển chỉ còn từ A tới M (trước đây là từ A tới Z)."
    # sentence = "Tuy có tổ chức công khai thông báo nhưng không đảm bảo thời hạn 30 ngày trước ngày mở cuộc đấu giá theo quy định nên vi phạm điều 12 Nghị định số 05//2005/NĐ-CP ngày 18/1/2005."

    # sentence = "Theo CIT, Roman Filippov là Thiếu tá và là cựu phi công Ukraine đã gia nhập quân đội Nga sau khi Nga sáp nhập bán đảo Crimea."
    sentence = """
    Ngày 31/01/2026, Bưu điện TP Hà Nội đã tổ chức thành công Hội nghị Người lao động năm 2026. Hội nghị là hoạt động thường niên có ý nghĩa quan trọng, thể hiện tinh thần dân chủ, trách nhiệm và sự đồng hành giữa người sử dụng lao động và người lao động; qua đó tạo sự thống nhất, quyết tâm cao trong toàn thể CBCNV, NLĐ, hướng tới hoàn thành thắng lợi các mục tiêu sản xuất kinh doanh năm 2026 của Bưu điện TP Hà Nội.



Toàn cảnh hội nghị

Tham dự và chỉ đạo Hội nghị có đồng chí Trần Đức Thích – Chủ tịch Công đoàn Tổng công ty Bưu điện Việt Nam; ông Bùi Văn Hoàng – Bí thư Đảng ủy, Giám đốc Bưu điện TP Hà Nội; ông Trịnh Quang Chiến – Ủy viên Ban Chấp hành Công đoàn Bộ Khoa học và Công nghệ Việt Nam, Chủ tịch Công đoàn Bưu điện TP Hà Nội; cùng các đồng chí lãnh đạo chuyên môn, công đoàn và hơn 100 đại biểu đại diện cho gần 2.000 người lao động đang công tác tại Bưu điện TP Hà Nội.

Tại Hội nghị, các đại biểu đã được nghe báo cáo đánh giá kết quả thực hiện nhiệm vụ sản xuất kinh doanh, công tác lãnh đạo, chỉ đạo của Đảng bộ và hoạt động công đoàn, Đoàn TNCS Hồ Chí Minh năm 2025 với nhiều kết quả ấn tượng: Chất lượng dịch vụ vận hành của Bưu điện TP Hà Nội đã có cải tiến rõ rệt khi vươn lên một trong 5 đơn vị dẫn đầu cùng nhiều chỉ số xếp thứ 1,2 trong toàn Tổng công ty; Tổ chức thành công Đại hội Đảng bộ Bưu điện TP Hà Nội, Đại hội Công đoàn, Đại hội Đoàn TNCS Hồ Chí Minh nhiệm kỳ 2025-2030; Giám đốc Bưu điện TP Hà Nội được Công đoàn Tổng công ty tin tưởng giao nhiệm vụ Cụm trưởng cụm Công đoàn số 1 nhiệm kỳ 2025-2030; Chủ tịch Công đoàn Bưu điện TP Hà Nội tiếp tục được tái cử tham gia BCH Công đoàn Khoa học và Công nghệ Việt Nam nhiệm kỳ 2025-2030; Thực hiện đầy đủ, kịp thời các chế độ, chính sách đối với người lao động; Thực hiện tốt quy chế dân chủ cơ sở, đối thoại tại doanh nghiệp; Xác định mục tiêu, nhiệm vụ của năm 2026.   



Đồng chí Trần Đức Thích – Chủ tịch Công đoàn Tổng công ty Bưu điện Việt Nam phát biểu chỉ đạo tại hội nghị

Phát biểu chỉ đạo tại Hội nghị, đồng chí Trần Đức Thích – Chủ tịch Công đoàn Tổng công ty Bưu điện Việt Nam ghi nhận và đánh giá cao những nỗ lực, cố gắng của tập thể lãnh đạo chuyên môn, công đoàn và người lao động Bưu điện TP Hà Nội trong việc duy trì tăng trưởng, ổn định sản xuất kinh doanh, bảo đảm việc làm và đời sống cho người lao động, đạt kết quả ấn tượng về chất lượng dịch vụ các công đoạn vận hành, qua đó khẳng định vai trò của Bưu điện TP Hà Nội là đơn vị đầu tàu trong toàn Tổng công ty.

Đồng chí biểu dương Bưu điện TP Hà Nội đã tổ chức Hội nghị Người lao động bài bản, nghiêm túc, đúng quy định, phát huy tốt quyền làm chủ của người lao động. Đồng thời, đề nghị đơn vị tiếp tục tập trung nâng cao năng suất lao động, nâng cao uy tín và sự phối hợp chặt chẽ với các Trung tâm Kinh doanh; chủ động tham gia sâu hơn vào các quy trình bán hàng, đẩy mạnh bán chéo dịch vụ, gia tăng doanh thu, tăng thu nhập cho người lao động. Bên cạnh đó, cần chú trọng nâng cao trình độ, kỹ năng cho đội ngũ CBCNV đáp ứng yêu cầu chuyển đổi số; quan tâm chăm lo đời sống, cải thiện môi trường làm việc; kịp thời tiếp thu các ý kiến, đề xuất chính đáng của người lao động, tạo động lực phấn đấu, quyết tâm hoàn thành các mục tiêu đề ra, hướng tới ổn định đời sống, tăng năng suất, tăng tiền lương cho người lao động.



Đồng chí Bùi Văn Hoàng – Bí thư Đảng ủy, Giám đốc Bưu điện TP Hà Nội phát biểu tại hội nghị

Tiếp thu ý kiến chỉ đạo của lãnh đạo Công đoàn Tổng công ty, đồng chí Bùi Văn Hoàng – Bí thư Đảng ủy, Giám đốc Bưu điện TP Hà Nội khẳng định đơn vị sẽ cụ thể hóa các nội dung chỉ đạo thành chương trình, kế hoạch hành động thiết thực. Giám đốc yêu cầu các yêu cầu các phòng chức năng Bưu điện TP Hà Nội khẩn trương tham mưu cho Giám đốc và Chủ tịch Công đoàn các giải pháp thiết thực nhằm giải quyết kịp thời các đề xuất, kiến nghị của người lao động tại các đơn vị; đồng thời tiếp tục hoàn thiện các quy định, cơ chế quản lý, đặc biệt là các cơ chế liên quan trực tiếp đến người lao động, giữ được người lao động gắn bó lâu dài, góp phần ổn định sản xuất kinh doanh và nâng cao chất lượng hoạt động toàn mạng lưới.

Tại hội nghị, Giám đốc và Chủ tịch Công đoàn Bưu điện TP Hà Nội và các đơn vị trực thuộc đã thực hiện ký cam kết thi đua quyết tâm hoàn thành toàn diện các nhiệm vụ kế hoạch SXKD năm 2026.

Đồng chí Giám đốc Bưu điện TP Hà Nội cũng yêu cầu các đơn vị tổ chức phổ biến, quán triệt đầy đủ Nghị quyết Hội nghị Người lao động năm 2026 đến toàn thể người lao động, đẩy mạnh công tác truyền thông, lan tỏa các định hướng chỉ đạo của Tổng công ty và Bưu điện TP Hà Nội; trên cơ sở đó cụ thể hóa các nhiệm vụ trọng tâm, xây dựng kế hoạch hành động phù hợp với điều kiện thực tế của từng đơn vị, quyết tâm hoàn thành toàn diện các mục tiêu, chỉ tiêu và cam kết thi đua đã đề ra, với khẩu hiệu hành động của năm 2026 là “Tăng tốc, bứt phá, dẫn đầu”, phấn đấu mục tiêu đưa chất lượng dịch vụ vận hành của Bưu điện TP Hà Nội dẫn đầu toàn Tổng công ty.



Trao giấy khen cho các cá nhân có thành tích xuất sắc trong công tác đấu tranh, phòng chống tội phạm lợi dụng mạng Bưu chính và phong trào toàn dân bảo vệ an ninh tổ quốc

Trong khuôn khổ Hội nghị, Bưu điện TP Hà Nội đã vinh dự được phối hợp cùng Phòng PA03 – Công an Thành phố Hà Nội tổ chức trao giấy khen của Giám đốc Công an TP Hà Nội cho các cá nhân có thành tích xuất sắc trong công tác đấu tranh, phòng chống tội phạm lợi dụng mạng Bưu chính và phong trào toàn dân bảo vệ an ninh tổ quốc. Hội nghị cũng trao Bằng khen của Bộ trưởng Bộ Khoa học và Công nghệ, Giấy khen của Bưu điện TP Hà Nội cho các tập thể, cá nhân tiêu biểu; đồng thời công bố các quyết định về luân chuyển, bổ nhiệm cán bộ, góp phần kiện toàn tổ chức bộ máy, đáp ứng yêu cầu nhiệm vụ trong giai đoạn phát triển mới.

Hội nghị Người lao động năm 2026 của Bưu điện TP Hà Nội đã diễn ra trong không khí dân chủ, đoàn kết, thống nhất cao, thể hiện rõ sự đồng hành giữa lãnh đạo và người lao động, tạo nền tảng quan trọng để Bưu điện TP Hà Nội tiếp tục khẳng định vai trò đơn vị đầu tàu, dẫn dắt, hoàn thành thắng lợi các mục tiêu sản xuất kinh doanh năm 2026 và những năm tiếp theo.

Một số hình ảnh tại hội nghị:
"""
    sentence = "Thông tư số 03/2024/TT-BTNMT, 12.9.20 của Bộ Tài nguyên và Môi trường được ban hành tháng 6 2024, tháng 7/2018, tháng 09.2023, 31/12 ngày 25/6"
    import time
    start = time.time()
    analyzer = TextAnalyzer()
    features = ["abbreviation", "date"]
    features = analyzer.analyze(sentence, features)
    end = time.time()
    print("Runtime: ", end - start)

    print(features)

    print(detect_dates_nemo_text(sentence))


    