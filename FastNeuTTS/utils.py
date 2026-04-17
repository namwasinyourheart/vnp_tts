# import ffmpeg

# def export_audio_bytes(audio_bytes, input_format, input_sample_rate=None, input_channels=None, audio_settings={}):
#     container = audio_settings.get("container")
#     codec = audio_settings.get("codec")
#     sample_rate = audio_settings.get("sample_rate")
#     channels = audio_settings.get("channels")
#     bitrate = audio_settings.get("bitrate")

#     input_stream = ffmpeg.input(
#         "pipe:0",
#         format=input_format,
#         ar=input_sample_rate,
#         ac=input_channels
#     )
#     # ffmpeg.input cần biết format, sample_rate (ar), channels (ac) khi nhận raw audio từ numpy

#     output_args = {
#         "format": container
#     }

#     if codec:
#         output_args["acodec"] = codec

#     if sample_rate:
#         output_args["ar"] = sample_rate

#     if channels:
#         output_args["ac"] = channels

#     if bitrate:
#         output_args["audio_bitrate"] = bitrate

#     process = (
#         ffmpeg
#         .output(input_stream, "pipe:1", **output_args)
#         .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
#     )

#     out, err = process.communicate(input=audio_bytes)

#     if process.returncode != 0:
#         raise RuntimeError(err.decode())

#     return out


import ffmpeg


def export_audio_bytes(audio_bytes, input_audio_settings, output_audio_settings):
    """
    Convert or encode raw audio bytes using FFmpeg through stdin/stdout pipes.

    This function sends raw audio bytes to an FFmpeg subprocess via stdin,
    applies optional resampling, channel conversion, or codec encoding,
    and returns the processed audio bytes read from stdout.

    It is designed for in-memory audio pipelines (e.g., TTS, audio processing,
    streaming services) where writing intermediate files is undesirable.

    Parameters
    ----------
    audio_bytes : bytes
        Raw input audio data.

    input_audio_settings : dict
        Metadata describing the input audio format. Required when input is
        raw PCM (since FFmpeg cannot infer properties from raw bytes).

        Supported keys:
        - "format" (str): Input sample format (e.g., "f32le", "s16le", "s24le").
        - "sample_rate" (int): Input sample rate in Hz (e.g., 24000, 44100).
        - "channels" (int): Number of audio channels (e.g., 1 for mono, 2 for stereo).

        Example:
        {
            "format": "f32le",
            "sample_rate": 24000,
            "channels": 1
        }

    output_audio_settings : dict
        Configuration for the output audio stream.

        Supported keys:
        - "container" (str): Output container or raw format (e.g., "wav", "mp3", "flac", "s16le").
        - "codec" (str): Audio codec (e.g., "pcm_s16le", "libmp3lame", "aac").
        - "sample_rate" (int): Output sample rate in Hz.
        - "channels" (int): Number of output channels.
        - "bitrate" (str): Target audio bitrate (e.g., "128k", "64k").

        Example:
        {
            "container": "wav",
            "codec": "pcm_s16le",
            "sample_rate": 24000,
            "channels": 1
        }

    Returns
    -------
    bytes
        Encoded or converted audio bytes produced by FFmpeg.

    Raises
    ------
    RuntimeError
        If FFmpeg returns a non-zero exit code. The error message from
        FFmpeg stderr will be included.

    Notes
    -----
    - Uses FFmpeg pipes (`pipe:0` and `pipe:1`) to avoid filesystem I/O.
    - When input audio is raw PCM, `format`, `sample_rate`, and `channels`
      should usually be specified.
    - Output format must be explicitly defined when writing to stdout.

    Example
    -------
    Convert float32 TTS audio (24000 Hz mono) to WAV:

    >>> wav_bytes = export_audio_bytes(
    ...     audio_bytes,
    ...     {"format": "f32le", "sample_rate": 24000, "channels": 1},
    ...     {"container": "wav", "codec": "pcm_s16le"}
    ... )
    """
    validate_audio_output_settings(output_audio_settings)

    # ----- INPUT SETTINGS -----
    input_format = input_audio_settings.get("format")
    input_sample_rate = input_audio_settings.get("sample_rate")
    input_channels = input_audio_settings.get("channels")

    input_kwargs = {}

    if input_format:
        input_kwargs["format"] = input_format
    if input_sample_rate:
        input_kwargs["ar"] = input_sample_rate
    if input_channels:
        input_kwargs["ac"] = input_channels

    input_stream = ffmpeg.input("pipe:0", **input_kwargs)

    # ----- OUTPUT SETTINGS -----
    container = output_audio_settings.get("container")
    codec = output_audio_settings.get("codec")
    sample_rate = output_audio_settings.get("sample_rate")
    channels = output_audio_settings.get("channels")
    bitrate = output_audio_settings.get("bitrate")

    container = output_audio_settings.get("container")

    output_kwargs = {}

    if container:
        if container == "raw":
            if codec == "pcm_s16le":
                output_kwargs["format"] = "s16le"
            elif codec == "pcm_f32le":
                output_kwargs["format"] = "f32le"
            else:
                raise ValueError(f"Unsupported codec for raw container: {codec}")
        else:
            output_kwargs["format"] = container
    if codec:
        output_kwargs["acodec"] = codec
    if sample_rate:
        output_kwargs["ar"] = sample_rate
    if channels:
        output_kwargs["ac"] = channels
    if bitrate and container == "mp3":
        output_kwargs["audio_bitrate"] = bitrate

    process = (
        ffmpeg
        .output(input_stream, "pipe:1", **output_kwargs)
        .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    out, err = process.communicate(input=audio_bytes)

    if process.returncode != 0:
        raise RuntimeError(err.decode())

    return out


VALID_CONTAINERS = {"raw", "mp3", "wav"}

VALID_CODECS = {
    "raw": {"pcm_s16le", "pcm_f32le"},
    "wav": {"pcm_s16le", "pcm_f32le"},
    "mp3": {"libmp3lame"},
}

VALID_SAMPLE_RATES = {8000, 16000, 22050, 24000, 32000, 44100, 48000}
VALID_CHANNELS = {1, 2}

def validate_audio_output_settings(settings):

    container = settings.get("container")
    codec = settings.get("codec")
    sample_rate = settings.get("sample_rate")
    channels = settings.get("channels")
    bitrate = settings.get("bitrate")

    # container
    if container not in VALID_CONTAINERS:
        raise ValueError(f"Invalid container: {container}")

    # codec required
    if codec is None:
        raise ValueError("codec is required")

    if codec not in VALID_CODECS[container]:
        raise ValueError(
            f"Invalid codec '{codec}' for container '{container}'"
        )

    # sample rate
    if sample_rate and sample_rate not in VALID_SAMPLE_RATES:
        raise ValueError(f"Invalid sample_rate: {sample_rate}")

    # channels
    if channels and channels not in VALID_CHANNELS:
        raise ValueError(f"Invalid channels: {channels}")

    # mp3 rule
    if container == "mp3" and codec != "libmp3lame":
        raise ValueError("mp3 container requires codec 'libmp3lame'")

    # # bitrate rule
    # if bitrate and container != "mp3":
    #     raise ValueError("bitrate only supported for mp3")

import ffmpeg
import threading
from typing import AsyncGenerator


async def export_audio_stream(
    audio_generator,
    input_audio_settings,
    output_audio_settings
) -> AsyncGenerator[bytes, None]:

    input_kwargs = {
        "format": input_audio_settings.get("format"),
        "ar": input_audio_settings.get("sample_rate"),
        "ac": input_audio_settings.get("channels"),
    }

    output_kwargs = {}

    if output_audio_settings.get("container"):
        output_kwargs["format"] = output_audio_settings["container"]

    if output_audio_settings.get("codec"):
        output_kwargs["acodec"] = output_audio_settings["codec"]

    if output_audio_settings.get("sample_rate"):
        output_kwargs["ar"] = output_audio_settings["sample_rate"]

    if output_audio_settings.get("channels"):
        output_kwargs["ac"] = output_audio_settings["channels"]

    if output_audio_settings.get("bitrate"):
        output_kwargs["audio_bitrate"] = output_audio_settings["bitrate"]

        output_kwargs["audio_bitrate"] = f"{output_audio_settings['bitrate']}k"


    process = (
        ffmpeg
        .input("pipe:0", **input_kwargs)
        .output("pipe:1", **output_kwargs)
        .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    async def write_input():
        try:
            async for chunk in audio_generator:
                process.stdin.write(chunk)
        finally:
            process.stdin.close()

    thread = threading.Thread(target=lambda: None)
    thread.run = lambda: None
    thread = threading.Thread(target=lambda: None)

    import asyncio
    asyncio.create_task(write_input())

    while True:
        data = process.stdout.read(4096)
        if not data:
            break
        yield data

    process.wait()

    if process.returncode != 0:
        err = process.stderr.read().decode()
        raise RuntimeError(err)