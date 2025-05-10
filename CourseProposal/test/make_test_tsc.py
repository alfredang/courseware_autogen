import json
import os
import re

def fix_ensemble_output():
    """Fix the ensemble_output.json by replacing auto-generated Details for Topic 1 with the actual subtopics"""
    # Load the files
    raw_json_path = "json_output/output_TSC_raw.json"
    ensemble_json_path = "json_output/ensemble_output.json"
    
    try:
        with open(raw_json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        with open(ensemble_json_path, 'r', encoding='utf-8') as f:
            ensemble_data = json.load(f)
    except Exception as e:
        print(f"Error loading files: {e}")
        return
        
    print("Files loaded successfully")
    
    # Debug the structure of the raw_data
    print("\nStructure of output_TSC_raw.json:")
    for key in raw_data.keys():
        print(f"Key: {key}")
        if isinstance(raw_data[key], dict):
            for subkey in raw_data[key].keys():
                print(f"  Subkey: {subkey}")
    
    # Get the original subtopics from raw data
    topic1_details = None
    tables_found = 0
    
    for section_name, section_content in raw_data.items():
        if isinstance(section_content, dict) and "content" in section_content:
            print(f"\nSearching in section: {section_name}")
            
            for item in section_content["content"]:
                if isinstance(item, dict) and "table" in item:
                    tables_found += 1
                    print(f"Found table #{tables_found}")
                    table = item["table"]
                    
                    # Debug the table structure
                    print(f"Table has {len(table)} rows")
                    if len(table) > 0:
                        print(f"First row has {len(table[0])} cells")
                    
                    for row_idx, row in enumerate(table):
                        if row_idx == 0:  # Skip header row
                            continue
                            
                        # Check each cell that might be a topic
                        for cell_idx, cell in enumerate(row):
                            if isinstance(cell, dict) and "Topic" in cell:
                                print(f"Found topic in row {row_idx+1}, cell {cell_idx+1}: {cell['Topic']}")
                                
                                if "T1: Fundamentals of storytelling" in cell["Topic"]:
                                    topic1_details = cell.get("Details", [])
                                    print(f"Found Topic 1 with details: {topic1_details}")
    
    if not topic1_details:
        print("Error: Could not find Topic 1's details in raw data")
        return
    
    # Update the ensemble output
    updated = False
    
    if "LU1" in ensemble_data["Assessment Methods"]["Course Outline"]["Learning Units"]:
        for topic_desc in ensemble_data["Assessment Methods"]["Course Outline"]["Learning Units"]["LU1"]["Description"]:
            if "Topic 1: Fundamentals of storytelling" in topic_desc["Topic"]:
                # Replace the auto-generated Details with the original subtopics
                original_details = topic_desc["Details"]
                topic_desc["Details"] = topic1_details
                updated = True
                
                print("\nUpdated Details field:")
                print(f"  Original: {original_details}")
                print(f"  New: {topic1_details}")
                break
    
    if not updated:
        print("Error: Could not find Topic 1 in ensemble output to update")
        return
    
    # Save the fixed ensemble output
    fixed_path = "json_output/fixed_ensemble_output.json"
    try:
        with open(fixed_path, 'w', encoding='utf-8') as f:
            json.dump(ensemble_data, f, indent=4)
        print(f"\nFixed ensemble output saved to {fixed_path}")
        
        # Also overwrite the original file
        with open(ensemble_json_path, 'w', encoding='utf-8') as f:
            json.dump(ensemble_data, f, indent=4)
        print(f"Original file {ensemble_json_path} also updated")
    except Exception as e:
        print(f"Error saving files: {e}")

if __name__ == "__main__":
    fix_ensemble_output() 