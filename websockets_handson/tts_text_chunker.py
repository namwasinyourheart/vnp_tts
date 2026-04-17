# from elevenlabs.realtime_tts import text_chunker

# def llm_tokens():
#     """Simulate LLM token stream."""
#     tokens = ["Hello", ", ", "how ", "are ", "you", "? ", "I'm ", "fine", "."]
#     for token in tokens:
#         yield token

# for chunk in text_chunker(llm_tokens()):
#     print(repr(chunk))
# Output:
# 'Hello, '
# 'how are you? '
# "I'm fine. "

import json
import websockets
from elevenlabs.realtime_tts import text_chunker

def get_llm_stream():
    text = "Các video mới được Lực lượng Phòng vệ Israel (IDF) công bố gần đây cho thấy dường như họ đã tấn công phải những mục tiêu giả của Iran, từ bệ phóng tên lửa, tiêm kích F-14 và F-4, trực thăng Mi-17 cho tới UAV."
    for word in text.split():
        yield word + " "

# # Use text_chunker as preprocessing before manual WebSocket send
# for chunk in text_chunker(get_llm_stream()):
#     # chunk is now aligned to sentence boundaries
#     print(f"Sending: {repr(chunk)}")

# ---------

# # Abstract algorithm
# splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")

# def text_chunker(text_stream):
#     buffer = ""
#     for fragment in text_stream:
#         if buffer.endswith(splitters):
#             yield buffer  # Emit at boundary
#             buffer = fragment
#         elif fragment.startswith(splitters):
#             yield buffer + fragment[0]  # Include boundary char
#             buffer = fragment[1:]
#         else:
#             buffer += fragment  # Continue buffering
#     if buffer:
#         yield buffer  # Flush remaining

# for chunk in text_chunker(get_llm_stream()):
#     # print(repr(chunk))
#     print(chunk)
    

# -------


def chunk_stream(text_stream):
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", )
    buffer = ""

    for fragment in text_stream:
        # Case 1: buffer already ends with a splitter
        if buffer and buffer.endswith(splitters):
            yield buffer # emit at boundary
            buffer = fragment

        # Case 2: fragment starts with a splitter
        elif fragment and fragment.startswith(splitters):
            yield buffer + fragment[0] # include boundary char
            buffer = fragment[1:]

        # Case 3: normal continuation
        else:
            buffer += fragment

    # flush remaining
    if buffer:
        yield buffer


# ---- Fake streaming source ----
import random
import time

def mock_llm_stream(text):
    i = 0
    while i < len(text):
        # # random token length giống tokenizer
        # step = random.randint(1, 6)
        # token = text[i:i+step]
        # i += step
        token = text[i]
        i += 1

        time.sleep(0.1)  # simulate network delay
        yield token

from llms import get_llm
from langchain_core.messages import HumanMessage

llm = get_llm()


message = HumanMessage(content="Explain LangChain streaming")


def llm_stream(message: HumanMessage):
    for chunk in llm.stream([message]):
        if chunk.content:        # bỏ qua empty deltas
            yield chunk.content


mock_text = "Hello, how are you today? I hope everything is going well. Let's start the meeting."
mock_text = "Well... I’m not sure. Maybe we should try again later?"

for segment in chunk_stream(mock_llm_stream(mock_text)):
    print(segment)
    print("-"*48)