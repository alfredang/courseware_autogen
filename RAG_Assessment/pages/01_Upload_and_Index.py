import streamlit as st
import os
import time
import tempfile
from config_loader import load_shared_resources
from redis_indexing import run_indexing_with_files, check_index_status

st.set_page_config(
    page_title="Upload & Index Documents",
    page_icon="📤",
    layout="wide",
)

# Load configuration
config, embed_model = load_shared_resources()

st.title("📤 Upload & Index Documents")
st.markdown("""
Upload your PDF documents here to be processed and indexed. 
The system will parse the documents and make them available for querying.
""")

# Document upload section
st.header("Document Upload")
uploaded_files = st.file_uploader(
    "Upload your PDF documents", 
    type=["pdf"], 
    accept_multiple_files=True
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Indexing Options")
    chunk_size = st.slider("Chunk Size (sentences per node)", 1, 10, 3, help="Number of sentences per text chunk")
    chunk_overlap = st.slider("Chunk Overlap", 0, 5, 1, help="Number of overlapping sentences between chunks")

with col2:
    st.subheader("Processing")
    index_button = st.button("Process and Index Documents", type="primary", disabled=len(uploaded_files) == 0)
    st.write(f"Files to be processed: {len(uploaded_files)}")
    
    # Display file names
    if uploaded_files:
        file_list = ", ".join([file.name for file in uploaded_files])
        st.write(f"Selected files: {file_list}")

# Index status display
st.header("Indexing Status")
status_placeholder = st.empty()

# Index document handling
if index_button and uploaded_files:
    # Create a temporary directory for uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded files to temp directory
        file_paths = []
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            file_paths.append(file_path)
        
        # Start indexing process
        status_placeholder.info("Indexing in progress... This may take a few minutes.")
        
        # Progress bar
        progress_bar = st.progress(0)
        
        # Process files and index them
        try:
            node_count = run_indexing_with_files(file_paths, embed_model, chunk_size, chunk_overlap)
            
            # Update progress
            for i in range(100):
                time.sleep(0.05)  # Simulate processing time
                progress_bar.progress(i + 1)
            
            # Show completion status
            status_placeholder.success(f"✅ Indexing complete! {node_count} nodes indexed.")
            st.balloons()
        
        except Exception as e:
            status_placeholder.error(f"❌ Indexing failed: {str(e)}")

# Display index information
if not index_button:
    index_status = check_index_status()
    if index_status["exists"]:
        status_placeholder.success(f"✅ Index exists with {index_status['node_count']} nodes")
        
        # Display index stats
        st.subheader("Index Statistics")
        st.json(index_status["stats"])
    else:
        status_placeholder.info("No index found. Please upload and process documents.")