"""
Advanced Memory Pipeline for Sweekar
Integrates features from demo_sweekar1.0:
- Score-based eviction with recency/importance/access tracking
- Trait strength with weighted moving average decay
- Short-term to long-term promotion based on computed scores
- Emotional valence estimation
- Access count incrementing on retrieval
"""

import csv
import json
import os
import uuid
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict


# ============================================================================
# Data Classes (from demo_sweekar1.0)
# ============================================================================

@dataclass
class ProfileEvent:
    """Raw evidence extracted from conversations - append-only"""
    event_id: str
    user_id: str
    timestamp: float
    event_type: str  # emotion, preference, fact, relationship, goal
    signal: str  # extracted signal description
    raw_text: str  # original text snippet
    confidence: float  # how confident we are in extraction
    source_message_id: str


@dataclass
class ProfileTrait:
    """Aggregated trait with stability tracking using weighted moving average"""
    trait_name: str
    value: str
    strength: float  # 0.0 to 1.0, stability score
    last_updated: float
    evidence_count: int
    last_signal: str  # most recent signal supporting this trait

    def update(self, new_value: str, signal_strength: float):
        """Update trait using weighted moving average: new = old * 0.8 + signal * 0.2"""
        self.strength = self.strength * 0.8 + signal_strength * 0.2
        self.value = new_value
        self.last_updated = time.time()
        self.evidence_count += 1
        self.last_signal = new_value


@dataclass
class ShortTermMemory:
    """Short-term memory entry with importance, recency, access tracking"""
    memory_id: str
    content: str
    importance: float  # 0.0 to 1.0, how important
    recency: float  # 0.0 to 1.0, how recent
    access_count: int
    created_at: float
    last_accessed: float
    memory_type: str  # event, preference, fact, emotional
    tags: List[str]

    def compute_score(self) -> float:
        """Compute relevance score for eviction decisions
        score = 0.5 * recency + 0.3 * importance + 0.2 * (access_count / 10)
        """
        time_elapsed = time.time() - self.created_at
        recency_score = max(0, 1.0 - (time_elapsed / (7 * 24 * 3600)))  # 7-day decay
        self.recency = recency_score

        score = 0.5 * recency_score + 0.3 * self.importance + 0.2 * (self.access_count / 10)
        return min(score, 1.0)


@dataclass
class LongTermMemory:
    """Long-term memory with retrieval statistics"""
    memory_id: str
    content: str
    event_type: str
    importance_base: float
    retrieval_count: int
    last_retrieved: float
    created_at: float
    emotional_valence: float  # positive/negative intensity (-1 to +1)
    related_traits: List[str]


# ============================================================================
# Memory Pipeline
# ============================================================================

class MemoryPipeline:
    """
    Advanced memory pipeline with:
    - 3-layer memory (events, short-term, long-term)
    - Score-based eviction
    - Trait strength evolution
    - Emotional valence tracking
    """

    SHORT_TERM_LIMIT = 50
    EVICTION_BATCH_SIZE = 5
    LTM_PROMOTION_THRESHOLD = 0.2
    LTM_ACCESS_THRESHOLD = 2
    RETRIEVAL_DECAY_DAYS = 30

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.base_dir = base_dir
        self.storage_dir = os.path.join(base_dir, 'storage')
        self.conversation_file = os.path.join(self.storage_dir, 'conversation.jsonl')

        # In-memory caches
        self.short_term: Dict[str, ShortTermMemory] = {}
        self.long_term: Dict[str, LongTermMemory] = {}
        self.traits: Dict[str, ProfileTrait] = {}
        self.pending_events: List[ProfileEvent] = []

        os.makedirs(self.storage_dir, exist_ok=True)

        # Load existing data
        self._load_all_data()
        self._ensure_storage_files()

    def _ensure_storage_files(self):
        """Ensure all storage files exist with proper headers"""
        files = {
            'short_memory.json': None,  # JSON format
            'long_memory.json': None,   # JSON format
            'profile_traits.csv': ['trait_name', 'value', 'strength', 'last_updated',
                                   'evidence_count', 'last_signal'],
            'profile_events.csv': ['event_id', 'user_id', 'timestamp', 'event_type',
                                  'signal', 'raw_text', 'confidence', 'source_message_id'],
        }

        for filename, headers in files.items():
            filepath = os.path.join(self.storage_dir, filename)
            if not os.path.exists(filepath):
                if filename.endswith('.json'):
                    with open(filepath, 'w') as f:
                        json.dump({}, f)
                else:
                    with open(filepath, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)

    def _load_all_data(self):
        """Load all memory data from storage into memory"""
        # Load short-term memory
        stm_file = os.path.join(self.storage_dir, 'short_memory.json')
        if os.path.exists(stm_file):
            try:
                with open(stm_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for mem_id, mem_data in data.items():
                        mem_data['tags'] = mem_data.get('tags', [])
                        self.short_term[mem_id] = ShortTermMemory(**mem_data)
            except (json.JSONDecodeError, IOError):
                pass

        # Load long-term memory
        ltm_file = os.path.join(self.storage_dir, 'long_memory.json')
        if os.path.exists(ltm_file):
            try:
                with open(ltm_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for mem_id, mem_data in data.items():
                        mem_data['related_traits'] = mem_data.get('related_traits', [])
                        self.long_term[mem_id] = LongTermMemory(**mem_data)
            except (json.JSONDecodeError, IOError):
                pass

        # Load traits
        traits_file = os.path.join(self.storage_dir, 'profile_traits.csv')
        if os.path.exists(traits_file):
            try:
                with open(traits_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.traits[row['trait_name']] = ProfileTrait(
                            trait_name=row['trait_name'],
                            value=row['value'],
                            strength=float(row['strength']),
                            last_updated=float(row['last_updated']),
                            evidence_count=int(row['evidence_count']),
                            last_signal=row.get('last_signal', '')
                        )
            except (IOError, KeyError):
                pass

    # =========================================================================
    # Persistence
    # =========================================================================

    def _persist_short_term(self):
        """Persist short-term memory to JSON"""
        stm_file = os.path.join(self.storage_dir, 'short_memory.json')
        data = {k: asdict(v) for k, v in self.short_term.items()}
        with open(stm_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _persist_long_term(self):
        """Persist long-term memory to JSON"""
        ltm_file = os.path.join(self.storage_dir, 'long_memory.json')
        data = {k: asdict(v) for k, v in self.long_term.items()}
        with open(ltm_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _persist_traits(self):
        """Persist traits to CSV"""
        traits_file = os.path.join(self.storage_dir, 'profile_traits.csv')
        with open(traits_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['trait_name', 'value', 'strength', 'last_updated',
                           'evidence_count', 'last_signal'])
            for trait in self.traits.values():
                writer.writerow([
                    trait.trait_name, trait.value, f"{trait.strength:.4f}",
                    f"{trait.last_updated:.0f}", trait.evidence_count, trait.last_signal
                ])

    def _persist_profile_events(self):
        """Append-only persistence of raw events"""
        events_file = os.path.join(self.storage_dir, 'profile_events.csv')
        file_exists = os.path.exists(events_file)

        with open(events_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['event_id', 'user_id', 'timestamp', 'event_type',
                               'signal', 'raw_text', 'confidence', 'source_message_id'])
            for event in self.pending_events:
                writer.writerow([
                    event.event_id, event.user_id, f"{event.timestamp:.0f}",
                    event.event_type, event.signal, event.raw_text,
                    f"{event.confidence:.2f}", event.source_message_id
                ])
        self.pending_events.clear()

    def _persist_pet_state_csv(self):
        """Update pet state CSV"""
        config_dir = os.path.join(self.base_dir, 'config')
        pet_state_file = os.path.join(config_dir, 'pet_state.json')
        pet_state_csv = os.path.join(self.storage_dir, 'pet_state.csv')

        if os.path.exists(pet_state_file):
            try:
                with open(pet_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                with open(pet_state_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['mood', 'hunger', 'health', 'total_interactions', 'last_updated'])
                    writer.writerow([
                        state.get('mood', 80), state.get('hunger', 70),
                        state.get('health', 90), state.get('total_interactions', 0),
                        datetime.now().isoformat()
                    ])
            except (IOError, json.JSONDecodeError):
                pass

    def persist_all(self):
        """Persist all memory layers"""
        self._persist_profile_events()
        self._persist_traits()
        self._persist_short_term()
        self._persist_long_term()
        self._persist_pet_state_csv()

    # =========================================================================
    # Memory Operations
    # =========================================================================

    def _estimate_importance(self, event_type: str) -> float:
        """Estimate memory importance based on event type"""
        importance_map = {
            'emotion': 0.8,
            'relationship': 0.9,
            'goal': 0.7,
            'preference': 0.5,
            'fact': 0.4
        }
        return importance_map.get(event_type, 0.5)

    def _estimate_valence(self, content: str) -> float:
        """Estimate emotional valence (-1 negative to +1 positive)"""
        positive_words = ['happy', 'joy', 'love', 'excited', 'great', 'amazing',
                         'good', 'wonderful', 'fantastic', 'beautiful', 'best']
        negative_words = ['sad', 'angry', 'fear', 'worried', 'hate', 'terrible',
                         'bad', 'awful', 'horrible', 'scared', 'anxious', 'depressed']

        content_lower = content.lower()
        pos_count = sum(1 for w in positive_words if w in content_lower)
        neg_count = sum(1 for w in negative_words if w in content_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.0
        return (pos_count - neg_count) / total

    def _infer_trait_name(self, event_type: str, signal: str) -> str:
        """Infer trait category from event"""
        signal_lower = signal.lower()

        if event_type == 'emotion':
            if any(w in signal_lower for w in ['sad', 'depressed', 'grief', 'cry']):
                return 'emotional_state'
            elif any(w in signal_lower for w in ['happy', 'excited', 'joy']):
                return 'emotional_state'
        elif event_type == 'preference':
            if any(w in signal_lower for w in ['like', 'love', 'enjoy']):
                return 'interests'
            elif any(w in signal_lower for w in ['hate', 'dislike']):
                return 'aversions'
        elif event_type == 'goal':
            return 'goals'
        elif event_type == 'relationship':
            return 'relationship_state'
        return 'general'

    def _update_trait(self, event_type: str, signal: str, confidence: float):
        """Update or create trait based on new evidence"""
        trait_name = self._infer_trait_name(event_type, signal)

        if trait_name in self.traits:
            self.traits[trait_name].update(signal, confidence)
        else:
            self.traits[trait_name] = ProfileTrait(
                trait_name=trait_name,
                value=signal,
                strength=confidence * 0.3,
                last_updated=time.time(),
                evidence_count=1,
                last_signal=signal
            )

    def _evict_lowest_scoring(self):
        """Evict lowest scoring memories from short-term (score-based)"""
        if not self.short_term:
            return

        scored = [(k, v.compute_score()) for k, v in self.short_term.items()]
        scored.sort(key=lambda x: x[1])

        # Evict bottom batch
        for i in range(min(self.EVICTION_BATCH_SIZE, len(scored))):
            memory_id, score = scored[i]
            memory = self.short_term[memory_id]

            # Promote to long-term if criteria met
            if score > self.LTM_PROMOTION_THRESHOLD and memory.access_count > self.LTM_ACCESS_THRESHOLD:
                self._promote_to_long_term(memory)

            del self.short_term[memory_id]

    def _promote_to_long_term(self, memory: ShortTermMemory):
        """Promote short-term memory to long-term"""
        ltm = LongTermMemory(
            memory_id=memory.memory_id,
            content=memory.content,
            event_type=memory.memory_type,
            importance_base=memory.importance,
            retrieval_count=memory.access_count,
            last_retrieved=memory.last_accessed,
            created_at=memory.created_at,
            emotional_valence=self._estimate_valence(memory.content),
            related_traits=self._find_related_traits(memory.memory_type)
        )
        self.long_term[memory.memory_id] = ltm

    def _find_related_traits(self, memory_type: str) -> List[str]:
        """Find traits related to this memory type"""
        return [trait for trait in self.traits.keys() if trait == memory_type or 'general' in trait]

    def add_to_short_term(self, content: str, importance: float,
                         memory_type: str, tags: List[str]):
        """Add memory to short-term storage with eviction"""
        if len(self.short_term) >= self.SHORT_TERM_LIMIT:
            self._evict_lowest_scoring()

        memory = ShortTermMemory(
            memory_id=str(uuid.uuid4()),
            content=content,
            importance=importance,
            recency=1.0,
            access_count=0,
            created_at=time.time(),
            last_accessed=time.time(),
            memory_type=memory_type,
            tags=tags
        )
        self.short_term[memory.memory_id] = memory

    # =========================================================================
    # Retrieval (with access_count increment)
    # =========================================================================

    def retrieve_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories, incrementing access count"""
        results = []
        query_lower = query.lower()

        # Search short-term
        for memory in self.short_term.values():
            if any(word in memory.content.lower() for word in query_lower.split()):
                memory.access_count += 1
                memory.last_accessed = time.time()
                results.append({
                    'content': memory.content,
                    'type': memory.memory_type,
                    'importance': memory.importance,
                    'access_count': memory.access_count,
                    'source': 'short_term'
                })

        # Search long-term for frequently accessed items
        for memory in self.long_term.values():
            if memory.retrieval_count >= 3:
                if any(word in memory.content.lower() for word in query_lower.split()):
                    memory.retrieval_count += 1
                    memory.last_retrieved = time.time()
                    results.append({
                        'content': memory.content,
                        'type': memory.event_type,
                        'importance': memory.importance_base,
                        'access_count': memory.retrieval_count,
                        'source': 'long_term'
                    })

        # Sort by access_count descending
        results.sort(key=lambda x: x['access_count'], reverse=True)
        return results[:limit]

    # =========================================================================
    # Decay
    # =========================================================================

    def decay_memories(self):
        """Apply time-based decay to all memories"""
        current_time = time.time()

        # Decay short-term recency
        for memory in self.short_term.values():
            age_days = (current_time - memory.created_at) / (24 * 3600)
            memory.recency = max(0, 1.0 - (age_days / 7))

        # Decay long-term retrieval counts after 30 days
        for memory in self.long_term.values():
            days_since_retrieval = (current_time - memory.last_retrieved) / (24 * 3600)
            if days_since_retrieval > self.RETRIEVAL_DECAY_DAYS:
                memory.retrieval_count = max(0, memory.retrieval_count - 1)

    # =========================================================================
    # Event Extraction
    # =========================================================================

    def load_conversations(self, days: int = 7) -> List[Dict]:
        """Load recent conversations from JSONL"""
        conversations = []
        cutoff = datetime.now().timestamp() - (days * 86400)

        if not os.path.exists(self.conversation_file):
            return []

        try:
            with open(self.conversation_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            ts = entry.get('timestamp', '')
                            if ts:
                                try:
                                    entry_time = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                                    if entry_time >= cutoff:
                                        conversations.append(entry)
                                except ValueError:
                                    continue
                        except json.JSONDecodeError:
                            continue
        except IOError:
            pass

        return conversations

    def extract_events(self, conversations: List[Dict]) -> List[ProfileEvent]:
        """Extract events/signals from conversation messages"""
        events = []

        emotion_keywords = ['happy', 'sad', 'angry', 'excited', 'worried', 'nervous',
                          'scared', 'love', 'hate', 'miss', 'angry', 'frustrated',
                          'anxious', 'depressed', 'grief']
        event_keywords = ['job', 'work', 'family', 'friend', 'health', 'money',
                        'love', 'school', 'home', 'pet', 'relationship', 'career']
        preference_keywords = ['like', 'love', 'hate', 'prefer', 'want', 'need', 'wish']

        for conv in conversations:
            content = conv.get('content', '')
            content_lower = content.lower()
            role = conv.get('role', '')
            timestamp = conv.get('timestamp', '')

            if role != 'user':
                continue

            try:
                ts_float = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
            except (ValueError, AttributeError):
                ts_float = time.time()

            msg_id = f"{timestamp}_{content[:20]}"

            # Extract emotions
            for emotion in emotion_keywords:
                if emotion in content_lower:
                    events.append(ProfileEvent(
                        event_id=str(uuid.uuid4()),
                        user_id='user',
                        timestamp=ts_float,
                        event_type='emotion',
                        signal=f'expressed_{emotion}',
                        raw_text=content[:200],
                        confidence=0.85,
                        source_message_id=msg_id
                    ))

            # Extract events
            for keyword in event_keywords:
                if keyword in content_lower:
                    events.append(ProfileEvent(
                        event_id=str(uuid.uuid4()),
                        user_id='user',
                        timestamp=ts_float,
                        event_type='event',
                        signal=f'talked_about_{keyword}',
                        raw_text=content[:200],
                        confidence=0.75,
                        source_message_id=msg_id
                    ))

            # Extract preferences
            for pref in preference_keywords:
                if pref in content_lower:
                    events.append(ProfileEvent(
                        event_id=str(uuid.uuid4()),
                        user_id='user',
                        timestamp=ts_float,
                        event_type='preference',
                        signal=f'expressed_{pref}',
                        raw_text=content[:200],
                        confidence=0.70,
                        source_message_id=msg_id
                    ))

        return events

    # =========================================================================
    # Main Pipeline
    # =========================================================================

    def run_daily_update(self):
        """Run the complete daily memory update pipeline"""
        # Load recent conversations
        conversations = self.load_conversations(days=7)

        # Extract events
        events = self.extract_events(conversations)

        # Process each event
        for event in events:
            # Add to pending events for append-only storage
            self.pending_events.append(event)

            # Add to short-term memory
            self.add_to_short_term(
                content=event.signal,
                importance=self._estimate_importance(event.event_type),
                memory_type=event.event_type,
                tags=[event.event_type]
            )

            # Update traits
            self._update_trait(event.event_type, event.signal, event.confidence)

        # Check for promotions (events repeated 2+ times become long-term)
        self._process_repeated_events(events)

        # Apply decay
        self.decay_memories()

        # Persist all
        self.persist_all()

        return {
            'conversations_processed': len(conversations),
            'events_extracted': len(events),
            'short_term_count': len(self.short_term),
            'long_term_count': len(self.long_term),
            'trait_count': len(self.traits),
            'timestamp': datetime.now().isoformat()
        }

    def _process_repeated_events(self, events: List[ProfileEvent]):
        """Promote frequently repeated events to long-term memory"""
        event_counts = defaultdict(int)
        event_data = {}

        for event in events:
            key = f"{event.event_type}:{event.signal}"
            event_counts[key] += 1
            if key not in event_data:
                event_data[key] = event

        # Promote events that appeared 2+ times
        for key, count in event_counts.items():
            if count >= 2:
                event_type, content = key.split(':', 1)
                event = event_data[key]

                # Check if already in long-term
                exists = any(m.content == content for m in self.long_term.values())
                if not exists:
                    ltm = LongTermMemory(
                        memory_id=str(uuid.uuid4()),
                        content=content,
                        event_type=event_type,
                        importance_base=self._estimate_importance(event_type),
                        retrieval_count=count,
                        last_retrieved=time.time(),
                        created_at=event.timestamp,
                        emotional_valence=self._estimate_valence(content),
                        related_traits=[self._infer_trait_name(event_type, content)]
                    )
                    self.long_term[ltm.memory_id] = ltm

    def get_recent_memories(self, limit: int = 5) -> List[Dict]:
        """Get recent memories from short-term storage"""
        memories = []
        sorted_memories = sorted(
            self.short_term.values(),
            key=lambda x: x.last_accessed,
            reverse=True
        )

        for memory in sorted_memories[:limit]:
            memories.append({
                'content': memory.content,
                'type': memory.memory_type,
                'created_at': datetime.fromtimestamp(memory.created_at).isoformat(),
                'importance': memory.importance
            })

        return memories

    def generate_summary(self) -> str:
        """Generate LLM-ready natural language summary"""
        trait_lines = []
        for trait in self.traits.values():
            stability = "stable" if trait.strength > 0.7 else "developing" if trait.strength > 0.4 else "emerging"
            trait_lines.append(
                f"- {trait.trait_name}: {trait.value} ({stability}, strength={trait.strength:.2f})"
            )

        short_term_highlight = []
        sorted_memories = sorted(
            self.short_term.values(),
            key=lambda x: x.importance,
            reverse=True
        )[:5]
        for memory in sorted_memories:
            short_term_highlight.append(f"  [{memory.memory_type}] {memory.content[:50]}")

        return f"""Profile Summary:

TRAITS:
{chr(10).join(trait_lines) if trait_lines else "  No traits yet"}

RECENT MEMORIES (by importance):
{chr(10).join(short_term_highlight) if short_term_highlight else "  No memories yet"}

MEMORY STATS:
  Short-term: {len(self.short_term)}/{self.SHORT_TERM_LIMIT}
  Long-term: {len(self.long_term)}
  Traits: {len(self.traits)}"""


if __name__ == "__main__":
    # Test the pipeline
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Initialize
    pipeline = MemoryPipeline()

    # Run update
    result = pipeline.run_daily_update()
    print("Daily update complete:")
    print(f"  Conversations: {result['conversations_processed']}")
    print(f"  Events: {result['events_extracted']}")
    print(f"  Short-term: {result['short_term_count']}")
    print(f"  Long-term: {result['long_term_count']}")
    print(f"  Traits: {result['trait_count']}")

    # Show summary
    print("\n" + pipeline.generate_summary())
