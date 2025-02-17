import os,sys,json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key

## ================================================================
# @ step4_splitbymeaning.py
def get_split_prompt(sentence, num_parts = 2, word_limit = 20):
    language = load_key("whisper.detected_language")
    split_prompt = f"""
### Task
As a Netflix subtitle splitter, split the text into {num_parts} parts (max {word_limit} words each). Split at natural points, maintain coherence, and keep parts balanced (min 3 words).

### Output Format in JSON
{{
    "analysis": "Brief analysis of the text structure",
    "split": "Complete sentence with [br] tags at split positions"
}}

### Given Text
<split_this_sentence>
{sentence}
</split_this_sentence>

### Your Answer, Provide ONLY a valid JSON object:
""".strip()
    return split_prompt


## ================================================================
# @ step4_1_summarize.py
def get_summary_prompt(source_content, custom_terms_json=None):
    src_lang = load_key("whisper.detected_language")
    tgt_lang = load_key("target_language")
    
    # add custom terms note
    terms_note = ""
    if custom_terms_json:
        terms_list = []
        for term in custom_terms_json['terms']:
            terms_list.append(f"- {term['src']}: {term['tgt']} ({term['note']})")
        terms_note = "\n### Existing Terms\nPlease exclude these terms in your extraction:\n" + "\n".join(terms_list)
    
    summary_prompt = f"""
### Task
As a {src_lang}-{tgt_lang} translation expert:
1. Summarize video content in two sentences
2. Extract and translate key terms to {tgt_lang} (exclude existing terms)
3. Add brief explanations{terms_note}

### Output in Json Format
{{
    "topic": "Two-sentence video summary",
    "terms": [
        {{
            "src": "{src_lang} term",
            "tgt": "{tgt_lang} translation or original",
            "note": "Brief explanation"
        }},
        ...
    ]
}}


### Source Text
<text>
{source_content}
</text>
""".strip()
    return summary_prompt

## ================================================================
# @ step5_translate.py & translate_lines.py
def generate_shared_prompt(previous_content_prompt, after_content_prompt, summary_prompt, things_to_note_prompt):
    return f'''### Context Information
<previous_content>
{previous_content_prompt}
</previous_content>

<subsequent_content>
{after_content_prompt}
</subsequent_content>

### Content Summary
{summary_prompt}

### Points to Note
{things_to_note_prompt}'''

def get_prompt_faithfulness(lines, shared_prompt):
    TARGET_LANGUAGE = load_key("target_language")
    # Split lines by \n
    line_splits = lines.split('\n')
    
    # Create JSON return format example
    json_format = {}
    for i, line in enumerate(line_splits, 1):
        json_format[i] = {
            "origin": line,
            "direct": f"<<direct {TARGET_LANGUAGE} translation>>"
        }
    
    src_language = load_key("whisper.detected_language")
    prompt_faithfulness = f'''
### Task
As a {src_language}-{TARGET_LANGUAGE} subtitle translator:
1. 翻译每一行，要求尽量口语化和地道
2. Maintain original meaning and terminology
3. Consider context and cultural nuances


{shared_prompt}

### Subtitle Data
<subtitles>
{lines}
</subtitles>

### Output Format
Please complete the following JSON data, where << >> represents placeholders that should not appear in your answer, and return your translation results in JSON format:
{json.dumps(json_format, ensure_ascii=False, indent=4)}
'''
    return prompt_faithfulness.strip()


def get_prompt_expressiveness(faithfulness_result, lines, shared_prompt):
    TARGET_LANGUAGE = load_key("target_language")
    json_format = {}
    for key, value in faithfulness_result.items():
        json_format[key] = {
            "origin": value['origin'],
            "direct": value['direct'],
            "reflection": "reflection on the direct translation version",
            "free": f"retranslated result, aiming for fluency and naturalness, conforming to {TARGET_LANGUAGE} expression habits, DO NOT leave empty line here!"
        }

    src_language = load_key("whisper.detected_language")
    prompt_expressiveness = f'''
### Task
As a {src_language}-{TARGET_LANGUAGE} translation consultant:
1. Review direct translations
2. Improve fluency and naturalness
3. Adapt to {TARGET_LANGUAGE} expression style
4. Match content tone (casual/professional/formal)

{shared_prompt}

### Subtitle Data
<subtitles>
{lines}
</subtitles>

### Output in the following JSON format, repeat "origin" and "direct" in the JSON format
{json.dumps(json_format, ensure_ascii=False, indent=4)}
'''
    return prompt_expressiveness.strip()


## ================================================================
# @ step6_splitforsub.py
def get_align_prompt(src_sub, tr_sub, src_part):
    TARGET_LANGUAGE = load_key("target_language")
    src_language = load_key("whisper.detected_language")
    src_splits = src_part.split('\n')
    num_parts = len(src_splits)
    src_part = src_part.replace('\n', ' [br] ')
    align_prompt = '''
### Task
As a {src_language}-{target_language} subtitle alignment expert:
1. Match split points with pre-processed {src_language} version
2. Maintain structural correspondence
3. Avoid empty lines (rewrite if needed)
4. Focus on viewer-ready output

### Subtitle Data
<subtitles>
{src_language} Original: "{src_sub}"
{target_language} Original: "{tr_sub}"
Pre-processed {src_language} Subtitles ([br] indicates split points): {src_part}
</subtitles>

### Output in JSON
{{
    "analysis": "Brief analysis of word order, structure, and semantic correspondence between {src_language} and {target_language} subtitles",
    "align": [
        {align_parts_json}
    ]
}}

### Your Answer, Provide ONLY a valid JSON object:
'''

    align_parts_json = ','.join(
        f'''
        {{
            "src_part_{i+1}": "{src_splits[i]}",
            "target_part_{i+1}": "Corresponding aligned {TARGET_LANGUAGE} subtitle part"
        }}''' for i in range(num_parts)
    )

    return align_prompt.format(
        src_language=src_language,
        target_language=TARGET_LANGUAGE,
        src_sub=src_sub,
        tr_sub=tr_sub,
        src_part=src_part,
        align_parts_json=align_parts_json,
    )

## ================================================================
# @ step8_gen_audio_task.py @ step10_gen_audio.py
def get_subtitle_trim_prompt(text, duration):
 
    rule = '''Consider a. Reducing filler words without modifying meaningful content. b. Omitting unnecessary modifiers or pronouns, for example:
    - "Please explain your thought process" can be shortened to "Please explain thought process"
    - "We need to carefully analyze this complex problem" can be shortened to "We need to analyze this problem"
    - "Let's discuss the various different perspectives on this topic" can be shortened to "Let's discuss different perspectives on this topic"
    - "Can you describe in detail your experience from yesterday" can be shortened to "Can you describe yesterday's experience" '''

    trim_prompt = '''
### Task
As a subtitle editor, optimize the following text to fit {duration} seconds while preserving meaning:

<text>
{text}
</text>

Rules: {rule}

### Output in JSON
{{
    "analysis": "Brief analysis of the subtitle, including structure, key information, and potential processing locations",
    "result": "Optimized and shortened subtitle in the original subtitle language"
}}

### Your Answer, Provide ONLY a valid JSON object:
'''.strip()
    return trim_prompt.format(
        text=text,
        duration=duration,
        rule=rule
    )

## ================================================================
# @ tts_main
def get_correct_text_prompt(text):
    return f'''
### Task
Clean text for TTS: keep basic punctuation (.,?!) and preserve meaning.

### Input
{text}

### Output
{{
    "text": "cleaned text here"
}}

### Your Answer, Provide ONLY a valid JSON object:
'''.strip()
