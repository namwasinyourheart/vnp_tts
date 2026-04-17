import numpy as np
import torchaudio
import io

# Đọc raw PCM (16-bit little-endian, mono)
with open('/home/nampv1/projects/tts/vnp_tts/toy_output/audio.pcm', 'rb') as f:
    data = f.read()

# Chuyển thành numpy array
audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32767.0  # Normalize to float32

# Test với sr=24000
sr = 24000
duration = len(audio) / sr
print(f"With sr=24000: Duration {duration:.2f}s, Samples: {len(audio)}")

# Test với sr=44100
sr2 = 44100
duration2 = len(audio) / sr2
print(f"With sr=44100: Duration {duration2:.2f}s")

# Sử dụng torchaudio để load raw PCM
audio_torch, sr_torch = torchaudio.load(io.BytesIO(data), format="s16le", num_frames=len(data)//2, channels_first=False)
print(f"Torchaudio: Shape {audio_torch.shape}, SR {sr_torch}, Duration {audio_torch.shape[0]/sr_torch:.2f}s")