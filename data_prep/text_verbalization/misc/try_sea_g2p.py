from sea_g2p import Normalizer, G2P

normalizer = Normalizer(lang="vi")
g2p = G2P(lang="vi")

# Automatic parallel processing when list is passed
texts = ["Giá cổ phiếu tăng từ $0.000045 lên $1,234.5678 trong 3.5×10^6 giao dịch.", "Hãy gửi email đến support@example.com."]
texts = ["123,44867 chiếc"]
texts = ["tỉ lệ 13:00"]
normalized = normalizer.normalize(texts)
print(normalized)
#['giá cổ phiếu tăng từ không chấm không không không không bốn lăm <en>u s d</en> lên một nghìn hai trăm ba mươi bốn phẩy năm sáu bảy tám <en>u s d</en> trong ba chấm năm nhân mười mũ sáu giao dịch.', 'hãy gửi email đến <en>support</en> a còng <en>example</en> chấm com.']
phonemes = g2p.convert(normalized)
print(phonemes)
#['zˈaːɜ kˈo4 fˈiɛɜw t̪ˈaŋ t̪ˌy2 xˌoŋ tʃˈəɜm xˌoŋ xˌoŋ xˌoŋ xˌoŋ bˈoɜn lˈam jˈuː ˈɛs dˈiː lˈen mˈo6t̪ ŋˈi2n hˈaːj tʃˈam bˈaː mˈyəj bˈoɜn fˈəɪ4 nˈam sˈaɜw bˈa4j t̪ˈaːɜm jˈuː ˈɛs dˈiː tʃˈɔŋ bˈaː tʃˈəɜm nˈam ɲˈən mˈyə2j mˈu5 sˈaɜw zˈaːw zˈi6c.', 'hˈa5j ɣˈy4j ˈiːmeɪl ɗˌeɜn səpˈɔːɹt ˈaː kˈɔ2ŋ ɛɡzˈæmpəl tʃˈəɜm kˈɔm.']