import os
import json
import asyncio
from typing import Dict, Any
from redisvl.schema import IndexSchema
from redisvl.types import FieldType, DistanceMetric

# Define the custom schema directly (without importing from retrieval_workflow)
def define_custom_schema():
    """Define the Redis index schema."""
    return IndexSchema(
        "rag_assessment_idx",
        prefix="doc:",
        fields=[
            {"name": "text", "type": FieldType.TEXT},
            {"name": "embedding", "type": FieldType.VECTOR, "attrs": {
                "dims": 384,  # For bge-small-en
                "distance_metric": DistanceMetric.COSINE,
                "algorithm": "HNSW"
            }},
            {"name": "file_path", "type": FieldType.TEXT},
            {"name": "file_name", "type": FieldType.TEXT},
            {"name": "file_type", "type": FieldType.TEXT},
            {"name": "file_size", "type": FieldType.NUMERIC},
            {"name": "creation_date", "type": FieldType.TEXT},
            {"name": "last_modified_date", "type": FieldType.TEXT}
        ]
    )

# Create a simplified version of the assessment creation function
async def create_tsc_assessments(input_tsc):
    """Streamlit-compatible version of the assessment creation function."""
    import streamlit as st
    from config_loader import load_shared_resources
    from llama_index.vector_stores.redis import RedisVectorStore
    from llama_index.core import VectorStoreIndex
    from utils.document_parser import parse_document
    from agents.tsc_extractor import create_tsc_agent, tsc_team_task
    from utils.helpers import extract_agent_json
    from autogen_agentchat.ui import Console
    
    try:
        # Load resources
        config, embed_model = load_shared_resources()
        
        # Create output directories
        os.makedirs("output_json", exist_ok=True)
        os.makedirs("output_documents", exist_ok=True)
        
        # Process input TSC
        model_choice = st.session_state.get('selected_model', "GPT-4o Mini (Default)")
        st.info(f"Processing document with {model_choice}...")
        parse_document(input_tsc, "output_json/output_TSC.json")
        
        with open("output_json/output_TSC.json", 'r', encoding='utf-8') as file:
            tsc_data = json.load(file)
            
        # Create TSC agent
        st.info("Creating TSC agent...")
        tsc_agent = create_tsc_agent(tsc_data=tsc_data, model_choice=model_choice)
        with st.spinner("Running TSC agent..."):
            stream = tsc_agent.run_stream(task=tsc_team_task(tsc_data))
            await Console(stream)
            
        # Save agent state
        state = await tsc_agent.save_state()
        with open("output_json/tsc_agent_state.json", "w") as f:
            json.dump(state, f)
            
        # Extract JSON
        tsc_data = extract_agent_json(file_path="output_json/tsc_agent_state.json", agent_name="tsc_prepper_agent")
        with open("output_json/parsed_TSC.json", "w", encoding="utf-8") as out:
            json.dump(tsc_data, out, indent=2)
            
        st.success("TSC extraction complete!")
        
        # Import these here to avoid circular imports
        from agents.content_team import create_content
        from utils.jinja_docu_replace import create_documents
        
        # Create content
        st.info("Generating assessment content...")
        await create_content()
        
        # Create documents
        st.info("Creating final documents...")
        create_documents()
        
        st.success("Assessment generation complete!")
        return {"status": "success"}
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        st.error(f"Error during document generation: {str(e)}")
        print(f"Error details: {error_details}")
        return {"status": "error", "message": str(e), "details": error_details}