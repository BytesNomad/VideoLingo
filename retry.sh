#cd ../"The Way, Part 6"; ffmpeg -i output_dub.mp4 -i dub.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4

#export DIR="The Perfect Body";cd ../"$DIR"; ffmpeg -i $DIR.mp4 -i dub.mp3 -filter_complex "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,subtitles=dub.srt:force_style='FontSize=30,FontName=Arial,PrimaryColour=&H00FFFF,OutlineColour=&H000000,OutlineWidth=1,BackColour=&H33000000,Alignment=2,MarginV=27,BorderStyle=4'[v];[1:a]volume=1.0[a]" -map "[v]" -map "[a]" -c:v h264_videotoolbox -c:a aac -b:a 192k output_dub.mp4


RETRY_FILE="$1"

mv batch/output/"$2"/"$RETRY_FILE" ./output
#rm output/audio/tts_tasks.xlsx 
rm -rf output/audio/tmp/

python core/step8_1_gen_audio_task.py 
python core/step8_2_gen_dub_chunks.py
python core/step9_extract_refer_audio.py
python core/step10_gen_audio.py
python core/step11_merge_full_audio.py
python core/step12_merge_dub_to_vid.py

mv ./output batch/output/"$RETRY_FILE" 