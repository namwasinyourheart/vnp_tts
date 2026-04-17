import subprocess
import json
import tempfile
import os

def probe_audio(input_source):
    """
    input_source: bytes OR file path
    """

    if isinstance(input_source, (bytes, bytearray)):
        # phải ghi ra file tạm (ffprobe không đọc pipe tốt như ffmpeg)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(input_source)
            tmp_path = tmp.name

        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_streams",
                "-show_format",
                "-print_format", "json",
                tmp_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

        finally:
            os.remove(tmp_path)

    elif isinstance(input_source, str):
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_streams",
            "-show_format",
            "-print_format", "json",
            input_source
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

    else:
        raise TypeError("input_source must be bytes or file path")

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error: {result.stderr}")

    return json.loads(result.stdout)


def get_audio_settings(input_source):
    """
    Trả về các thông số chính của audio:
    - codec
    - sample_rate
    - channels
    - duration
    - bit_rate (nếu có)
    """

    probe = probe_audio(input_source)

    streams = probe.get("streams", [])
    if not streams:
        raise ValueError("No audio stream found")

    audio_stream = streams[0]
    format_info = probe.get("format", {})

    result = {
        "codec": audio_stream.get("codec_name"),
        "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream.get("sample_rate") else None,
        "channels": audio_stream.get("channels"),
        "duration": float(format_info.get("duration", 0)) if format_info.get("duration") else None,
        "bit_rate": int(format_info.get("bit_rate")) if format_info.get("bit_rate") else None,
    }

    # optional: bit depth (quan trọng với PCM)
    if audio_stream.get("bits_per_sample"):
        result["bit_depth"] = audio_stream.get("bits_per_sample")

    return result



def verify_audio_settings(input_source, expected):
    probe = probe_audio(input_source)

    streams = probe.get("streams", [])
    if not streams:
        raise ValueError("No audio stream found")

    audio_stream = streams[0]
    errors = []

    # codec
    if "codec" in expected:
        actual = audio_stream.get("codec_name")
        if actual != expected["codec"]:
            errors.append(f"codec mismatch: {actual} != {expected['codec']}")

    # sample rate
    if "sample_rate" in expected:
        actual = int(audio_stream.get("sample_rate", 0))
        if actual != expected["sample_rate"]:
            errors.append(f"sample_rate mismatch: {actual} != {expected['sample_rate']}")

    # channels
    if "channels" in expected:
        actual = audio_stream.get("channels")
        if actual != expected["channels"]:
            errors.append(f"channels mismatch: {actual} != {expected['channels']}")

    # optional: duration
    if "duration" in expected:
        actual = float(probe.get("format", {}).get("duration", 0))
        if abs(actual - expected["duration"]) > 0.1:
            errors.append(f"duration mismatch: {actual} != {expected['duration']}")

    if errors:
        raise ValueError("Audio verification failed:\n" + "\n".join(errors))

    return True


if __name__ == "__main__":
    wav_path = "/home/nampv1/projects/tts/vnp_tts/toy_output/25_male_north_middle_adv_tvc_nhat_nam_8s_converted.mp3"
    wav_path = "/home/nampv1/projects/tts/speech-synth-engine/gateway_output/xiaomi_clone_Dân_trí_-_Trong_kỳ_điều_hành_c_20260410_155644.wav"
    print(get_audio_settings(wav_path))
    # verify_audio_settings(
    #     wav_path,
    #     expected={
    #         "codec": "pcm_s16le",
    #         "sample_rate": 16000,
    #         "channels": 1
    #     }
    # )
    # print("Audio verification passed!")