import numpy as np


def test_export_audio_bytes():
    """
    Test export_audio_bytes by generating a 1-second sine wave,
    converting it with FFmpeg, and saving the result to a file.
    """

    duration = 1.0
    sample_rate = 24000
    freq = 440  # A4 tone

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # generate float32 mono waveform
    wav = 0.5 * np.sin(2 * np.pi * freq * t).astype(np.float32)

    audio_bytes = wav.tobytes()

    input_audio_settings = {
        "format": "f32le",
        "sample_rate": sample_rate,
        "channels": 1
    }

    output_audio_settings = {
        "container": "wav",
        "codec": "pcm_s16le",
        "sample_rate": sample_rate,
        "channels": 1
    }

    out_bytes = export_audio_bytes(
        audio_bytes,
        input_audio_settings,
        output_audio_settings
    )

    with open("test_output.wav", "wb") as f:
        f.write(out_bytes)

    print("Test complete: saved test_output.wav")