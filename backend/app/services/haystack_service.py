import os
import sys
import json
from typing import List, Dict, Any, Optional


# Define a simple document class
class SimpleDocument:
    def __init__(self, content: str, meta: Optional[Dict[str, Any]] = None):
        self.content = content
        self.meta = meta or {}


# Simple keyword extractor
class SimpleKeywordExtractor:
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text"""
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Exclude short words
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]


# Simple Haystack service
class SimpleHaystackService:
    """Simplified Haystack service providing semantic analysis"""

    def __init__(self):
        """Initialize the service"""
        self.keyword_extractor = SimpleKeywordExtractor()

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text"""
        return self.keyword_extractor.extract_keywords(text, top_n)

    def process_structured_data(self, text: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process text and extract structured data (simulation)"""
        # If no schema is provided, use default schema
        if not schema:
            schema = {
                "title": "Title",
                "date": "Date",
                "participants": "Participant list",
                "agenda": "Agenda items",
                "decisions": "Decisions",
                "action_items": "Action items with assignees and deadlines"
            }

        # Return simulated structured data
        result = {}
        for key, description in schema.items():
            if key == "title":
                # Extract title (use first line)
                lines = text.split('\n')
                result[key] = lines[0] if lines else "No title"
            elif key == "date":
                # Extract date (simulation)
                result[key] = "2025-03-07"
            elif key == "participants":
                # Extract participants (simulation)
                result[key] = ["User1", "User2", "User3"]
            elif key == "agenda":
                # Extract agenda (simulation)
                result[key] = ["Topic1", "Topic2", "Topic3"]
            elif key == "decisions":
                # Extract decisions (simulation)
                result[key] = ["Decision1", "Decision2"]
            elif key == "action_items":
                # Extract action items (simulation)
                result[key] = [
                    {"item": "Task1", "assignee": "User1", "deadline": "2025-03-14"},
                    {"item": "Task2", "assignee": "User2", "deadline": "2025-03-21"}
                ]
            else:
                # Other fields
                result[key] = f"Sample value for {key}"

        return result

    def analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure (simulation)"""
        # Return simulated document structure
        return {
            "title": text.split('\n')[0] if text.split('\n') else "No title",
            "topics": ["Topic1", "Topic2", "Topic3"],
            "key_points": {
                "Topic1": ["Point1-1", "Point1-2"],
                "Topic2": ["Point2-1", "Point2-2"],
                "Topic3": ["Point3-1", "Point3-2"]
            },
            "decisions": ["Decision1", "Decision2"],
            "action_items": [
                {"item": "Task1", "assignee": "User1", "deadline": "2025-03-14"},
                {"item": "Task2", "assignee": "User2", "deadline": "2025-03-21"}
            ]
        }

    # Keep for backward compatibility
    def analyze_meeting_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure (for backward compatibility)"""
        return self.analyze_document_structure(text)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text (simulation)"""
        # Return simulated entities
        return {
            "people": ["Person1", "Person2", "Person3"],
            "organizations": ["Org1", "Org2"],
            "locations": ["Location1", "Location2"],
            "dates": ["2025-03-07", "2025-03-14"],
            "products": ["Product1", "Product2"]
        }


# Create a singleton instance
haystack_service = SimpleHaystackService() 