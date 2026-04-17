import re
import time
import torch
import random
import librosa
import numpy as np
from itertools import cycle
from IPython.display import Audio
from collections import defaultdict
from NeuTTS.codec import TTSCodec, overlap
from lmdeploy import pipeline, TurbomindEngineConfig, GenerationConfig

def compile_upsampler_with_triton_check(upsampler):
    """
    Checks for Triton and compiles the upsampler's forward pass if found.

    Args:
        upsampler: The model object containing the upsampler structure.
    """
    try:
        # Check if Triton is available. Importing it is the standard way.
        import triton

        # If the import succeeds, proceed with compilation
        upsampler.model.dec.resblocks[2].forward = torch.compile(
            upsampler.model.dec.resblocks[2].forward,
            mode="reduce-overhead", 
            dynamic=True            
        )
    except ImportError:
        # If Triton is not found, print the required message and pass
        print("Triton not found, please install triton/triton_windows for faster speed although optional.")
        pass

class TTSEngine:
    """
    Uses LMdeploy to run maya-1 with great speed
    """

    def __init__(
        self, 
        memory_util = 0.1, 
        tp = 1, 
        enable_prefix_caching = True,
        quant_policy = 0, 
        model="neuphonic/neutts-air",
        espeak_lang="en-us"

    ):
        """
        Initializes the model configuration.

        Args:
            memory_util (float): Target fraction of GPU memory usage (0.0 to 1.0). Default: 0.3
            tp (int): Number of Tensor Parallel (TP) ranks. Use for multiple gpus. Default: 1
            enable_prefix_caching (bool): If True, cache input prefixes. Use for batching. Default: True
            quant_policy (int): KV cache quant bit-width (e.g., 8 or None). Saves vram at slight quality cost. Default: 8
        """
        self.tts_codec = TTSCodec(espeak_lang=espeak_lang)
        backend_config = TurbomindEngineConfig(cache_max_entry_count=memory_util, tp=tp, enable_prefix_caching=enable_prefix_caching, dtype='bfloat16', quant_policy=quant_policy)
        self.pipe = pipeline(model, backend_config=backend_config)
        self.gen_config = GenerationConfig(top_p=0.95,
                              top_k=50,
                              temperature=1.0,
                              max_new_tokens=1024,
                              repetition_penalty=1.1,
                              do_sample=True,
                              min_p=0.1,
                              min_new_tokens=40
                              )
        self.stored_dict = defaultdict(dict) 
       # compile_upsampler_with_triton_check(tts_codec.upsampler) ## optionally compiles upsampler with triton for considerable speed boosts



    # 3. An instance method (operates on the object's data)
    def encode_audio(self, voice, trascript):
        """
        Encodes the voice file. Takes time, hence good idea too cache it for later use.

        Args:
            voice (str): audio file path
        """

        codes_str, transcript = self.tts_codec.encode_audio(voice, trascript, add_silence=32000)
        return codes_str, transcript


    # 4. Another instance method (modifies the object's state)
    def split_sentences(self, text):
        """
        Splits paragraphs into list of sentences

        Args:
            text (str): input paragraphs
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return sentences

    def decode_audio(self, tokens, batched=False):
        """
        Decodes audio from neucodec tokens

        Args:
            tokens (list/str): List or str of tokens to decode
            batched (bool): To decode tokens as list or single string
        """
        if batched:
            decoded = self.tts_codec.decode_tokens_batched(tokens)
            pad_len = decoded[1]
            audio = decoded[0].squeeze(1).flatten().numpy()
            audio = audio[:-pad_len*480]
        else:
            audio = self.tts_codec.decode_tokens(tokens)[0][0][0].numpy()

        return audio

    def generate(self, prompt, codes_str, transcript):
        """
        Generates speech from text, for single batch size

        Args:
            prompt (str): Input for tts model
            voice (str): Description of voice
        """
        formatted_prompt = self.tts_codec.format_prompt(prompt, transcript, codes_str)
        responses = self.pipe([formatted_prompt], gen_config=self.gen_config, do_preprocess=False)
        generated_tokens = responses[0].text
        audio = self.decode_audio(generated_tokens)
        return audio

    def batch_generate(self, prompts, codes_strs, transcripts):
        """
        Generates speech from text, for larger batch size

        Args:
            prompt (list): Input for tts model, list of prompts
            voice (list): Description of voice, list of voices respective to prompt
        """
        formatted_prompts = []
        for prompt, code_str, transcript in zip(prompts, cycle(codes_strs), cycle(transcripts)):
            formatted_prompt = self.tts_codec.format_prompt(prompt, transcript, code_str)
            formatted_prompts.append(formatted_prompt)

        responses = self.pipe(formatted_prompts, gen_config=self.gen_config, do_preprocess=False)
        generated_tokens = [response.text for response in responses]

        print("Generated tokens:")
        for i, t in enumerate(generated_tokens):
            print(f"{i}: len={len(t)} | preview={repr(t[:200])}")

        audios = self.decode_audio(generated_tokens, batched=True)
        return audios

    async def stream_audio(self, text, user_id, display_audio=True):
        """
        Fast async function for streaming audio: low as 100ms latency(depends on how long text is and reference file)

        Args:
            text (str): Input for tts model, single prompt
            user_id (int): Unique user id for each seperate user stored in stored dict
            display_audio (bool): To display audio or not
        """
        duration = 6
        all_audios = []
        all_tokens = ""
        num_tokens = 0
        first_audio = True
        fade_samples = 100

        transcript = self.stored_dict[f"{user_id}"]['transcript']
        codes_str = self.stored_dict[f"{user_id}"]['codes_str']

        prompt = self.tts_codec.format_prompt(text, transcript, codes_str)

        t0 = time.time()
        async for response in self.pipe.generate(messages=prompt, gen_config=self.gen_config, session_id=user_id, sequence_start=True, sequence_end=True, do_preprocess=False):
            all_tokens += response.response
            num_tokens += 1 
            # if num_tokens == 50:
            if num_tokens == 20:

                if first_audio:
                    print(f"Latency is {time.time() - t0} seconds.")
                    first_audio = False

                wav = self.decode_audio(all_tokens, False).astype(np.float32)
                all_audios.append(wav)
                wav = overlap(all_audios, fade_samples)
                all_audios[-1] = wav

                yield wav

                num_tokens = 0
                all_tokens = ""

        if num_tokens > 10:
            wav = self.decode_audio(all_tokens, False).astype(np.float32)

            all_audios.append(wav)
            wav = overlap(all_audios, fade_samples)
            all_audios[-1] = wav

            yield wav

        if display_audio:
            display(Audio(np.concatenate(all_audios), rate=24000))

    # Metadata	Value
    # Sample Rate	24000 Hz
    # Channels	Mono
    # Bit Depth	32-bit float
    # Format	PCM Float
    # Streaming	Yes (token-based)
    # Chunk Decode	20 tokens
    # Crossfade	100 samples (~4ms)
    
    def add_speaker(self, audio_file, trascript):
        """
        Function to add a new user and unique speaker transcript and codes, returns user id to use for stream_audio function

        Args:
            audio_file (str): new audio file to encode and create unique user id for
        """
        codes_str, transcript = self.encode_audio(audio_file, trascript)

        user_id = random.randint(100000, 999999)
        self.stored_dict[f"{user_id}"]['transcript'] = transcript
        self.stored_dict[f"{user_id}"]['codes_str'] = codes_str
        return user_id