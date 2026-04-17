#from FastAudioSR import FASR
from transformers import pipeline as transformers_pipeline
from huggingface_hub import snapshot_download
from phonemizer.backend.espeak.wrapper import EspeakWrapper
from phonemizer.backend import EspeakBackend
from typing import Optional, Dict
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio
from torchaudio import transforms as T
from huggingface_hub import PyTorchModelHubMixin, ModelHubMixin, REMOVEDhub_download
from transformers import AutoFeatureExtractor, HubertModel, Wav2Vec2BertModel
from neucodec import DistillNeuCodec
import librosa
import gc
import re

class TTSCodec:
    def __init__(self, espeak_lib=None, espeak_lang="en-us"):

        decoder_paths = snapshot_download("YatharthS/FlashSR")
        #self.upsampler = FASR(f'{decoder_paths}/upsampler.pth')
        #self.upsampler.model.half().eval()
        self.transcriber = transformers_pipeline("automatic-speech-recognition", model="openai/whisper-small", device='cuda:0', torch_dtype=torch.bfloat16)
        if espeak_lib:
            EspeakWrapper.set_library(espeak_lib)
        self.phonemizer = EspeakBackend(
            # language="en-us", preserve_punctuation=True, with_stress=True
            language=espeak_lang, preserve_punctuation=True, with_stress=True
        )
        self.codec_encoder = DistillNeuCodec.from_pretrained("neuphonic/distill-neucodec").to("cuda:0").eval()



    @torch.inference_mode()   
    def encode_audio(self, audio, transcript, duration=8, add_silence=8000):

        """encodes audio file into speech tokens and context tokens"""
        audio, sr = librosa.load(audio, duration=duration, sr=16000)
        if add_silence:
            audio = np.concatenate((audio, np.zeros(add_silence)))
        if not transcript:
            transcript = self.transcriber(audio[:-32000])['text'].lstrip()
        audio = torch.from_numpy(audio)[None, None, ...].float()

        context_codes = self.codec_encoder.encode_code(audio).cpu().numpy()
        codes_str = "".join([f"<|speech_{i}|>" for i in context_codes[0][0]])

        return codes_str, transcript

    def format_prompt(self, text, transcript, codes_str):

        transcript_phones = " ".join(self.phonemizer.phonemize([transcript])[0].split())
        text_phones = " ".join(self.phonemizer.phonemize([text])[0].split())

        prompt = f"user: Convert the text to speech:<|TEXT_PROMPT_START|>{transcript_phones} {text_phones}<|TEXT_PROMPT_END|>\nassistant:<|SPEECH_GENERATION_START|>{codes_str}"
        return prompt
    @torch.inference_mode()
    def decode_tokens_batched(self, tokens, batch=False, upsample=False):

        """decodes the speech tokens with context tokens for audio output, optionally upsamples to 48khz for higher quality output"""

        my_data = [int(num) for token in tokens for num in re.findall(r"<\|speech_(\d+)\|>", token)] 

        chunk_size = 50
        total_len = len(my_data)
        pad_len = (chunk_size - (total_len % chunk_size)) % chunk_size
        padded_data = my_data + [0] * pad_len
        codes_1d = np.array(padded_data, dtype=np.int32)

        codes_reshaped = codes_1d.reshape(-1, 1, chunk_size)
        codes = torch.from_numpy(codes_reshaped).to('cuda:0')

        recon = self.codec_encoder.decode_code(codes).cpu()
        if upsample:
            recon = T.Resample(24_000, 16_000)(recon.squeeze(1)).half()
            chunks = recon.split(64)

            processed_chunks = [self.upsampler.run(chunk) for chunk in chunks]
            wav = torch.cat(processed_chunks, dim=0)

            return wav, pad_len
        else:
            return recon, pad_len

    @torch.inference_mode()
    def decode_tokens(self, tokens, batch=False, upsample=False):

        """decodes the speech tokens with context tokens for audio output, optionally upsamples to 48khz for higher quality output"""

        speech_ids = [int(num) for num in re.findall(r"<\|speech_(\d+)\|>", tokens)]
        codes = np.array(speech_ids, dtype=np.int32)[np.newaxis, np.newaxis, :]
        codes = torch.from_numpy(codes).to('cuda:0')

        recon = self.codec_encoder.decode_code(codes).cpu()
        if upsample:
            recon = T.Resample(24_000, 16_000)(torch.from_numpy(recon).squeeze(1))
            wav = self.upsampler.run(recon.half())
            return wav, 48000
        else:
            return recon, 24000


    def c_cache(self):
        """clears any vram/cache, very useful"""
        gc.collect()
        torch.cuda.empty_cache()

def overlap(frames: list[np.ndarray], overlap: int) -> np.ndarray:
    if len(frames) <= 1:
        return frames[0] if frames else np.array([])

    last = frames[-1].squeeze()
    prev = frames[-2].squeeze()

    # Calculate Stride (Hop Size) and Overlap Segments
    stride = prev.shape[-1] - overlap

    # Generate linear fade windows: fade-out for previous, fade-in for last
    t = np.linspace(0.0, 1.0, overlap, dtype=last.dtype)

    # Weighted Sum (Overlap-Add)
    weighted_sum = (prev[stride:] * (1.0 - t)) + (last[:overlap] * t)

    # Replace the overlapped start of the last frame
    result = last.copy()
    result[:overlap] = weighted_sum
    return result