from fastapi import FastAPI, WebSocket
import asyncio
import re

app = FastAPI()

SENTENCE_RE = re.compile(r'(.+?[.!?])(\s|$)')


# ===== Dummy Event =====
class DummyEvent:
    def __init__(self, type, text=""):
        self.type = type
        self.text = text


# ===== Dummy Event Stream =====
async def dummy_event_stream():
    chunks = [
        "Hello world. This is ",
        "a streaming example. ",
        "We split sentences ",
        "before sending to TTS!"
    ]

    for chunk in chunks:
        await asyncio.sleep(0.5)
        yield DummyEvent("agent_chunk", chunk)

    yield DummyEvent("agent_end")


# ===== Dummy TTS =====
class DummyTTS:
    async def send_text(self, text):
        print("TTS:", text)

        


async def process_upstream(event_stream, websocket, tts):
    buffer = ""

    async for event in event_stream:
        await websocket.send_json({
            "type": event.type,
            "text": event.text
        })

        if event.type == "agent_chunk":
            buffer += event.text

            while True:
                match = SENTENCE_RE.match(buffer)
                if not match:
                    break

                sentence = match.group(1)
                buffer = buffer[len(sentence):].lstrip()

                await tts.send_text(sentence)

        elif event.type == "agent_end":
            if buffer.strip():
                await tts.send_text(buffer)
                buffer = ""


# @app.websocket("/sentence_splitter")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     print("Client connected")

#     event_stream = dummy_event_stream()
#     tts = DummyTTS()

#     await process_upstream(event_stream, websocket, tts)

@app.websocket("/sentence_splitter")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    buffer = ""
    tts = DummyTTS()

    while True:
        text = await websocket.receive_text()

        buffer += text

        while True:
            match = SENTENCE_RE.match(buffer)
            if not match:
                break

            sentence = match.group(1)
            buffer = buffer[len(sentence):].lstrip()

            await tts.send_text(sentence)

            await websocket.send_json({
                "type": "sentence",
                "text": sentence
            })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    # async def main():
    #     async for event in dummy_event_stream():
    #         print(event.text)
    
    # asyncio.run(main())