"""
Text Processors Module

This module provides utility functions for processing lyrics, including:
- Cleaning raw lyrics.
- Romanizing Japanese text using SudachiPy for tokenization and Pykakasi for romanization.
- A final formatting function to ensure consistent capitalization and spacing.
"""

# Standard library imports
import re

# Local application imports
from src.extensions import KKS_CONVERTER as kks
from src.extensions import TOKENIZER_OBJ as tokenizer

# --- Constants for Performance and Clarity ---
JAPANESE_REGEX = re.compile(
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f]"
)

PARTICLE_MAP = {
    ("は", "助詞"): "wa",
    ("へ", "助詞"): "e",
    ("を", "助詞"): "o",
}

PUNCTUATION_MAP = str.maketrans({
    "、": ",", "。": ".", "…": "...", "「": '"', "」": '"',
    "『": '"', "』": '"', "？": "?", "！": "!", "　": " "
})

# --- Helper Functions ---

def is_japanese_text(text: str) -> bool:
    """
    Check if a string contains any Japanese characters using a pre-compiled regex.
    """
    return JAPANESE_REGEX.search(text) is not None

def clean_genius_metadata(lyrics: str) -> str:
    """Remove unwanted boilerplate metadata and lines from raw Genius lyrics."""
    if not isinstance(lyrics, str):
        return "[Error: Invalid input]"
    
    lyrics = re.sub(r"^\d+\s*Contributors?.+?Lyrics\s*", "", lyrics, flags=re.DOTALL | re.IGNORECASE)
    lyrics = re.sub(r"\d*You might also like.*", "", lyrics, flags=re.DOTALL | re.IGNORECASE)
    lyrics = re.sub(r"\d+Embed$", "", lyrics.strip())
    lyrics = re.sub(r"\[[^\]]*\]", "", lyrics)
    lyrics = lyrics.replace('\u200b', '')

    cleaned_lines = []
    for line in lyrics.splitlines():
        if re.search(r"[。？！」]?\s*English:", line, re.IGNORECASE):
            continue
        if re.match(r"^\s*The first thing you can do is to.*", line, re.IGNORECASE):
            continue
        cleaned_lines.append(line)
    
    lyrics = "\n".join(cleaned_lines)
    lyrics = re.sub(r"(\r\n|\r|\n){2,}", "\n\n", lyrics)
    
    return lyrics.strip()

def format_processed_text(text: str) -> str:
    """
    Applies final formatting to a block of processed text.
    """
    if not text or not isinstance(text, str):
        return text or ""

    lines = text.splitlines()
    formatted_lines = []
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            formatted_lines.append("")
            continue
        
        single_spaced_line = re.sub(r'\s+', ' ', stripped_line)
        
        if single_spaced_line:
            capitalized_line = single_spaced_line[0].upper() + single_spaced_line[1:]
            formatted_lines.append(capitalized_line)
        
    return "\n".join(formatted_lines)

# --- Main Romanization Logic ---

def romanize_lyrics(lyrics: str) -> str:
    """
    Romanize Japanese lyrics using a more accurate, context-aware approach.
    """
    if not lyrics or not isinstance(lyrics, str):
        return lyrics or "[Error: Invalid input]"

    romanized_lines = []
    lines = lyrics.splitlines()

    for line in lines:
        if not is_japanese_text(line):
            romanized_lines.append(line)
            continue
        
        try:
            tokens = tokenizer.tokenize(line, tokenizer.SplitMode.C)
            processed_line = []
            
            for i, token in enumerate(tokens):
                surface = token.surface()
                reading = token.reading_form()
                pos_tuple = (surface, token.part_of_speech()[0])

                if pos_tuple in PARTICLE_MAP:
                    processed_line.append(PARTICLE_MAP[pos_tuple])
                    continue

                if not is_japanese_text(surface):
                    processed_line.append(surface)
                    continue

                text_to_convert = reading if reading else surface
                romaji_parts = kks.convert(text_to_convert)
                current_romaji = "".join([part['hepburn'] for part in romaji_parts])
                
                if "っ" in reading or "ッ" in reading:
                    if i + 1 < len(tokens):
                        next_token = tokens[i+1]
                        if is_japanese_text(next_token.surface()):
                            next_token_reading = next_token.reading_form() or next_token.surface()
                            next_romaji_full = "".join([p['hepburn'] for p in kks.convert(next_token_reading)])
                            
                            first_consonant = ''
                            for char in next_romaji_full:
                                if char not in 'aeiouAEIOU':
                                    first_consonant = char
                                    break
                            
                            if first_consonant:
                                if next_romaji_full.startswith('ch'):
                                    current_romaji = current_romaji.replace('tsu', 't')
                                else:
                                    current_romaji = current_romaji.replace('tsu', first_consonant)
                    else:
                        current_romaji = current_romaji.replace('tsu', '')
                
                processed_line.append(current_romaji)

            final_line = " ".join(processed_line).translate(PUNCTUATION_MAP)
            romanized_lines.append(final_line)

        except Exception as e:
            romanized_lines.append(f"[Error processing line: {line} ({e})]")

    return format_processed_text("\n".join(romanized_lines))