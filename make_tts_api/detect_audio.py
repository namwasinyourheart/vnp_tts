import subprocess
import json

def detect_audio(file_path):
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    format_name = data["format"]["format_name"]
    codec = data["streams"][0]["codec_name"]

    return format_name, codec


def detect_audio_bytes(audio_bytes: bytes):
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-i", "pipe:0",
    ]

    result = subprocess.run(cmd, input=audio_bytes, capture_output=True)
    data = json.loads(result.stdout.decode("utf-8") or "{}")

    format_name = (data.get("format") or {}).get("format_name")
    streams = data.get("streams") or []
    codec = (streams[0].get("codec_name") if streams else None)

    return format_name, codec

if __name__ == "__main__":
    audio_path = "/media/nampv1/hdd/data/Venterprise/raw/generated/Address_HàNội_train_dev_test_minimax/test_item_part1/minimax_selenium/default/elevenlabs_spk16/wav/0101087279_một_trăm_bảy_mươi_tám_tôn_đức_thắng,_phường_hàng_b.wav"
    audio_path = "vnp_tts/toy_output/25_male_north_middle_adv_tvc_nhat_nam_8s_converted.wav"
    fmt, codec = detect_audio(audio_path)
    print("Format:", fmt)
    print("Codec:", codec)