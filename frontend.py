import streamlit as st
import os
import json
from app.chatbot.agent import ChatbotAgent
from app.models.schemas import ChatRequest, Message
from app.utils.config import Config

# Page Configuration
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-title {
        font-size: 2.5rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .recommendation-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .test-type-badge {
        background-color: #3B82F6;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.markdown("<div class='main-title'>📋 SHL Assessment Recommender</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Find the perfect SHL individual assessments for your hiring roles through natural conversation.</div>", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Check for API Key in env
    api_key_exists = bool(os.getenv("GEMINI_API_KEY") or Config.GEMINI_API_KEY)
    
    if not api_key_exists:
        st.warning("⚠️ GEMINI_API_KEY is not set in your environment.")
        user_key = st.text_input("Enter your Gemini API Key:", type="password")
        if user_key:
            os.environ["GEMINI_API_KEY"] = user_key
            st.success("API Key applied for this session!")
            st.rerun()
    else:
        st.success("✅ GEMINI_API_KEY is configured.")
        
    st.markdown("---")
    
    st.subheader("📊 Catalog Statistics")
    cleaned_catalog_path = os.path.join("app", "resources", "cleaned_catalog.json")
    if os.path.exists(cleaned_catalog_path):
        with open(cleaned_catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        st.metric("Individual Assessments", len(catalog))
        
        # Count by test type
        type_counts = {}
        for item in catalog:
            t_type = item.get("test_type", "K")
            type_counts[t_type] = type_counts.get(t_type, 0) + 1
            
        st.markdown("**Assessment Types:**")
        for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            st.markdown(f"- `{t}`: {count} tests")
    else:
        st.error("Cleaned catalog not found. Please run `python app/scraper/parse_catalog.py` first.")

    st.markdown("---")
    
    # Sample Role Templates
    st.subheader("💡 Try Quick Prompts")
    quick_roles = [
        "Hiring a senior Java developer",
        "We need a screening test for admin assistants",
        "Hiring plant operators for a chemical facility (safety focus)",
        "Screening 500 entry-level contact centre agents"
    ]
    for role in quick_roles:
        if st.button(role, use_container_width=True):
            # Reset chat and pre-populate
            st.session_state.messages = [{"role": "user", "content": role}]
            st.session_state.agent_instance = ChatbotAgent()
            st.rerun()

    st.markdown("---")
    if st.button("🔄 Reset Conversation", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent_instance = None
        st.rerun()

# ----------------- MAIN UI -----------------

# Initialize session state for messages and agent instance
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "agent_instance" not in st.session_state or st.session_state.agent_instance is None:
    try:
        st.session_state.agent_instance = ChatbotAgent()
    except Exception as e:
        st.session_state.agent_instance = None

# If agent cannot be initialized due to missing API Key
if st.session_state.agent_instance is None and not os.getenv("GEMINI_API_KEY"):
    st.error("Please enter a valid **Gemini API Key** in the sidebar to start the chat.")
    st.stop()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if user_input := st.chat_input("Ask about SHL assessments... (e.g. 'I am hiring a Java developer')"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate bot response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing catalog and thinking..."):
            try:
                # Build request history
                history = [Message(role=m["role"], content=m["content"]) for m in st.session_state.messages]
                request = ChatRequest(messages=history)
                
                # Get response
                response = st.session_state.agent_instance.generate_response(request)
                
                # Show reply text
                st.markdown(response.reply)
                st.session_state.messages.append({"role": "assistant", "content": response.reply})
                
                # Show structured recommendations if present
                if response.recommendations:
                    st.markdown("---")
                    st.subheader("📋 Active Recommendation Shortlist")
                    cols = st.columns(min(len(response.recommendations), 3))
                    
                    for idx, rec in enumerate(response.recommendations):
                        col_idx = idx % 3
                        with cols[col_idx]:
                            st.markdown(f"""
                            <div class="recommendation-card">
                                <strong>#{idx+1} {rec.name}</strong><br>
                                <span class="test-type-badge">Type: {rec.test_type}</span><br><br>
                                <a href="{rec.url}" target="_blank">🔗 Official Catalog URL</a>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    if response.end_of_conversation:
                        st.balloons()
                        st.success("🔒 Shortlist locked in. Conversation completed!")
            except Exception as e:
                st.error(f"Error generating response: {e}")
