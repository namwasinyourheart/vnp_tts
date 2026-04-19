from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

path = "yammdd/vietnamese-error-correction"

tokenizer = AutoTokenizer.from_pretrained(path)
model = AutoModelForSeq2SeqLM.from_pretrained(path)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

text = "cong ty trach nhiem huhu han"
text = "cham soc khach hang"
text = "hom nay toi rat vui khi hoc xu ly ngon ngu tu nhien"
out = pipe(text, max_new_tokens=256)

print(out[0]["generated_text"])
# Output: hôm nay anh buồn quá bé yêu ơi
