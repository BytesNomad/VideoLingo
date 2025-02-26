from pathlib import Path
import edge_tts
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from core.config_utils import load_key

# Available voices can be listed using edge-tts --list-voices command
# Common English voices:
# en-US-JennyNeural - Female
# en-US-GuyNeural - Male  
# en-GB-SoniaNeural - Female British
# Common Chinese voices:
# zh-CN-YunjianNeural                Male      Sports, Novel          Passion
# zh-CN-YunxiNeural                  Male      Novel                  Lively, Sunshine
# zh-CN-YunxiaNeural                 Male      Cartoon, Novel         Cute
# zh-CN-YunyangNeural                Male      News                   Professional, Reliable
# zh-CN-liaoning-XiaobeiNeural       Female    Dialect                Humorous
# zh-CN-shaanxi-XiaoniNeural         Female    Dialect                Bright
# zh-CN-XiaoxiaoNeural               Female    News, Novel            Warm
# zh-CN-XiaoyiNeural                 Female    Cartoon, Novel         Lively

def select_voice(speaker_id):
    """根据说话人信息选择合适的 Edge TTS 声音"""
    edge_set = load_key("edge_tts")

    # 检查是否有针对特定说话人的声音配置
    speaker_voice_mapping = edge_set.get("speaker_voices", {})
    if speaker_id and speaker_id in speaker_voice_mapping:
        return speaker_voice_mapping[speaker_id]
    
    # 默认声音
    default_voice = edge_set.get("default_voice", "zh-CN-YunjianNeural")
    print(f"Speaker:{speaker_id} Using default voice: {default_voice}")
    return default_voice



def edge_tts(text, save_path, speaker=None):
  
    # Load settings from config file

    # 选择合适的声音
    try:
        voice = select_voice(speaker)
    except Exception as e:
        print(f"Error selecting voice: {e}")
        voice = "zh-CN-YunjianNeural"  # 回退到默认声音
    print(f"Speaker:{speaker} Using voice: {voice}")
    
    # Create output directory if it doesn't exist
    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use subprocess to run edge-tts command directly
    import subprocess
    
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", text,
        "--write-media", str(speech_file_path)
    ]

    print(cmd)
    subprocess.run(cmd, check=True)
    print(f"Audio saved to {speech_file_path}")

if __name__ == "__main__":
    edge_tts("今天是个好天气", "edge_tts.wav", "SPEAKER_01")
