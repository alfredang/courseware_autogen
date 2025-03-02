import streamlit as st
from config_loader import load_shared_resources
from redis_querying import initialize_chat_pipeline, run_chat_query
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer

st.set_page_config(
    page_title="Chat with Documents",
    page_icon="💬",
    layout="wide",
)

# Load configuration
config, embed_model = load_shared_resources()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)

if "pipeline" not in st.session_state:
    st.session_state.pipeline = initialize_chat_pipeline(embed_model, config)

st.title("💬 Chat with Your Documents")
st.markdown("""
Ask questions about your indexed documents and get answers based on their content.
The system will retrieve relevant information and generate responses using Gemini LLM.
""")

# Sidebar customization options
st.sidebar.header("Chat Options")
retrieval_mode = st.sidebar.radio(
    "Retrieval Mode:",
    ["Hybrid (Query + Rewrite)", "Direct Query", "Query Rewrite"],
    index=0,
    help="Choose how documents are retrieved"
)

top_k = st.sidebar.slider(
    "Number of chunks to retrieve", 
    min_value=1, 
    max_value=15, 
    value=6,
    help="Higher values retrieve more context but may be slower"
)

st.sidebar.markdown("---")

# Clear chat button
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.session_state.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)
    st.rerun()

# Chat interface
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Get user input
prompt = st.chat_input("Ask something about your documents...")

# Handle user input
if prompt:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response with a spinner
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            # Process query with the query pipeline
            response = run_chat_query(
                prompt, 
                st.session_state.pipeline,
                st.session_state.memory,
                retrieval_mode,
                top_k
            )
            
            response_content = response.message.content
            
            # Update chat history
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            
            # Display response
            message_placeholder.markdown(response_content)

# Initial empty state
if not st.session_state.messages:
    st.info("👋 Send a message to start chatting about your documents!")