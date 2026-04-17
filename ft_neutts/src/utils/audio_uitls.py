from IPython.display import Audio

def listen_audio(sample, audio_col="audio"):
    """
    Decode (if needed) and play an audio sample from a HuggingFace Dataset item.

    Supports both:
    1) Decoded audio dict: {"array": np.ndarray, "sampling_rate": int}
    2) Audio decoder object (requires .get_all_samples())

    Parameters
    ----------
    sample : dict
        A single item from a HuggingFace Dataset (e.g., dataset[i]).
    audio_col : str, optional
        Name of the audio column (default: "audio").

    Returns
    -------
    IPython.display.Audio
        An Audio widget for inline playback in Jupyter.
    """
    audio = sample[audio_col]

    # Case 1: already decoded (HF Audio feature with decode=True)
    if isinstance(audio, dict) and "array" in audio and "sampling_rate" in audio:
        array = audio["array"]
        sample_rate = audio["sampling_rate"]

    # Case 2: needs decoding (AudioDecoder / lazy audio)
    else:
        decoded = audio.get_all_samples()
        array = decoded.data
        sample_rate = decoded.sample_rate

    # Ensure 1D array for playback
    if hasattr(array, "ndim") and array.ndim > 1:
        array = array.squeeze()

    return Audio(array, rate=sample_rate)
