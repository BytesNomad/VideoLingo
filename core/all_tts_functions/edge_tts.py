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

def edge_tts(text, save_path):
    # Load settings from config file
    edge_set = load_key("edge_tts")
    voice = edge_set.get("voice", "zh-CN-YunxiNeural")
    
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
    edge_tts("今天是个好天气", "edge_tts.wav")
