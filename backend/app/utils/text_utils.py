"""
Text utility functions for the report generation system.
This module provides functions for text processing and analysis.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Initialize logger
logger = logging.getLogger(__name__)

# Download required NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK resources: {e}")

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Get stopwords
try:
    stop_words = set(stopwords.words('english'))
except Exception as e:
    logger.warning(f"Failed to load stopwords: {e}")
    stop_words = set()

def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def split_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into chunks of specified size with overlap.
    
    Args:
        text: Input text to split
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # If text is shorter than chunk_size, return it as is
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Get chunk of size chunk_size or remaining text if shorter
        end = min(start + chunk_size, len(text))
        
        # If not at the end of text, try to find a sentence boundary
        if end < len(text):
            # Look for the last sentence boundary within the chunk
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            
            # Use the latest sentence boundary found
            if last_period > start:
                end = last_period + 1
            elif last_newline > start:
                end = last_newline + 1
        
        # Add the chunk to the list
        chunks.append(text[start:end])
        
        # Move the start position for the next chunk, considering overlap
        start = end - overlap
        
        # Ensure we're making progress
        if start >= end:
            start = end
    
    return chunks

def extract_keywords(text: str, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Extract keywords from text.
    
    Args:
        text: Input text to extract keywords from
        top_n: Number of top keywords to return
        
    Returns:
        List of dictionaries with keywords and their scores
    """
    if not text:
        return []
    
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Tokenize
    words = word_tokenize(cleaned_text)
    
    # Remove stopwords and lemmatize
    filtered_words = []
    for word in words:
        if word not in stop_words and len(word) > 2:
            filtered_words.append(lemmatizer.lemmatize(word))
    
    # Count word frequencies
    word_freq = {}
    for word in filtered_words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    
    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N keywords with normalized scores
    max_freq = sorted_words[0][1] if sorted_words else 1
    
    keywords = []
    for word, freq in sorted_words[:top_n]:
        keywords.append({
            "text": word,
            "score": round(freq / max_freq, 2)
        })
    
    return keywords

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Create a simple extractive summary of the text.
    
    Args:
        text: Input text to summarize
        max_sentences: Maximum number of sentences in the summary
        
    Returns:
        Summarized text
    """
    if not text:
        return ""
    
    # Split into sentences
    sentences = sent_tokenize(text)
    
    # If there are fewer sentences than max_sentences, return the original text
    if len(sentences) <= max_sentences:
        return text
    
    # Simple scoring: prefer sentences at the beginning and end of the document
    scores = {}
    for i, sentence in enumerate(sentences):
        # Score based on position (higher for first and last few sentences)
        position_score = 1.0
        if i < 3:  # First three sentences
            position_score = 1.0 - (i * 0.1)
        elif i >= len(sentences) - 3:  # Last three sentences
            position_score = 0.8 + ((i - (len(sentences) - 3)) * 0.1)
        else:
            position_score = 0.5
        
        # Score based on length (prefer medium-length sentences)
        length = len(sentence.split())
        length_score = 0.5
        if 5 <= length <= 25:
            length_score = 1.0
        elif length < 5:
            length_score = 0.3
        
        # Final score
        scores[i] = position_score * 0.7 + length_score * 0.3
    
    # Get indices of top-scoring sentences
    top_indices = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
    top_indices = [idx for idx, _ in sorted(top_indices)]
    
    # Construct summary from selected sentences in original order
    summary_sentences = [sentences[i] for i in sorted(top_indices)]
    
    return ' '.join(summary_sentences) 