"""
Chat engine for processing user messages and generating AI responses
"""

import json
import os
from datetime import datetime
from typing import List, Dict
import random


class ChatEngine:
    """Handles chat processing and conversation persistence"""

    def __init__(self, pet_config):
        self.pet_config = pet_config
        self.pet_name = pet_config.get_pet_name()
        self.conversation_file = self._get_conversation_file()

        # Initialize conversation history
        self.conversation_history: List[Dict] = []
        self._load_history()

        # Response templates for placeholder AI
        self._response_templates = self._init_response_templates()

    def _get_conversation_file(self) -> str:
        """Get the conversation JSONL file path"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        storage_dir = os.path.join(base_dir, 'storage')
        os.makedirs(storage_dir, exist_ok=True)
        return os.path.join(storage_dir, 'conversation.jsonl')

    def _load_history(self):
        """Load conversation history from JSONL file"""
        if os.path.exists(self.conversation_file):
            try:
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                self.conversation_history.append(entry)
                            except json.JSONDecodeError:
                                continue
            except IOError:
                pass

    def _append_to_jsonl(self, entry: Dict):
        """Thread-safe append to JSONL file"""
        with open(self.conversation_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            f.flush()
            os.fsync(f.fileno())

    def _init_response_templates(self) -> Dict[str, List[str]]:
        """Initialize response templates by category"""
        return {
            'greeting': [
                "Hi there! {} Love talking with you!",
                "Hey! How are you doing today?",
                "Hello! I missed you! What's up?",
            ],
            'question': [
                "That's interesting! Tell me more~",
                "Hmm, I'm not sure but let me think about it...",
                "Great question! What do you think?",
            ],
            'emotion_positive': [
                "Yay! I'm so happy to hear that!",
                "That's wonderful! You make me so happy!",
                "I love hearing things like that!",
            ],
            'emotion_negative': [
                "Aww, I'm here for you. Want to talk about it?",
                "I understand... I'm always here to listen.",
                "That sounds tough. I'm sending you virtual hugs!",
            ],
            'neutral': [
                "I see! What else is on your mind?",
                "Interesting! Tell me more!",
                "Okay! I'm listening~",
            ],
            'food': [
                "Ooh food! That sounds yummy!",
                "Yum! I wish I could taste it!",
                "Food is the best! What are you having?",
            ],
            'work': [
                "Work stuff can be tricky. Hang in there!",
                "I believe in you! You're doing great!",
                "Take it one step at a time!",
            ],
            'love': [
                "That's so sweet! You have a big heart!",
                "Love is the best feeling!",
                "That's beautiful! 💕",
            ],
            'sad': [
                "I'm sorry you're feeling down. I'm here for you.",
                "Sending you gentle hugs and love. It'll be okay.",
                "Take care of yourself, okay? I'm always here.",
            ],
            'default': [
                "I hear you! Tell me more~",
                "That's interesting! What happened next?",
                "I love our conversations! What's on your mind?",
                "Mhm! And how did that make you feel?",
                "Wow! I'm learning so much about you!",
            ]
        }

    def _classify_message(self, message: str) -> str:
        """Classify the user message to determine response category"""
        msg_lower = message.lower()

        if any(g in msg_lower for g in ['hi', 'hello', 'hey', 'yo']):
            return 'greeting'
        elif any(q in msg_lower for q in ['what', 'how', 'why', 'when', 'where', 'who']):
            return 'question'
        elif any(p in msg_lower for p in ['happy', 'excited', 'great', 'amazing', 'love', 'yay']):
            return 'emotion_positive'
        elif any(n in msg_lower for n in ['sad', 'angry', 'frustrated', 'upset', 'cry']):
            return 'emotion_negative'
        elif any(f in msg_lower for f in ['food', 'eat', 'hungry', 'lunch', 'dinner', 'breakfast']):
            return 'food'
        elif any(w in msg_lower for w in ['work', 'job', 'boss', 'meeting', 'project']):
            return 'work'
        elif any(l in msg_lower for l in ['love', 'miss', 'care']):
            return 'love'

        return 'neutral'

    def _generate_response(self, user_message: str) -> str:
        """Generate a placeholder AI response"""
        category = self._classify_message(user_message)
        templates = self._response_templates.get(category, self._response_templates['default'])
        response = random.choice(templates)

        # Add pet name if available
        if '{}' in response:
            response = response.format(self.pet_name)

        return response

    def process_message(self, user_message: str) -> Dict:
        """Process a user message and return AI response"""
        timestamp = datetime.now().isoformat()

        # Create user message entry
        user_entry = {
            'timestamp': timestamp,
            'role': 'user',
            'content': user_message
        }

        # Add to history
        self.conversation_history.append(user_entry)

        # Append to JSONL (append-safe)
        self._append_to_jsonl(user_entry)

        # Generate response
        response_text = self._generate_response(user_message)

        # Create assistant message entry
        assistant_entry = {
            'timestamp': timestamp,
            'role': 'assistant',
            'content': response_text
        }

        # Add to history
        self.conversation_history.append(assistant_entry)

        # Append to JSONL (append-safe)
        self._append_to_jsonl(assistant_entry)

        # Update pet stats
        self.pet_config.update_pet_state(mood=5, hunger=-3)

        return assistant_entry

    def get_conversation_history(self, limit: int = 100) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history[-limit:]

    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        total_messages = len(self.conversation_history)

        # Count days active
        days = set()
        for entry in self.conversation_history:
            ts = entry.get('timestamp', '')
            if ts:
                days.add(ts[:10])

        # Count memory entries
        memory_entries = 0
        storage_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'storage'
        )
        for filename in ['short_memory.csv', 'long_memory.csv']:
            path = os.path.join(storage_dir, filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    memory_entries += sum(1 for _ in f) - 1

        return {
            'message_count': total_messages,
            'days_active': max(1, len(days)),
            'memory_entries': memory_entries
        }
