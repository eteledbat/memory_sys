"""
Sweekar - AI Companion Pet Product
Main entry point for the Streamlit UI
"""

import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat.chat_engine import ChatEngine
from memory.memory_pipeline import MemoryPipeline
from config.pet_config import PetConfig

# Page configuration
st.set_page_config(
    page_title="Sweekar - Your AI Pocket Pet",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #fef9f3 0%, #fdf2e9 50%, #fce8d5 100%);
    }

    /* Chat container styling */
    .chat-container {
        background: white;
        border-radius: 24px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 179, 71, 0.2);
    }

    /* Pet avatar circle */
    .pet-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ffb347 0%, #ff6b6b 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 36px;
        box-shadow: 0 4px 16px rgba(255, 107, 107, 0.3);
        margin: 0 auto;
    }

    /* Status cards */
    .status-card {
        background: white;
        border-radius: 16px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(255, 179, 71, 0.15);
    }

    /* User message bubble */
    .user-message {
        background: linear-gradient(135deg, #ffb347 0%, #ff8c00 100%);
        color: white;
        border-radius: 20px 20px 4px 20px;
        padding: 12px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 8px rgba(255, 140, 0, 0.3);
    }

    /* Pet message bubble */
    .pet-message {
        background: white;
        color: #333;
        border-radius: 20px 20px 20px 4px;
        padding: 12px 18px;
        margin: 8px 0;
        max-width: 80%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 179, 71, 0.2);
    }

    /* Pet name header */
    .pet-header {
        text-align: center;
        padding: 16px;
        background: linear-gradient(135deg, #ffb347 0%, #ff6b6b 100%);
        border-radius: 20px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(255, 107, 107, 0.3);
    }

    /* Setup card */
    .setup-card {
        background: white;
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        max-width: 500px;
        margin: 0 auto;
        text-align: center;
    }

    /* Input area styling */
    .stTextInput > div > div > input {
        border-radius: 24px;
        border: 2px solid rgba(255, 179, 71, 0.3);
        padding: 14px 20px;
        font-size: 16px;
    }

    .stTextInput > div > div > input:focus {
        border-color: #ffb347;
        box-shadow: 0 0 0 3px rgba(255, 179, 71, 0.2);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 24px;
        background: linear-gradient(135deg, #ffb347 0%, #ff6b6b 100%);
        color: white;
        border: none;
        padding: 12px 32px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: 0 4px 16px rgba(255, 107, 107, 0.3);
    }

    .stButton > button:hover {
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
        transform: translateY(-2px);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #ffb347, #ff6b6b);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: #fffdf9;
    }

    /* Message timestamp */
    .timestamp {
        font-size: 11px;
        color: #888;
        margin-top: 4px;
    }

    /* Stats text - darker color for visibility */
    .stats-text {
        color: #333;
        font-size: 14px;
        font-weight: 500;
    }

    /* Memory preview text */
    .memory-text {
        color: #444;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'pet_config' not in st.session_state:
        st.session_state.pet_config = PetConfig()

    if 'chat_engine' not in st.session_state:
        st.session_state.chat_engine = ChatEngine(
            st.session_state.pet_config
        )

    if 'setup_complete' not in st.session_state:
        st.session_state.setup_complete = (
            st.session_state.pet_config.config.get('pet_name') is not None
        )

    if 'messages' not in st.session_state:
        st.session_state.messages = []


def render_setup_page():
    """Render the initial pet setup page"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="setup-card">
            <div class="pet-avatar" style="margin-bottom: 24px;">
                🐾
            </div>
            <h1 style="color: #ff6b6b; margin-bottom: 8px;">Welcome to Sweekar!</h1>
            <p style="color: #666; margin-bottom: 32px;">
                Your AI Pocket Pet companion<br>
                Let's give your pet a name!
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("pet_setup_form"):
            pet_name = st.text_input(
                "Pet Name",
                placeholder="e.g., Mochi, Luna, Biscuit...",
                max_chars=20
            )
            submitted = st.form_submit_button("Create My Pet 🐾")

            if submitted and pet_name.strip():
                st.session_state.pet_config.set_pet_name(pet_name.strip())
                st.session_state.pet_config.save()
                st.session_state.setup_complete = True
                st.rerun()


def render_pet_avatar(name: str, size: str = "large"):
    """Render pet avatar with name"""
    size_map = {
        "small": (50, 50, 24),
        "medium": (80, 80, 36),
        "large": (120, 120, 56)
    }
    w, h, font = size_map.get(size, size_map["medium"])

    emoji_map = {
        "mochi": "🐱", "luna": "🐱", "biscuit": "🐶",
        "pudding": "🐱", "whiskers": "🐱", "nugget": "🐶",
        "max": "🐕", "cookie": "🍪"
    }

    # Get emoji based on name or default
    pet_emoji = "🐾"
    name_lower = name.lower()
    for key, emo in emoji_map.items():
        if key in name_lower:
            pet_emoji = emo
            break

    st.markdown(f"""
    <div style="text-align: center;">
        <div class="pet-avatar" style="width: {w}px; height: {h}px; font-size: {font}px; margin: 0 auto;">
            {pet_emoji}
        </div>
        <h3 style="color: #ff6b6b; margin-top: 12px;">{name}</h3>
    </div>
    """, unsafe_allow_html=True)


def render_pet_status():
    """Render pet status panel"""
    pet_state = st.session_state.pet_config.get_pet_state()

    col1, col2, col3 = st.columns(3)

    with col1:
        mood = pet_state.get('mood', 80)
        st.markdown(f"""
        <div class="status-card">
            <div style="font-size: 24px;">😊</div>
            <div style="font-size: 12px; color: #666; margin-top: 4px;">MOOD</div>
            <div style="font-size: 20px; font-weight: 600; color: #ff6b6b;">{mood}%</div>
            <div style="margin-top: 8px;">
                <div style="background: #f0f0f0; border-radius: 4px; height: 6px;">
                    <div style="background: linear-gradient(90deg, #ffb347, #ff6b6b); height: 6px; border-radius: 4px; width: {mood}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        hunger = pet_state.get('hunger', 70)
        st.markdown(f"""
        <div class="status-card">
            <div style="font-size: 24px;">🍖</div>
            <div style="font-size: 12px; color: #666; margin-top: 4px;">HUNGER</div>
            <div style="font-size: 20px; font-weight: 600; color: #ff6b6b;">{hunger}%</div>
            <div style="margin-top: 8px;">
                <div style="background: #f0f0f0; border-radius: 4px; height: 6px;">
                    <div style="background: linear-gradient(90deg, #ffb347, #ff6b6b); height: 6px; border-radius: 4px; width: {hunger}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        health = pet_state.get('health', 90)
        st.markdown(f"""
        <div class="status-card">
            <div style="font-size: 24px;">💚</div>
            <div style="font-size: 12px; color: #666; margin-top: 4px;">HEALTH</div>
            <div style="font-size: 20px; font-weight: 600; color: #4CAF50;">{health}%</div>
            <div style="margin-top: 8px;">
                <div style="background: #f0f0f0; border-radius: 4px; height: 6px;">
                    <div style="background: linear-gradient(90deg, #4CAF50, #8BC34A); height: 6px; border-radius: 4px; width: {health}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_chat_message(role: str, content: str, timestamp: str = ""):
    """Render a single chat message with styling"""
    if role == "user":
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 12px 0;">
            <div>
                <div class="user-message">{content}</div>
                <div class="timestamp" style="text-align: right;">{timestamp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin: 12px 0;">
            <div>
                <div class="pet-message">{content}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_chat_page():
    """Render the main chat interface"""
    pet_name = st.session_state.pet_config.config.get('pet_name', 'Pet')
    pet_emoji = "🐾"
    is_using_api = st.session_state.chat_engine.is_using_api()

    # Header with pet name
    st.markdown(f"""
    <div class="pet-header">
        <div style="display: flex; align-items: center; justify-content: center; gap: 16px;">
            <div style="font-size: 48px;">{pet_emoji}</div>
            <div>
                <h2 style="margin: 0;">{pet_name}</h2>
                <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Your AI Companion</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API status indicator
    if is_using_api:
        st.success("🤖 Connected to MiniMax AI")
    else:
        st.info("💡 Set MINIMAX_API_KEY env variable to enable AI responses")

    # Main content area using columns
    col_left, col_main, col_right = st.columns([1, 3, 1])

    # Left column - Pet Avatar
    with col_left:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        render_pet_avatar(pet_name, "medium")
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        render_pet_status()

        # Memory update button
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Update Memory", use_container_width=True):
            with st.spinner("Updating memory..."):
                pipeline = MemoryPipeline()
                result = pipeline.run_daily_update()
                st.success(f"Updated! Events: {result['events_extracted']}, Short-term: {result['short_term_count']}")

    # Main column - Chat
    with col_main:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

        # Display messages
        chat_container = st.container()
        with chat_container:
            # Load existing messages
            messages = st.session_state.chat_engine.get_conversation_history()
            for msg in messages[-50:]:  # Last 50 messages
                render_chat_message(
                    msg.get('role', 'assistant'),
                    msg.get('content', ''),
                    msg.get('timestamp', '')[:16]
                )

        # Chat input
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            col_input, col_btn = st.columns([5, 1])
            with col_input:
                user_input = st.text_input(
                    "Type a message...",
                    label_visibility="collapsed",
                    placeholder="Say something to your pet..."
                )
            with col_btn:
                submitted = st.form_submit_button("Send")
                if submitted and user_input.strip():
                    # Get AI response
                    response = st.session_state.chat_engine.process_message(user_input.strip())
                    # Rerun to show new messages
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # Right column - Info panel
    with col_right:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Quick stats - darker colors for readability
        stats = st.session_state.chat_engine.get_stats()
        st.markdown(f"""
        <div class="status-card">
            <h4 style="color: #ff6b6b; margin-bottom: 12px;">📊 Stats</h4>
            <div style="text-align: left;">
                <div style="margin: 8px 0;" class="stats-text">💬 Messages: <strong>{stats.get('message_count', 0)}</strong></div>
                <div style="margin: 8px 0;" class="stats-text">📅 Days active: <strong>{stats.get('days_active', 1)}</strong></div>
                <div style="margin: 8px 0;" class="stats-text">🧠 Memory entries: <strong>{stats.get('memory_entries', 0)}</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Memory preview
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="status-card">
            <h4 style="color: #ff6b6b; margin-bottom: 12px;">🧠 Recent Memory</h4>
        """, unsafe_allow_html=True)

        pipeline = MemoryPipeline()
        recent = pipeline.get_recent_memories(limit=3)

        if not recent:
            st.markdown("""
            <div style="font-size: 12px; color: #888; padding: 8px; text-align: center;">
                No memories yet.<br>Click "Update Memory" or chat more to generate memories.
            </div>
            """, unsafe_allow_html=True)
        else:
            for mem in recent:
                st.markdown(f"""
                <div style="font-size: 12px; padding: 8px; background: #f9f9f9; border-radius: 8px; margin: 8px 0;">
                    <span class="memory-text">[{mem.get('type', '')}]</span><br>
                    <span style="color: #333;">{mem.get('content', '')[:80]}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main application entry point"""
    init_session_state()

    if not st.session_state.setup_complete:
        render_setup_page()
    else:
        render_chat_page()


if __name__ == "__main__":
    main()
