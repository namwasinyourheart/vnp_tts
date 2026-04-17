import re
import time
import torch
import asyncio
import numpy as np
from typing import Optional
from NeuTTS.engine import TTSEngine
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.responses import StreamingResponse
from pydub import AudioSegment
from io import BytesIO
from utils import export_audio_bytes, export_audio_stream

try:
    tts_engine = TTSEngine(model="pnnbao-ump/VieNeu-TTS", espeak_lang="vi")
    user_voice_map = {}
    print("✅ TTSEngine loaded successfully.")
except Exception as e:
    print(f"❌ Error loading TTSEngine: {e}")
    tts_engine = None

app = FastAPI(title="Streaming TTS Service", version="1.0")

@app.get("/set_voice/", summary="Register a voice file and get a unique User ID.")
async def set_voice(
    audio_file: str = Query(default="/media/nampv1/hdd/data/VoiceGarden/elevenlabs/13_female_north_young_story_tuyet_trinh_4s.mp3", description="The filename of the custom reference audio for the voice."),
    transcript: str = Query(default="đoàn kết thì sống, chia rẽ thì chết, một lòng một dạ", description="The transcript of the reference audio for voice cloning."),
    user_id: Optional[str] = Query(None, description="Optional: A preferred unique User ID.")
):
    """
    Registers a new speaker voice using a reference audio file. 
    It assigns or uses a unique User ID for this voice profile.

    This is the function that calls `tts_engine.add_speaker(audio_file)`.
    """
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS Engine is not available.")

    try:
        # The engine handles creating a unique ID if one isn't provided/valid.
        final_user_id = tts_engine.add_speaker(audio_file, transcript)
        user_voice_map[final_user_id] = audio_file # Store the mapping

        return {
            "message": "Speaker voice registered successfully.",
            "user_id": final_user_id,
            "audio_file": audio_file,
            "transcript": transcript
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register speaker: {e}")


async def stream_audio_generator(input_text: str, user_id: str, display_audio: bool):
    """
    An asynchronous generator that yields converted 16-bit PCM audio chunks.
    """
    if tts_engine is None:
        raise RuntimeError("TTS Engine is not initialized.")

    try:
        async for wav_float32 in tts_engine.stream_audio(input_text, user_id, display_audio=display_audio):
            # 1. Convert float32 array (-1.0 to 1.0) to int16 PCM (-32768 to 32767)
            wav_int16 = (wav_float32 * 32767).astype(np.int16)

            # 2. Convert the int16 NumPy array to raw bytes
            yield wav_int16.tobytes()

    except Exception as e:
        print(f"Error during audio generation: {e}")
        pass


@app.post("/v1/audio/speech", summary="Stream TTS audio (OpenAI compatible).")
async def tts_stream(
    input: str = Body(..., embed=True, description="The text to generate audio for."),
    voice: str = Body(..., embed=True, description="The 'voice' maps to our custom speaker user_id."),
    model: str = Body("tts-1", embed=True, description="Placeholder model name."), 
    response_format: str = Body("pcm", embed=True, description="Desired audio format.") 
):
    # In your logic, map the 'voice' back to your 'user_id'
    ## model and response format do not matter currently
    user_id = int(voice)
    try:
        audio_generator = stream_audio_generator(
            input_text=input,
            user_id=user_id,
            display_audio=False
        )

        # ===== RETURN RAW PCM =====
        if response_format == "pcm":
            return StreamingResponse(
                audio_generator,
                media_type="application/octet-stream"
            )

        # ===== RETURN MP3 44.1kHz 128kbps =====
        elif response_format == "mp3_44100_128":
            pcm_bytes = b"".join([chunk async for chunk in audio_generator])

            audio = AudioSegment(
                data=pcm_bytes,
                sample_width=2,     # 16-bit
                frame_rate=24000,   # original SR
                channels=1          # mono
            )

            # Resample to 44.1kHz
            audio = audio.set_frame_rate(44100)

            mp3_buffer = BytesIO()
            audio.export(
                mp3_buffer,
                format="mp3",
                bitrate="128k"
            )
            mp3_buffer.seek(0)

            return StreamingResponse(
                mp3_buffer,
                media_type="audio/mpeg"
            )

        else:
            raise HTTPException(status_code=400, detail="Unsupported response_format")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TTS generation failed: {e}")

from pydantic import BaseModel
from typing import Optional


from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal


ContainerType = Literal["raw", "mp3", "wav"]

# RawCodec = Literal["pcm_s16le", "pcm_f32le"]
# WavCodec = Literal["pcm_s16le", "pcm_f32le"]
# Mp3Codec = Literal["libmp3lame"]


class OutputAudioSettings(BaseModel):

    container: ContainerType = "wav"
    codec: str = "pcm_s16le"

    sample_rate: int = 24000
    channels: int = 1
    bitrate: Optional[int] = None


    @model_validator(mode="after")
    def validate_audio_settings(self):

        raw_codecs = {"pcm_s16le", "pcm_f32le"}
        wav_codecs = {"pcm_s16le", "pcm_f32le"}
        mp3_codecs = {"libmp3lame"}

        if self.container == "raw":
            if self.codec not in raw_codecs:
                raise ValueError("raw container only supports PCM codecs")

            # if self.bitrate != 128:
            #     raise ValueError("bitrate is not supported for raw")

        elif self.container == "wav":
            if self.codec not in wav_codecs:
                raise ValueError("wav container only supports PCM codecs")

            # if self.bitrate != 128:
            #     raise ValueError("bitrate is not supported for wav")

        elif self.container == "mp3":
            if self.codec not in mp3_codecs:
                raise ValueError("mp3 container requires codec 'libmp3lame'")

        return self


    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v):
        if v is None:
            return v

        valid_rates = {8000, 16000, 22050, 24000, 32000, 44100, 48000}

        if v not in valid_rates:
            raise ValueError("unsupported sample_rate")

        return v


    @field_validator("channels")
    @classmethod
    def validate_channels(cls, v):
        if v not in {1, 2}:
            raise ValueError("channels must be 1 or 2")

        return v

    @field_validator("bitrate")
    @classmethod
    def validate_bitrate(cls, v):
        if v is None:
            return v

        if v not in {32, 64, 128, 192, 256}:
            raise ValueError("unsupported bitrate")

        return v

@app.post("/v1/tts/stream")
async def tts_stream(
    input: str = Body(...),
    voice: str = Body(...),
    model: str = Body("tts-1"),
    audio_settings: OutputAudioSettings = Body(default_factory=OutputAudioSettings)
):
    user_id = int(voice)
    audio_settings=audio_settings.model_dump()

    try:
        audio_generator = stream_audio_generator(
            input_text=input,
            user_id=user_id,
            display_audio=False
        )

        # collect PCM bytes
        pcm_bytes = b"".join([chunk async for chunk in audio_generator])


        # convert audio
        output_bytes = export_audio_bytes(
            audio_bytes=pcm_bytes,
            input_format="s16le",
            input_sample_rate=24000,
            input_channels=1,
            audio_settings=audio_settings
        )

        buffer = BytesIO(output_bytes)
        buffer.seek(0)

        media_type = f"audio/{audio_settings['container']}"

        return StreamingResponse(
            buffer,
            media_type=media_type
        )

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TTS generation failed: {e}")


@app.post("/v1/tts/stream1")
async def tts_stream1(
    input: str = Body(...),
    voice: str = Body(...),
    model: str = Body("tts-1"),
    audio_settings: OutputAudioSettings = Body(default_factory=OutputAudioSettings)
):

    user_id = int(voice)

    input_audio_settings = {
        "format": "s16le",
        "sample_rate": 24000,
        "channels": 1
    }

    output_audio_settings = audio_settings.model_dump()

    try:
        audio_generator = stream_audio_generator(
            input_text=input,
            user_id=user_id,
            display_audio=False
        )

        # collect PCM bytes
        pcm_bytes = b"".join([chunk async for chunk in audio_generator])


        # convert audio
        output_bytes = export_audio_bytes(
            pcm_bytes,
            input_audio_settings,
            output_audio_settings
        )

        buffer = BytesIO(output_bytes)
        buffer.seek(0)

        media_type = f"audio/{output_audio_settings['container']}"

        return StreamingResponse(
            buffer,
            media_type=media_type
        )

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TTS generation failed: {e}")



@app.post("/v1/tts/stream2")
async def tts_stream2(
    input: str = Body(...),
    voice: str = Body(...),
    model: str = Body("tts-1"),
    audio_settings: OutputAudioSettings = Body(default_factory=OutputAudioSettings)
):

    user_id = int(voice)

    input_audio_settings = {
        "format": "s16le",
        "sample_rate": 24000,
        "channels": 1
    }

    output_audio_settings = audio_settings.model_dump()

    async def pcm_generator():

        async for wav_chunk in stream_audio_generator(
            input_text=input,
            user_id=user_id,
            display_audio=False
        ):
            yield wav_chunk.astype("float32").tobytes()

    async def encoded_stream():

        async for chunk in export_audio_stream(
            pcm_generator(),
            input_audio_settings,
            output_audio_settings
        ):
            yield chunk

    media_type = f"audio/{output_audio_settings.get('container','wav')}"

    return StreamingResponse(
        encoded_stream(),
        media_type=media_type
    )



from fastapi import WebSocket, WebSocketDisconnect
from io import BytesIO
import json

@app.websocket("/v1/tts/ws")
async def tts_stream_ws(websocket: WebSocket):
    await websocket.accept()

    try:
        data = await websocket.receive_json()

        input_text = data["input"]
        voice = data["voice"]
        model = data.get("model", "tts-1")
        audio_settings = OutputAudioSettings(**data.get("audio_settings", {}))

        user_id = int(voice)
        audio_settings=audio_settings.model_dump()

        audio_generator = stream_audio_generator(
            input_text=input_text,
            user_id=user_id,
            display_audio=False
        )

        async for pcm_chunk in audio_generator:

            output_bytes = export_audio_bytes(
                audio_bytes=pcm_chunk,
                input_format="s16le",
                audio_settings=audio_settings
            )

            await websocket.send_bytes(output_bytes)

        await websocket.send_json({"event": "done"})

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        await websocket.send_json({
            "event": "error",
            "message": str(e)
        })


# curl -X 'POST' \
#   'https://e840-3-17-150-119.ngrok-free.app/v1/audio/speech' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "input": "Đất nước Việt Nam tươi đẹp",
#   "voice": "344318",
#   "model": "tts-1",
#   "response_format": "mp3_44100_128"
# }'

# Hello, I'm delighted to assist you with our voice services. Choose a voice that resonates with you and let's begin our creative audio journey together.
# /media/nampv1/hdd/data/VoiceGarden/elevenlabs/13-female-north-young-story-tuyet-trinh-eng-11s.mp3

# đoàn kết là sống, chia rẽ là chết, một lòng một dạ