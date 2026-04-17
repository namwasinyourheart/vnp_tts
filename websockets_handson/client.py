import asyncio
import websockets

async def run():
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as ws:

        # streaming input từng phần
        await ws.send("xin ")
        await ws.send("chao ")
        await ws.send("ban")

        # nhận streaming output
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=2)
                print("Received:", message)
            except asyncio.TimeoutError:
                break

asyncio.run(run())


