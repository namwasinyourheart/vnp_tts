# FastNeuTTS
Fast NeuTTS is a highly optimized engine for [NeuTTS-air](https://huggingface.co/neuphonic/neutts-air) using [LMdeploy](https://github.com/InternLM/lmdeploy) to generate minutes of audio in just seconds. This repo is similar to the previous [FastMaya](https://github.com/ysharma3501/FastMaya) repo but much more faster and supports voice cloning as well.
It will soon support multilingual models and multi-speaker models as well with streaming and latencies as low as 100ms.

## Key improvements in this repo
* Much faster then original  implementation and can reach over **200x realtime** on consumer gpus using batching!
* Memory efficent as it works on **6gb vram gpus**.
* Works with multiple gpus using tensor parallel to improve speed further.
* Incredibly low potential latency of just **100ms**
  
Speed was tested on 4070 Ti Super
- Input text can be found in test.txt
- 2.397 seconds to generate 508 seconds of audio
- Hence **211x realtime** or 0.0047 RTF factor

Simple 2 line installation; requires pip and git but uv will speed up installation considerably
```
uv pip install git+https://github.com/ysharma3501/FastNeuTTS.git
sudo apt install espeak-ng -y
```

Usage for single batch size:
```python
import re
import time
import torch
from IPython.display import Audio
from NeuTTS.engine import TTSEngine

tts_engine = TTSEngine()
text = "Wow. This place looks even better than I imagined. How did they set all this up so perfectly? The lights, the music, everything feels magical. I can't stop smiling right now."

audio_file = "audio_file" ## custom reference file, should be 3s or more

codes_str, transcript = tts_engine.encode_audio(audio_file) ## good idea to cache speaker codes and transcripts so no need to encode again
audio = tts_engine.batch_generate([text], [codes_str], [transcript])

display(Audio(audio, rate=24000))
```


Usage for larger batch sizes:
```python

text = ["Wow. This place looks even better than I imagined. How did they set all this up so perfectly? The lights, the music, everything feels magical. I can't stop smiling right now.", "You dare challenge me, mortal. How amusing. Your kind always thinks they can win!"]
audio_file = "custom_reference_file" ## should be 3+ seconds

codes_str, transcript = tts_engine.encode_audio(audio_file) ## good idea to cache speaker codes and transcripts so no need to encode again
audio = tts_engine.batch_generate(text, [codes_str], [transcript])

display(Audio(audio, rate=24000))
```

Usage for **auto-splitting text** into sentences and batching(good for paragraphs):
```python
text = """Paris, often affectionately known as the City of Light or La Ville Lumière, is the historic capital of France, globally celebrated as a center of art, fashion, gastronomy, and romance. Situated on the winding Seine River, which divides the city into the Left Bank and Right Bank, Paris offers a captivating blend of magnificent Haussmann architecture, grand boulevards, and charming, intimate neighborhoods. It is home to world-renowned landmarks like the iconic Eiffel Tower, the colossal Louvre Museum housing the Mona Lisa, and the historic Notre-Dame Cathedral. Millions of visitors flock here annually to soak in the cultural richness, from the bohemian streets of Montmartre to the high-fashion boutiques along the Champs-Élysées, making it a perennial top destination for travelers worldwide."""
text = tts_engine.split_sentences(text)

audio_file = "custom_reference_file" ## should be 3+ seconds

codes_str, transcript = tts_engine.encode_audio(audio_file) ## good idea to cache speaker codes and transcripts so no need to encode again
audio = tts_engine.batch_generate(text, [codes_str], [transcript])

display(Audio(audio, rate=24000))
```

Newly added: Async streaming inference that supports multiple users!
```python
input_text = "Wow. This place looks even better than I imagined. How did they set all this up so perfectly? The lights, the music, everything feels magical. I can't stop smiling right now."
display_audio = True

audio_file = "custom_reference_file"
user_id = tts_engine.add_speaker(audio_file) ## this will create a unique user for this reference file

async for wav in stream_audio(input_text, user_id, display_audio=display_audio):
    ## you can manipulate wav now or just display it
    pass
```

It is important to note that larger batch sizes lead to **larger speedups**. For single batch sizes, it is roughly 6x realtime which is still considerably faster then FastMaya while larger batch sizes are 200x realtime or more.

Stars would be greatly appreciated and I would be happy to implement other features as well.

## Next priorities
- [x] fast streaming generation, current testing shows latencies low as 200ms
- [ ] Multilingual models(hi, fr, de, etc.)
- [ ] Efficent Multi speaker generation
- [x] Online inference using async LMdeploy. Rough implementation done, will improve later on.
