import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print as rprint
import subprocess

from core.config_utils import load_key
from core.all_whisper_methods.demucs_vl import demucs_main, RAW_AUDIO_FILE, VOCAL_AUDIO_FILE
from core.all_whisper_methods.audio_preprocess import process_transcription, convert_video_to_audio, split_audio, save_results, compress_audio, CLEANED_CHUNKS_EXCEL_PATH
from core.step1_ytdlp import find_video_files

WHISPER_FILE = "output/audio/for_whisper.mp3"
ENHANCED_VOCAL_PATH = "output/audio/enhanced_vocals.mp3"

def enhance_vocals(vocals_ratio=2.50):
    """Enhance vocals audio volume"""
    if not load_key("demucs"):
        return RAW_AUDIO_FILE
        
    try:
        print(f"[cyan]🎙️ Enhancing vocals with volume ratio: {vocals_ratio}[/cyan]")
        ffmpeg_cmd = (
            f'ffmpeg -y -i "{VOCAL_AUDIO_FILE}" '
            f'-filter:a "volume={vocals_ratio}" '
            f'"{ENHANCED_VOCAL_PATH}"'
        )
        subprocess.run(ffmpeg_cmd, shell=True, check=True, capture_output=True)
        
        return ENHANCED_VOCAL_PATH
    except subprocess.CalledProcessError as e:
        print(f"[red]Error enhancing vocals: {str(e)}[/red]")
        return VOCAL_AUDIO_FILE  # Fallback to original vocals if enhancement fails
    
def transcribe():
    if os.path.exists(CLEANED_CHUNKS_EXCEL_PATH):
        rprint("[yellow]⚠️ Transcription results already exist, skipping transcription step.[/yellow]")
        return
    
    # step0 Convert video to audio
    video_file = find_video_files()
    convert_video_to_audio(video_file)

    # step1 Demucs vocal separation:
    if load_key("demucs"):
        demucs_main()
    
    # step2 Compress audio
    choose_audio = VOCAL_AUDIO_FILE if load_key("demucs") else RAW_AUDIO_FILE
    #whisper_audio = compress_audio(choose_audio, WHISPER_FILE)
    whisper_audio = choose_audio

    # step3 Extract audio
    segments = split_audio(whisper_audio)
    
    # step4 Transcribe audio
    all_results = []
    time_offset = 0
    
    if load_key("whisper.runtime") == "local":
        from core.all_whisper_methods.whisperX_local import transcribe_audio as ts
        rprint("[cyan]🎤 Transcribing audio with local model...[/cyan]")
    else:
        from core.all_whisper_methods.whisperX_302 import transcribe_audio_302 as ts
        rprint("[cyan]🎤 Transcribing audio with 302 API...[/cyan]")

    for i, (start, end) in enumerate(segments):
        try:
            rprint(f"[cyan]Processing segment {i+1}/{len(segments)}...[/cyan]")
            result = ts(whisper_audio, start, end)
            all_results.append(result)
            
        except Exception as e:
            rprint(f"[red]Error processing segment {i+1}: {str(e)}[/red]")
            import traceback
            print(traceback.format_exc())
            raise e
    
    if not all_results:
        raise Exception("No transcription results were generated!")
    
    # step5 Combine results
    combined_result = {'segments': []}
    for result in all_results:
        if result and 'segments' in result:
            combined_result['segments'].extend(result['segments'])
    
    # 确保segments按时间排序
    combined_result['segments'].sort(key=lambda x: x['start'])
    
    # step6 Process df
    try:
        df = process_transcription(combined_result)
        save_results(df)
    except Exception as e:
        rprint(f"[red]Error processing transcription results: {str(e)}[/red]")
        raise
        
if __name__ == "__main__":
    transcribe()