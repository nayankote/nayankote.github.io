#!/usr/bin/env python3
"""
Intelligent Notes Parser
Converts raw text notes into structured JSON with auto-tagging.
Supports both keyword-based and LLM-based tagging.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

# ============================================
# TAG CONFIGURATION - Easy to edit!
# ============================================

# Define your tag clusters with keywords
# Add/remove tags easily by editing this dictionary
TAG_CLUSTERS = {
    'personal': {
        'keywords': ['friend', 'family', 'reflection', 'grateful', 'gratitude', 
                    'meditation', 'feel', 'feeling', 'emotion', 'relationship'],
        'weight': 1.0
    },
    'work': {
        'keywords': ['code', 'project', 'meeting', 'api', 'design', 'development',
                    'team', 'deadline', 'feature', 'bug', 'deploy', 'production'],
        'weight': 1.0
    },
    'fitness': {
        'keywords': ['workout', 'run', 'yoga', 'exercise', 'gym', 'training',
                    'strength', 'cardio', 'muscle', 'lift', 'rep'],
        'weight': 1.0
    },
    'ironman': {
        'keywords': ['swim', 'bike', 'triathlon', 'ironman', 'race', '70.3',
                    'transition', 'endurance', 'marathon'],
        'weight': 1.2  # Higher weight = more likely to tag
    },
    'thinking': {
        'keywords': ['idea', 'thought', 'philosophy', 'wonder', 'question',
                    'reflect', 'consider', 'ponder', 'contemplat'],
        'weight': 1.0
    },
    'til': {
        'keywords': ['learned', 'discovered', 'til', 'today i learned', 
                    'finally understood', 'realized', 'figured out'],
        'weight': 1.3
    },
    'startups': {
        'keywords': ['startup', 'founder', 'venture', 'funding', 'pivot',
                    'product-market fit', 'mvp', 'launch', 'scale', 'growth'],
        'weight': 1.1
    },
    'ideas': {
        'keywords': ['what if', 'could build', 'imagine', 'concept', 'brainstorm',
                    'innovation', 'creative', 'new approach'],
        'weight': 1.0
    },
    'mental-health': {
        'keywords': ['therapy', 'anxiety', 'depression', 'mental health',
                    'wellbeing', 'stress', 'burnout', 'mindfulness', 'self-care'],
        'weight': 1.2
    },
    'career': {
        'keywords': ['career', 'job', 'promotion', 'salary', 'interview',
                    'resume', 'linkedin', 'networking', 'professional'],
        'weight': 1.0
    },
    'motivation': {
        'keywords': ['motivat', 'inspir', 'push', 'drive', 'determina',
                    'discipline', 'consistency', 'persist'],
        'weight': 0.9
    }
}

# Minimum confidence score for a tag (0.0 to 1.0)
MIN_TAG_CONFIDENCE = 0.3

# Maximum tags per note
MAX_TAGS_PER_NOTE = 3

# LLM Configuration (optional)
USE_LLM = False  # Set to True to use Claude for semantic tagging
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# ============================================
# KEYWORD-BASED TAGGING
# ============================================

class KeywordTagger:
    """Fast, keyword-based auto-tagger"""
    
    def __init__(self, tag_clusters: Dict):
        self.tag_clusters = tag_clusters
    
    def tag_note(self, text: str) -> List[tuple]:
        """
        Tag a note based on keyword matching.
        Returns list of (tag, confidence) tuples.
        """
        text_lower = text.lower()
        scores = {}
        
        for tag, config in self.tag_clusters.items():
            score = 0.0
            keywords = config['keywords']
            weight = config.get('weight', 1.0)
            
            # Count keyword matches
            matches = 0
            for keyword in keywords:
                if keyword in text_lower:
                    matches += 1
            
            if matches > 0:
                # Calculate confidence based on matches
                # More matches = higher confidence
                base_score = min(matches / len(keywords), 1.0)
                score = base_score * weight
                scores[tag] = score
        
        # Filter and sort by confidence
        tagged = [(tag, score) for tag, score in scores.items() 
                  if score >= MIN_TAG_CONFIDENCE]
        tagged.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N tags
        return tagged[:MAX_TAGS_PER_NOTE]

# ============================================
# LLM-BASED TAGGING (Optional)
# ============================================

class LLMTagger:
    """Semantic tagging using Claude API"""
    
    def __init__(self, api_key: str, available_tags: List[str]):
        self.api_key = api_key
        self.available_tags = available_tags
    
    def tag_note(self, text: str) -> List[str]:
        """
        Tag a note using Claude for semantic understanding.
        Returns list of tags.
        """
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            prompt = f"""Analyze this note and assign 1-3 relevant tags from this list:
{', '.join(self.available_tags)}

Note: "{text}"

Return ONLY the tags as a comma-separated list, nothing else.
Choose tags that best capture the main topic(s) of the note."""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            tags_text = message.content[0].text.strip()
            tags = [tag.strip().lower() for tag in tags_text.split(',')]
            
            # Validate tags
            valid_tags = [tag for tag in tags if tag in self.available_tags]
            return valid_tags[:MAX_TAGS_PER_NOTE]
            
        except Exception as e:
            print(f"LLM tagging failed: {e}")
            print("Falling back to keyword tagging...")
            return []

# ============================================
# NOTES PARSER
# ============================================

class NotesParser:
    """Main parser class"""
    
    def __init__(self, use_llm: bool = False):
        self.keyword_tagger = KeywordTagger(TAG_CLUSTERS)
        self.llm_tagger = None
        
        if use_llm and ANTHROPIC_API_KEY:
            available_tags = list(TAG_CLUSTERS.keys())
            self.llm_tagger = LLMTagger(ANTHROPIC_API_KEY, available_tags)
        
        self.notes = []
    
    def generate_id(self, text: str, date: str) -> int:
        """Generate unique ID from text and date"""
        content = f"{text}{date}"
        hash_obj = hashlib.md5(content.encode())
        # Convert first 8 hex chars to int
        return int(hash_obj.hexdigest()[:8], 16)
    
    def extract_title(self, text: str, max_length: int = 60) -> str:
        """Extract or generate a title from the note"""
        # If text starts with a clear title pattern (short first line)
        lines = text.split('\n')
        first_line = lines[0].strip()
        
        if len(first_line) < max_length and len(lines) > 1:
            return first_line
        
        # Otherwise, create title from first few words
        words = text.split()
        if len(words) <= 5:
            return text
        
        title = ' '.join(words[:5])
        if len(title) > max_length:
            title = title[:max_length-3] + '...'
        else:
            title += '...'
        
        return title
    
    def parse_note_file(self, filepath: Path) -> Optional[Dict]:
        """Parse a single note file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            if not text:
                return None
            
            # Extract date from filename or use file modification time
            date = self._extract_date(filepath)
            
            # Generate title
            title = self.extract_title(text)
            
            # Tag the note
            if self.llm_tagger:
                tags = self.llm_tagger.tag_note(text)
                if not tags:  # Fallback to keyword
                    tagged = self.keyword_tagger.tag_note(text)
                    tags = [tag for tag, _ in tagged]
            else:
                tagged = self.keyword_tagger.tag_note(text)
                tags = [tag for tag, _ in tagged]
            
            # Ensure at least one tag
            if not tags:
                tags = ['uncategorized']
            
            # Generate ID
            note_id = self.generate_id(text, date)
            
            return {
                'id': note_id,
                'title': title,
                'tags': tags,
                'date': date,
                'text': text,
                'source': filepath.name
            }
            
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return None
    
    def _extract_date(self, filepath: Path) -> str:
        """Extract date from filename or use file modification time"""
        # Try to find date in filename (YYYY-MM-DD format)
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, filepath.name)
        
        if match:
            return match.group(1)
        
        # Use file modification time
        mtime = filepath.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    
    def parse_directory(self, directory: Path) -> List[Dict]:
        """Parse all note files in a directory"""
        notes = []
        
        # Support multiple file types
        patterns = ['*.txt', '*.md', '*.note']
        
        for pattern in patterns:
            for filepath in directory.glob(pattern):
                note = self.parse_note_file(filepath)
                if note:
                    notes.append(note)
        
        # Sort by date (newest first)
        notes.sort(key=lambda x: x['date'], reverse=True)
        
        return notes
    
    def save_to_json(self, notes: List[Dict], output_path: Path):
        """Save notes to JSON file"""
        data = {
            'notes': notes,
            'generated_at': datetime.now().isoformat(),
            'total_notes': len(notes)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(notes)} notes to {output_path}")

# ============================================
# QUICK RETAG FUNCTION
# ============================================

def retag_existing_notes(json_path: Path, use_llm: bool = False):
    """
    Retag existing notes with updated tag configuration.
    Useful when you add/remove tags and want to re-process everything.
    """
    print("Re-tagging existing notes...")
    
    # Load existing notes
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    notes = data['notes']
    parser = NotesParser(use_llm=use_llm)
    
    # Re-tag each note
    for note in notes:
        if parser.llm_tagger:
            tags = parser.llm_tagger.tag_note(note['text'])
            if not tags:
                tagged = parser.keyword_tagger.tag_note(note['text'])
                tags = [tag for tag, _ in tagged]
        else:
            tagged = parser.keyword_tagger.tag_note(note['text'])
            tags = [tag for tag, _ in tagged]
        
        note['tags'] = tags if tags else ['uncategorized']
    
    # Save back
    parser.save_to_json(notes, json_path)
    print("✓ Re-tagging complete!")

# ============================================
# CLI INTERFACE
# ============================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Parse notes and generate tags automatically'
    )
    
    parser.add_argument(
        'input_dir',
        type=Path,
        help='Directory containing note files (.txt, .md)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path('notes.json'),
        help='Output JSON file (default: notes.json)'
    )
    
    parser.add_argument(
        '--llm',
        action='store_true',
        help='Use Claude API for semantic tagging (requires ANTHROPIC_API_KEY)'
    )
    
    parser.add_argument(
        '--retag',
        type=Path,
        help='Retag existing notes.json file with updated configuration'
    )
    
    args = parser.parse_args()
    
    # Retag mode
    if args.retag:
        retag_existing_notes(args.retag, use_llm=args.llm)
        return
    
    # Parse mode
    if not args.input_dir.exists():
        print(f"Error: Directory {args.input_dir} does not exist")
        return
    
    print(f"Parsing notes from: {args.input_dir}")
    print(f"Using {'LLM' if args.llm else 'keyword'} tagging")
    
    parser = NotesParser(use_llm=args.llm)
    notes = parser.parse_directory(args.input_dir)
    
    if notes:
        parser.save_to_json(notes, args.output)
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"   Total notes: {len(notes)}")
        
        tag_counts = {}
        for note in notes:
            for tag in note['tags']:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        print(f"   Tag distribution:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      {tag}: {count}")
    else:
        print("No notes found!")

if __name__ == '__main__':
    main()
