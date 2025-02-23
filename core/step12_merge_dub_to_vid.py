import os
import sys
import platform
import subprocess
from pathlib import Path

import numpy as np
import cv2
from rich import print as rprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.all_whisper_methods.demucs_vl import BACKGROUND_AUDIO_FILE
from core.step7_merge_sub_to_vid import check_gpu_available
from core.config_utils import load_key
from core.step1_ytdlp import find_video_files
from core.translate_once import translate_filename

DUB_VIDEO = "output/output_dub.mp4"
DUB_SUB_FILE = 'output/dub.srt'
DUB_AUDIO = 'output/dub.mp3'

TRANS_FONT_SIZE = 30
TRANS_FONT_NAME = 'Arial'
if platform.system() == 'Linux':
    TRANS_FONT_NAME = 'NotoSansCJK-Regular'

TRANS_FONT_COLOR = '&H00FFFF'
TRANS_OUTLINE_COLOR = '&H000000'
TRANS_OUTLINE_WIDTH = 1 
TRANS_BACK_COLOR = '&H33000000'

def check_gpu_available():
    """检查系统支持的硬件加速编码器"""
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        if platform.system() == 'Darwin':  # macOS
            return 'h264_videotoolbox' in result.stdout
        else:  # Linux/Windows
            return 'h264_nvenc' in result.stdout
    except:
        return False

def merge_video_audio():
    """Merge video and audio, and reduce video volume"""
    VIDEO_FILE = find_video_files()
    background_file = BACKGROUND_AUDIO_FILE
    
    if not load_key("burn_subtitles"):
        rprint("[bold yellow]Warning: A 0-second black video will be generated as a placeholder as subtitles are not burned in.[/bold yellow]")

        # Create a black frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(DUB_VIDEO, fourcc, 1, (1920, 1080))
        out.write(frame)
        out.release()

        rprint("[bold green]Placeholder video has been generated.[/bold green]")
        return

    # Merge video and audio with translated subtitles
    dub_volume = load_key("dub_volume")
    merge_background = load_key("merge_background_sound")
    video = cv2.VideoCapture(VIDEO_FILE)
    TARGET_WIDTH = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    TARGET_HEIGHT = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.release()
    rprint(f"[bold green]Video resolution: {TARGET_WIDTH}x{TARGET_HEIGHT}[/bold green]")
    
    subtitle_filter = (
        f"subtitles={DUB_SUB_FILE}:force_style='FontSize={TRANS_FONT_SIZE},"
        f"FontName={TRANS_FONT_NAME},PrimaryColour={TRANS_FONT_COLOR},"
        f"OutlineColour={TRANS_OUTLINE_COLOR},OutlineWidth={TRANS_OUTLINE_WIDTH},"
        f"BackColour={TRANS_BACK_COLOR},Alignment=2,MarginV=27,BorderStyle=4'"
    )
    
    cmd = [
        'ffmpeg', '-y', '-i', VIDEO_FILE
    ]
    
    if merge_background:
        cmd.extend(['-i', background_file])
    
    cmd.extend(['-i', DUB_AUDIO])
    
    filter_complex = [
        f'[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,'
        f'pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,'
        f'{subtitle_filter}[v];'
    ]
    
    if merge_background:
        # 修正音频混合的 filter chain
        filter_complex.extend([
            f'[1:a]volume=1[a1];',
            f'[2:a]volume={dub_volume}[a2];',
            f'[a1][a2]amix=inputs=2:duration=first:dropout_transition=3[a]'
        ])
    else:
        # 如果不需要混合背景音，只处理配音音频
        filter_complex.extend([f'[1:a]volume={dub_volume}[a]'])
    
    # 移除重复的音频处理
    cmd.extend(['-filter_complex', ''.join(filter_complex)])
    
    if check_gpu_available():
        if platform.system() == 'Darwin':  # macOS
            rprint("[bold green]Using VideoToolbox hardware acceleration...[/bold green]")
            cmd.extend(['-map', '[v]', '-map', '[a]', 
                       '-c:v', 'h264_videotoolbox',
                       '-b:v', '1500k',        # 降低视频比特率
                       '-maxrate', '2000k',    # 降低最大比特率
                       '-bufsize', '2000k',    # 降低缓冲区大小
                       '-profile:v', 'high',   # 使用 main profile 以获得更好的压缩率
                       '-allow_sw', '1'])
        else:  # Linux/Windows
            rprint("[bold green]Using NVIDIA GPU acceleration...[/bold green]")
            cmd.extend(['-map', '[v]', '-map', '[a]', 
                       '-c:v', 'h264_nvenc',
                       '-preset', 'p7',        # 使用更高压缩率的预设
                       '-b:v', '1500k',
                       '-maxrate', '2000k',
                       '-bufsize', '2000k',
                       '-rc:v', 'vbr'])        # 使用可变比特率
    else:
        rprint("[bold yellow]No hardware encoder detected, using CPU...[/bold yellow]")
        cmd.extend(['-map', '[v]', '-map', '[a]',
                   '-c:v', 'libx264',
                   '-preset', 'medium',        # 使用 medium 预设平衡压缩率和速度
                   '-crf', '28',              # 提高 CRF 值以获得更小的文件大小
                   '-b:v', '1500k'])
    
    cmd.extend(['-c:a', 'aac', '-b:a', '96k', DUB_VIDEO])  # 进一步降低音频比特率

    print(' '.join(cmd))
    subprocess.run(cmd)
    
    # 获取原始文件名并翻译
    # original_name = Path(VIDEO_FILE).stem
    # translated_name = translate_filename(original_name)
    # final_output = f"output/{translated_name}.mp4"
    
    # # 重命名输出文件
    # if os.path.exists(DUB_VIDEO):
    #     try:
    #         os.rename(DUB_VIDEO, final_output)
    #         rprint(f"[bold green]✅ 视频已重命名为: {translated_name}.mp4[/bold green]")
    #     except Exception as e:
    #         rprint(f"[red]重命名视频失败: {str(e)}[/red]")
    
    # rprint(f"[bold green]🎉 视频处理完成: {final_output}[/bold green]")

if __name__ == '__main__':
    merge_video_audio()
