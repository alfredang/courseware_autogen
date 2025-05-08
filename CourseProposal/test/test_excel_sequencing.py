import json
import os
from CourseProposal.utils.excel_conversion_pipeline import map_new_key_names_excel, write_json_file
import streamlit as st
st.session_state = {}
st.session_state['cp_type'] = "New CP"

def test_excel_conversion():
    # Define paths
    generated_mapping_path = "CourseProposal/json_output/generated_mapping.json"
    output_json_file = "CourseProposal/json_output/generated_mapping.json"
    excel_data_path = "CourseProposal/json_output/excel_data.json"
    ensemble_output_path = "CourseProposal/json_output/ensemble_output.json"
    
    # Load the necessary files
    with open(generated_mapping_path, 'r') as f:
        generated_mapping = json.load(f)
    
    with open(ensemble_output_path, 'r') as f:
        ensemble_output = json.load(f)
    
    # Print the current sequencing data
    print("Current sequencing rationale:")
    print(generated_mapping.get("#Sequencing_rationale", "Not found"))
    print("\n")
    
    # Run the conversion function
    map_new_key_names_excel(
        generated_mapping_path, 
        generated_mapping, 
        output_json_file, 
        excel_data_path, 
        ensemble_output
    )
    
    # Read the updated file
    with open(output_json_file, 'r') as f:
        updated_mapping = json.load(f)
    
    # Check if the sequencing rationale was properly updated
    print("Updated sequencing rationale:")
    print(updated_mapping.get("#Sequencing_rationale", "Not found"))
    
    print("\nVerification complete!")

if __name__ == "__main__":
    test_excel_conversion() 