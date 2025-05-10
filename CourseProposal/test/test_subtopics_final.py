import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_subtopics_in_all_components():
    """
    Test that subtopics are correctly handled in all components of the pipeline:
    1. Document parser (output_TSC_raw.json)
    2. TSC agent (output_TSC.json)
    3. Extraction agent (ensemble_output.json)
    4. Excel conversion (generated_mapping.json)
    """
    print("\n=== Testing Subtopics Handling Throughout Pipeline ===")
    
    # 1. Check document parser output (output_TSC_raw.json)
    with open('json_output/output_TSC_raw.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Find the table in TSC and Topics content
    print("\n1. Document Parser Output (output_TSC_raw.json):")
    raw_subtopics_found = False
    
    for item in raw_data["TSC and Topics"]["content"]:
        if isinstance(item, dict) and "table" in item:
            table = item["table"]
            for row in table:
                if len(row) >= 4 and isinstance(row[3], dict) and "Topic" in row[3]:
                    if "T1: Fundamentals of storytelling" in row[3]["Topic"]:
                        details = row[3].get("Details", [])
                        print(f"  Topic: {row[3]['Topic']}")
                        print(f"  Details: {details}")
                        if details and "Test1 Test1 Test1" in details and "Test2 Test2 Test2" in details:
                            raw_subtopics_found = True
                            print("  ✓ Subtopics correctly parsed in document parser output")
                        else:
                            print("  ✗ Subtopics missing in document parser output")
    
    if not raw_subtopics_found:
        print("  ✗ Topic 1 not found or subtopics missing in document parser output")
    
    # 2. Check TSC agent output (output_TSC.json)
    with open('json_output/output_TSC.json', 'r', encoding='utf-8') as f:
        tsc_data = json.load(f)
    
    print("\n2. TSC Agent Output (output_TSC.json):")
    tsc_subtopics_found = False
    
    # Look for LU1 in TSC output
    for key, value in tsc_data["Course_Proposal_Form"].items():
        if "LU1: Storytelling with Generative AI" in key:
            print(f"  Found LU1 in TSC output:")
            for line in value:
                print(f"    {line}")
                if "Test1 Test1 Test1" in line or "Test2 Test2 Test2" in line:
                    tsc_subtopics_found = True
    
    if tsc_subtopics_found:
        print("  ✓ Subtopics correctly preserved in TSC agent output")
    else:
        print("  ✗ Subtopics missing in TSC agent output")
    
    # 3. Check extraction agent output (ensemble_output.json)
    with open('json_output/ensemble_output.json', 'r', encoding='utf-8') as f:
        ensemble_data = json.load(f)
    
    print("\n3. Extraction Agent Output (ensemble_output.json):")
    ensemble_subtopics_found = False
    
    # Look for Topic 1 in LU1
    lu1_data = ensemble_data["Assessment Methods"]["Course Outline"]["Learning Units"].get("LU1", {})
    for desc in lu1_data.get("Description", []):
        if "Topic 1: Fundamentals of storytelling" in desc.get("Topic", ""):
            details = desc.get("Details", [])
            print(f"  Topic: {desc['Topic']}")
            print(f"  Details: {details}")
            if details and "Test1 Test1 Test1" in details and "Test2 Test2 Test2" in details:
                ensemble_subtopics_found = True
                print("  ✓ Subtopics correctly preserved in extraction agent output")
            else:
                print("  ✗ Subtopics missing in extraction agent output")
    
    if not ensemble_subtopics_found and "LU1" in ensemble_data["Assessment Methods"]["Course Outline"]["Learning Units"]:
        print("  ✗ Topic 1 found but subtopics missing in extraction agent output")
    
    # 4. Check Excel conversion output (generated_mapping.json)
    generated_mapping_path = 'json_output/generated_mapping.json'
    if os.path.exists(generated_mapping_path):
        with open(generated_mapping_path, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
        
        print("\n4. Excel Conversion Output (generated_mapping.json):")
        excel_subtopics_found = False
        
        # Look for Course Outline key that might contain the combined text with subtopics
        for key, value in mapping_data.items():
            if key == "#Course_Outline" and isinstance(value, str):
                if "Test1 Test1 Test1" in value and "Test2 Test2 Test2" in value:
                    excel_subtopics_found = True
                    print("  ✓ Subtopics correctly included in Excel mapping")
                    print(f"  Excerpt from mapping:\n    {value.split('Fundamentals of storytelling')[1].split('T2:')[0]}")
                else:
                    print("  ✗ Subtopics missing in Excel mapping")
        
        if not excel_subtopics_found:
            print("  ✗ Course Outline not found or subtopics missing in Excel mapping")
    else:
        print(f"  ! File {generated_mapping_path} does not exist - Excel pipeline may not have been run")
    
    # Final summary
    print("\n=== Summary ===")
    all_passed = raw_subtopics_found and tsc_subtopics_found and ensemble_subtopics_found
    if os.path.exists(generated_mapping_path):
        all_passed = all_passed and excel_subtopics_found
    
    if all_passed:
        print("✓ All components correctly handle subtopics")
    else:
        print("✗ Some components don't handle subtopics correctly:")
        if not raw_subtopics_found:
            print("  - Document parser doesn't parse subtopics correctly")
        if not tsc_subtopics_found:
            print("  - TSC agent doesn't preserve subtopics correctly")
        if not ensemble_subtopics_found:
            print("  - Extraction agent doesn't preserve subtopics correctly")
        if os.path.exists(generated_mapping_path) and not excel_subtopics_found:
            print("  - Excel conversion doesn't include subtopics correctly")

if __name__ == "__main__":
    test_subtopics_in_all_components() 