import ffmpeg

def get_audio_metadata(file_path):
    probe = ffmpeg.probe(file_path)

    audio_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "audio"),
        None
    )

    if audio_stream is None:
        raise ValueError("No audio stream found")

    metadata = {
        "codec": audio_stream.get("codec_name"),
        "sample_rate": int(audio_stream.get("sample_rate", 0)),
        "channels": audio_stream.get("channels"),
        "bit_rate": int(audio_stream.get("bit_rate", 0)) if audio_stream.get("bit_rate") else None,
        "duration": float(probe["format"].get("duration", 0)),
        "container": probe["format"].get("format_name"),
    }

    return metadata

audio_path = "/home/nampv1/Downloads/pcm1.wav"

meta = get_audio_metadata(audio_path)
print(meta)