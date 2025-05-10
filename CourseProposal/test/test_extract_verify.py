import json
import os
import re

def test_parse_extract_verify():
    """
    Test that the document parser and extraction agent correctly handle subtopics:
    - Parse a document with a topic that has subtopics
    - Run the extraction agent
    - Verify the 'Details' field in ensemble_output.json contains the correct subtopics
    """
    # Expected values based on the document
    expected_topic1_details = [
        "Test1 Test1 Test1",
        "Test2 Test2 Test2"
    ]
    
    # Check the output_TSC_raw.json file first (from document parser)
    with open('json_output/output_TSC_raw.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Check if topics in TSC Mapping table have the expected Details
    tsc_mapping_table = None
    for item in raw_data["TSC and Topics"]["content"]:
        if isinstance(item, dict) and "table" in item:
            tsc_mapping_table = item["table"]
            break
    
    if tsc_mapping_table:
        print("Checking output_TSC_raw.json:")
        for row in tsc_mapping_table[1:]:  # Skip header row
            # Check if this is the topic with subtopics
            if isinstance(row[3], dict) and row[3].get("Topic", "").startswith("T1: Fundamentals of storytelling"):
                details = row[3].get("Details", [])
                print(f"Topic 1 'Details' in output_TSC_raw.json: {details}")
                if details == expected_topic1_details:
                    print("✓ Topic 1 'Details' are correct in raw output")
                else:
                    print("✗ Topic 1 'Details' are incorrect in raw output")
    else:
        print("TSC Mapping table not found in output_TSC_raw.json")
    
    # Check the ensemble_output.json file (from extraction agent)
    with open('json_output/ensemble_output.json', 'r', encoding='utf-8') as f:
        ensemble_data = json.load(f)
    
    print("\nChecking ensemble_output.json:")
    # Get the topics from LU1 Description
    lu1_description = ensemble_data["Assessment Methods"]["Course Outline"]["Learning Units"]["LU1"]["Description"]
    
    for topic_desc in lu1_description:
        topic = topic_desc["Topic"]
        details = topic_desc["Details"]
        print(f"{topic}\nDetails: {details}")
        
        # Check if this is Topic 1 (Fundamentals of storytelling)
        if "Topic 1: Fundamentals of storytelling" in topic:
            if details == expected_topic1_details:
                print("✓ Topic 1 'Details' are correct in ensemble output")
            else:
                print("✗ Topic 1 'Details' are incorrect in ensemble output")
                print(f"  Expected: {expected_topic1_details}")
                print(f"  Actual: {details}")

if __name__ == "__main__":
    test_parse_extract_verify() 