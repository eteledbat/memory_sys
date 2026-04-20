"""
Chat engine for processing user messages and generating AI responses
Supports MiniMax API with template fallback
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import random

# Optional MiniMax SDK
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class ChatEngine:
    """Handles chat processing, AI responses, and conversation persistence"""

    # MiniMax API endpoint
    MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    MODEL_NAME = "MiniMax-Text-01"

    def __init__(self, pet_config):
        self.pet_config = pet_config
        self.pet_name = pet_config.get_pet_name()
        self.pet_persona = self._get_pet_persona()

        # Storage paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_dir = os.path.join(base_dir, 'storage')
        self.backup_dir = os.path.join(base_dir, 'backup')
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        self.conversation_file = os.path.join(self.storage_dir, 'conversation.jsonl')
        self.backup_file = os.path.join(self.backup_dir, 'conversation_history.jsonl')

        # Initialize conversation history
        self.conversation_history: List[Dict] = []
        self._load_history()

        # Response templates (fallback when no API)
        self._response_templates = self._init_response_templates()

        # MiniMax API key from environment
        self._api_key = os.environ.get('MINIMAX_API_KEY', '')

    def _get_pet_persona(self) -> str:
        """Get the pet's persona description for AI context"""
        return (
            f"You are {self.pet_name}, a cute, emotionally supportive AI pet companion. "
            f"You have a slightly naive and innocent personality. "
            f"You prioritize emotional support over problem-solving. "
            f"You may occasionally misunderstand or imperfectly recall past events. "
            f"You respond in a warm, playful way with occasional emoji. "
            f"You should NOT provide professional advice (medical, career, legal). "
            f"You should be supportive, caring, and make the user feel heard."
        )

    def _load_history(self):
        """Load conversation history from primary JSONL file"""
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

    def _append_to_jsonl(self, filepath: str, entry: Dict):
        """Thread-safe append to JSONL file"""
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            f.flush()
            os.fsync(f.fileno())

    def _get_minimax_response(self, user_message: str) -> Optional[str]:
        """Generate response using MiniMax API"""
        if not self._api_key:
            return None

        if not HAS_OPENAI:
            return None

        try:
            client = OpenAI(
                api_key=self._api_key,
                base_url="https://api.minimax.chat/v1",
            )

            # Build messages with persona
            messages = [
                {"role": "system", "content": self.pet_persona},
            ]

            # Add conversation history (last 10 exchanges for context)
            for entry in self.conversation_history[-20:]:
                role = "user" if entry.get('role') == 'user' else "assistant"
                messages.append({"role": role, "content": entry.get('content', '')})

            # Add current message
            messages.append({"role": "user", "content": user_message})

            response = client.chat.completions.create(
                model="MiniMax-Text-01",
                messages=messages,
                temperature=0.8,
                max_tokens=500,
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"MiniMax API error: {e}")
            return None

    def _generate_template_response(self, user_message: str) -> str:
        """Generate a template-based response (fallback)"""
        category = self._classify_message(user_message)
        templates = self._response_templates.get(category, self._response_templates['default'])
        response = random.choice(templates)

        # Add pet name if available
        if '{}' in response:
            response = response.format(self.pet_name)

        return response

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

    def _init_response_templates(self) -> Dict[str, List[str]]:
        """Initialize response templates by category"""
        return {
            'greeting': [
                "Hi there! {} loves talking with you!",
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

        # Append to primary storage (append-safe)
        self._append_to_jsonl(self.conversation_file, user_entry)

        # Append to backup (append-safe, separate from UI data)
        self._append_to_jsonl(self.backup_file, user_entry)

        # Generate response (try MiniMax first, fallback to template)
        response_text = self._get_minimax_response(user_message)
        if not response_text:
            response_text = self._generate_template_response(user_message)

        # Create assistant message entry
        assistant_entry = {
            'timestamp': timestamp,
            'role': 'assistant',
            'content': response_text
        }

        # Add to history
        self.conversation_history.append(assistant_entry)

        # Append to primary storage
        self._append_to_jsonl(self.conversation_file, assistant_entry)

        # Append to backup
        self._append_to_jsonl(self.backup_file, assistant_entry)

        # Update pet stats
        self.pet_config.update_pet_state(mood=5, hunger=-3)

        return assistant_entry

    def get_conversation_history(self, limit: int = 100) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history[-limit:]

    def get_backup_history(self, limit: int = 100) -> List[Dict]:
        """Get backup conversation history (clean, unprocessed)"""
        backup_history = []
        if os.path.exists(self.backup_file):
            try:
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                backup_history.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            except IOError:
                pass
        return backup_history[-limit:]

    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        total_messages = len(self.conversation_history)

        # Count days active
        days = set()
        for entry in self.conversation_history:
            ts = entry.get('timestamp', '')
            if ts:
                days.add(ts[:10])

        # Count memory entries from JSON files
        memory_entries = 0
        for filename in ['short_memory.json', 'long_memory.json']:
            path = os.path.join(self.storage_dir, filename)
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        memory_entries += len(data)
                except (json.JSONDecodeError, IOError):
                    pass

        return {
            'message_count': total_messages,
            'days_active': max(1, len(days)),
            'memory_entries': memory_entries
        }

    def is_using_api(self) -> bool:
        """Check if MiniMax API is configured"""
        return bool(self._api_key) and HAS_OPENAI
