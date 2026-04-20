"""
Pet configuration management
Handles pet name and basic state persistence
"""

import json
import os
from datetime import datetime


class PetConfig:
    """Manages pet configuration and state"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(base_dir, 'config')

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'pet_config.json')
        self.pet_state_file = os.path.join(config_dir, 'pet_state.json')

        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)

        # Load or initialize config
        self.config = self._load_config()
        self.pet_state = self._load_pet_state()

    def _load_config(self) -> dict:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_config()

    def _load_pet_state(self) -> dict:
        """Load pet state from JSON file"""
        if os.path.exists(self.pet_state_file):
            try:
                with open(self.pet_state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_pet_state()

    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            'pet_name': None,
            'created_at': datetime.now().isoformat(),
            'first_run': True
        }

    def _default_pet_state(self) -> dict:
        """Default pet state"""
        return {
            'mood': 80,
            'hunger': 70,
            'health': 90,
            'last_fed': datetime.now().isoformat(),
            'last_play': datetime.now().isoformat(),
            'total_interactions': 0
        }

    def set_pet_name(self, name: str):
        """Set the pet name"""
        self.config['pet_name'] = name
        self.config['first_run'] = False

    def get_pet_name(self) -> str:
        """Get the pet name"""
        return self.config.get('pet_name', 'Pet')

    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def save_pet_state(self):
        """Save pet state to file"""
        with open(self.pet_state_file, 'w', encoding='utf-8') as f:
            json.dump(self.pet_state, f, indent=2, ensure_ascii=False)

    def update_pet_state(self, mood: int = None, hunger: int = None, health: int = None):
        """Update pet state values"""
        if mood is not None:
            self.pet_state['mood'] = max(0, min(100, self.pet_state['mood'] + mood))
        if hunger is not None:
            self.pet_state['hunger'] = max(0, min(100, self.pet_state['hunger'] + hunger))
        if health is not None:
            self.pet_state['health'] = max(0, min(100, self.pet_state['health'] + health))

        self.pet_state['total_interactions'] += 1
        self.save_pet_state()

    def get_pet_state(self) -> dict:
        """Get current pet state"""
        return self.pet_state.copy()

    def decay_stats(self):
        """Apply time-based decay to pet stats"""
        self.pet_state['hunger'] = max(0, self.pet_state['hunger'] - 2)
        self.pet_state['mood'] = max(0, self.pet_state['mood'] - 1)
        self.save_pet_state()
