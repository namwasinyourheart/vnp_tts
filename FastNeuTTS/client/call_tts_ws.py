import websockets
import json

async def run():
    uri = "ws://localhost:8000/v1/tts/ws"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "input": "Xin chào",
            "voice": "1",
            "model": "tts-1",
            "audio_settings": {
                "container": "wav"
            }
        }))

        while True:
            msg = await ws.recv()

            if isinstance(msg, bytes):
                print("audio chunk:", len(msg))
            else:
                data = json.loads(msg)
                if data["event"] == "done":
                    break
