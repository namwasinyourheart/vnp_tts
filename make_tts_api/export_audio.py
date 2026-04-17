import ffmpeg
from typing import Optional

try:
    from .detect_audio import detect_audio_bytes
except ImportError:
    from detect_audio import detect_audio_bytes


def _normalize_ffmpeg_input_format(format_name: Optional[str]) -> Optional[str]:
    if not format_name:
        return None

    primary = format_name.split(",")[0].strip()

    if primary == "wavpipe":
        return "wav"

    return primary


def export_audio_bytes(audio_bytes, input_format=None, audio_settings=None):
    if audio_settings is None:
        audio_settings = {}

    container = audio_settings.get("container")
    codec = audio_settings.get("codec")
    sample_rate = audio_settings.get("sample_rate")
    channels = audio_settings.get("channels")
    bitrate = audio_settings.get("bitrate")

    if container in {"s16le", "f32le"}:
        expected_codec = "pcm_s16le" if container == "s16le" else "pcm_f32le"
        if codec and codec != expected_codec:
            raise ValueError(
                f"Invalid output settings: container='{container}' requires codec='{expected_codec}', got codec='{codec}'. "
                "Prefer container='raw' and set codec to pcm_s16le/pcm_f32le."
            )

    if input_format is None:
        detected_format, _detected_codec = detect_audio_bytes(audio_bytes)
        input_format = _normalize_ffmpeg_input_format(detected_format)

    if input_format is None:
        raise ValueError("Unable to detect input_format from audio_bytes; please specify input_format explicitly")

    input_kwargs = {}
    if input_format:
        input_kwargs["format"] = input_format

    input_stream = ffmpeg.input("pipe:0", **input_kwargs)

    output_args = {}
    if container:
        if container == "raw":
            if codec == "pcm_s16le":
                output_args["format"] = "s16le"
            elif codec == "pcm_f32le":
                output_args["format"] = "f32le"
            else:
                raise ValueError(f"Unsupported codec for raw container: {codec}")
        else:
            output_args["format"] = container

    if codec:
        output_args["acodec"] = codec

    if sample_rate:
        output_args["ar"] = sample_rate

    if channels:
        output_args["ac"] = channels

    if bitrate:
        output_args["audio_bitrate"] = bitrate

    process = (
        ffmpeg
        .output(input_stream, "pipe:1", **output_args)
        .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    out, err = process.communicate(input=audio_bytes)

    if process.returncode != 0:
        raise RuntimeError(err.decode())

    return out


if __name__ == "__main__":

    # 1. đọc file từ disk
    with open("/media/nampv1/hdd/data/VoiceGarden/elevenlabs/25_male_north_middle_adv_tvc_nhat_nam_8s.mp3", "rb") as f:
        audio_bytes = f.read()


    audio_settings = {
        "container": "raw",
        "codec": "pcm_s16le", # 
        # "container": "mp3",
        # "codec": "libmp3lame", # 
        # "container": "wav",
        # "codec": "pcm_s16le",
        "sample_rate": 32000,
        "channels": 1,
        # "bitrate": "192k"
    }


    output_bytes = export_audio_bytes(
        audio_bytes,
        audio_settings=audio_settings
    )
    # ext = audio_settings["container"]
    ext = "pcm" #output.raw #ffplay -f s16le -ar 32000 -ch_layout mono your_file.pcm

    # 4. save ra disk
    with open(f"/home/nampv1/projects/tts/vnp_tts/toy_output/25_male_north_middle_adv_tvc_nhat_nam_8s_converted.{ext}", "wb") as f:
        f.write(output_bytes)