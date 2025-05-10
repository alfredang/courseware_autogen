import json
import os
import sys

def examine_subtopics():
    """Directly examine the subtopics in the TSC_raw.json and show how they should be processed"""
    # Load the raw TSC data
    raw_json_path = "json_output/output_TSC_raw.json"
    with open(raw_json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"Loaded {raw_json_path} successfully")
    
    # Load the ensemble output for comparison
    ensemble_json_path = "json_output/ensemble_output.json"
    with open(ensemble_json_path, 'r', encoding='utf-8') as f:
        ensemble_data = json.load(f)
    
    print(f"Loaded {ensemble_json_path} for comparison")
    
    # Find the table in the TSC data containing the topics
    table_found = False
    table = None
    
    for item in raw_data["TSC and Topics"]["content"]:
        if isinstance(item, dict) and "table" in item:
            table = item["table"]
            table_found = True
            break
    
    if not table_found:
        print("Error: Could not find table in TSC data")
        return
    
    # Find the row with T1: Fundamentals of storytelling
    topic1_found = False
    topic1_row = None
    
    for row in table:
        if len(row) >= 4 and isinstance(row[3], dict) and "Topic" in row[3]:
            if "T1: Fundamentals of storytelling" in row[3]["Topic"]:
                topic1_row = row
                topic1_found = True
                break
    
    if not topic1_found:
        print("Error: Could not find Topic 1 in table")
        return
    
    # Extract Topic and Details from T1
    topic1_cell = topic1_row[3]
    print("\nRaw TSC Topic 1 Data:")
    print(f"Topic: {topic1_cell['Topic']}")
    print(f"Details: {topic1_cell.get('Details', [])}")
    
    # Check how this appears in the ensemble output
    lu1_found = False
    topic1_in_ensemble = None
    
    if "LU1" in ensemble_data["Assessment Methods"]["Course Outline"]["Learning Units"]:
        for topic_desc in ensemble_data["Assessment Methods"]["Course Outline"]["Learning Units"]["LU1"]["Description"]:
            if "Topic 1: Fundamentals of storytelling" in topic_desc["Topic"]:
                topic1_in_ensemble = topic_desc
                lu1_found = True
                break
    
    if not lu1_found:
        print("Error: Could not find Topic 1 in ensemble output")
        return
    
    # Compare raw and ensemble data
    print("\nEnsemble Output Topic 1 Data:")
    print(f"Topic: {topic1_in_ensemble['Topic']}")
    print(f"Details: {topic1_in_ensemble['Details']}")
    
    # Report if the details are preserved
    raw_details = topic1_cell.get('Details', [])
    ensemble_details = topic1_in_ensemble['Details']
    
    details_preserved = raw_details and all(item in ensemble_details for item in raw_details)
    
    print("\nAnalysis:")
    print(f"Raw Details count: {len(raw_details)}")
    print(f"Ensemble Details count: {len(ensemble_details)}")
    print(f"Details preserved correctly: {'Yes' if details_preserved else 'No'}")
    
    if not details_preserved:
        print("\nEXPECTED OUTPUT:")
        print(f"Topic: {topic1_in_ensemble['Topic']}")
        print(f"Details: {raw_details}")
        
        # Create a new ensemble output with the correct details
        corrected_ensemble = ensemble_data.copy()
        for topic_desc in corrected_ensemble["Assessment Methods"]["Course Outline"]["Learning Units"]["LU1"]["Description"]:
            if "Topic 1: Fundamentals of storytelling" in topic_desc["Topic"]:
                topic_desc["Details"] = raw_details
        
        # Save the corrected ensemble output
        corrected_path = "json_output/corrected_ensemble_output.json"
        with open(corrected_path, 'w', encoding='utf-8') as f:
            json.dump(corrected_ensemble, f, indent=4)
        
        print(f"\nCorrected ensemble output saved to {corrected_path}")

if __name__ == "__main__":
    examine_subtopics() 