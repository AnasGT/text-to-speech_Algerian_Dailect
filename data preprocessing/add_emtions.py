import pandas as pd
import json
import re

from pathlib import Path

# Define path to the Excel file
FILE_PATH = Path(r"C:\Users\ANAS\Desktop\Egyptian-Text-To-Speech-main\inhancing_chunking\6_audio_chunks_report_with_emotions_with_phonemes.xlsx")

# Load the data
df = pd.read_excel(FILE_PATH)

# Helper to parse the Detected_Emotions field safely
def parse_emotions(cell):
    if pd.isna(cell) or not isinstance(cell, str):
        return {}
    try:
        return json.loads(cell)
    except json.JSONDecodeError:
        # Try single quotes
        try:
            return json.loads(cell.replace("'", '"'))
        except:
            return {}


def insert_emotions_into_transcript(row):
    """
    Given a DataFrame row with:
      - 'Start Time (ms)'
      - 'Duration (s)'
      - 'corrected_Transcript'
      - 'Detected_Emotions'
    returns transcript with emotion tags inserted at correct word positions.
    """
    transcript = row['Transcript']
    emotions = parse_emotions(row['Detected_Emotions'])
    # No emotions: return original
    if not emotions:
        return transcript

    # Split transcript into words and compute timings per word
    words = transcript.split()
    if not words:
        return transcript

    # Convert chunk start to seconds
    chunk_start_sec = row['Start Time (ms)'] / 1000.0
    duration = row['Duration (s)']
    time_per_word = duration / len(words)

    # Build a list of (word, word_start, word_end)
    word_times = []
    for idx, word in enumerate(words):
        w_start = chunk_start_sec + idx * time_per_word
        w_end = w_start + time_per_word
        # Ensure last word ends exactly at chunk end
        if idx == len(words) - 1:
            w_end = chunk_start_sec + duration
        word_times.append((idx, word, w_start, w_end))

    # For each emotion, find where to insert
    # Collect inserts: dict of idx -> list of tags
    inserts = {}
    for emotion, props in emotions.items():
        start = props.get('start_time', None)
        if start is None:
            continue
        # Absolute time
        abs_start = chunk_start_sec + start
        # Find word index
        for idx, word, w_start, w_end in word_times:
            if w_start <= abs_start < w_end:
                inserts.setdefault(idx, []).append(emotion)
                break
    
    # Rebuild transcript with tags
    out_words = []
    for idx, word in enumerate(words):
        if idx in inserts:
            # multiple emotions: concatenate
            tags = ''.join(f"<{e}>" for e in inserts[idx])
            out_words.append(tags)
        out_words.append(word)
    
    return ' '.join(out_words)

# Apply to DataFrame
df['transcript_with_emotions'] = df.apply(insert_emotions_into_transcript, axis=1)

# Optionally save to new Excel file
OUTPUT_PATH = r'C:\Users\ANAS\Desktop\Egyptian-Text-To-Speech-main\inhancing_chunking\7_audio_chunks_report_with_emotions_with_phonemes_and_emo.xlsx'
df.to_excel(OUTPUT_PATH, index=False)
print(f"Saved updated transcripts to: {OUTPUT_PATH}")