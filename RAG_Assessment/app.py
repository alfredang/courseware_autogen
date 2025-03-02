import streamlit as st
import os
from config_loader import load_shared_resources

# Create necessary directories
os.makedirs("data/uploads", exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="Document Q&A System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load configuration
config, embed_model = load_shared_resources()

# Main page
st.title("📚 Document Q&A System")
st.markdown("""
Welcome to the Document Q&A System! This application allows you to:

1. **Upload and Index Documents**: Upload your PDF documents to be processed and indexed.
2. **Chat with Documents**: Ask questions about your documents and get answers.

Use the navigation sidebar to switch between these functions.
""")

# Display system status
st.sidebar.title("System Status")

# Check Redis connection
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    ping = r.ping()
    if ping:
        st.sidebar.success("✅ Redis server is connected")
    else:
        st.sidebar.error("❌ Redis server connection failed")
except Exception as e:
    st.sidebar.error(f"❌ Redis error: {str(e)}")

# Check embedding model
if embed_model:
    st.sidebar.success(f"✅ Embedding model loaded: {type(embed_model).__name__}")
else:
    st.sidebar.error("❌ Embedding model not loaded")

# Check LLM configuration
if config.get("gemini_api_key") or config.get("GEMINI_API_KEY") or config.get("GEMINI_API"):
    st.sidebar.success("✅ Gemini API key configured")
else:
    st.sidebar.error("❌ Gemini API key not configured")

st.sidebar.markdown("---")
st.sidebar.markdown("### Navigation")
st.sidebar.markdown("Use the pages in the sidebar to navigate between features.")