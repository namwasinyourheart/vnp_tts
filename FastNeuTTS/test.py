import re
import time
import torch
from IPython.display import Audio
from NeuTTS.engine import TTSEngine

tts_engine = TTSEngine()
text = "Wow. This place looks even better than I imagined. How did they set all this up so perfectly? The lights, the music, everything feels magical. I can't stop smiling right now."

audio_file = "/media/nampv1/hdd/data/VoiceGarden/elevenlabs/13-female-north-young-story-tuyet-trinh-eng-11s.mp3" ## custom reference file, should be 3s or more

codes_str, transcript = tts_engine.encode_audio(audio_file) ## good idea to cache speaker codes and transcripts so no need to encode again
audio = tts_engine.batch_generate([text], [codes_str], [transcript])


import soundfile as sf

sf.write("test.wav", audio, 24000)


# display(Audio(audio, rate=24000))