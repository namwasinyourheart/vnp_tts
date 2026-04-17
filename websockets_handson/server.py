import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


@app.websocket("/sentence_splitter")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            # Nhận từng chunk text từ client
            text_chunk = await websocket.receive_text()

            # Giả lập xử lý streaming (ví dụ: viết hoa từng phần)
            # for char in text_chunk:
            #     await asyncio.sleep(0.05)  # giả lập delay
            #     await websocket.send_text(char.upper())

            await websocket.send_text(text_chunk.upper())

    except WebSocketDisconnect:
        print("Client disconnected")

@app.websocket("/upper")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            # Nhận từng chunk text từ client
            text_chunk = await websocket.receive_text()

            # Giả lập xử lý streaming (ví dụ: viết hoa từng phần)
            # for char in text_chunk:
            #     await asyncio.sleep(0.05)  # giả lập delay
            #     await websocket.send_text(char.upper())

            await websocket.send_text(text_chunk.upper())

    except WebSocketDisconnect:
        print("Client disconnected")