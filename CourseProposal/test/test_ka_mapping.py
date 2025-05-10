import json
import re
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_ka_mappings():
    """
    Test script to diagnose issues with Knowledge and Ability factors not being mapped to topics
    """
    print("\n=== Analyzing Knowledge and Ability Mapping Issues ===")
    
    # 1. Load the TSC data (where we extract LU -> K&A mappings from)
    tsc_path = 'json_output/output_TSC.json'
    print(f"\nLoading TSC data from: {tsc_path}")
    try:
        with open(tsc_path, 'r', encoding='utf-8') as f:
            tsc_data = json.load(f)
            print("[OK] Successfully loaded TSC data")
    except FileNotFoundError:
        print(f"Error: File {tsc_path} not found!")
        return
    except json.JSONDecodeError:
        print(f"Error: File {tsc_path} contains invalid JSON!")
        return
    
    # 2. Load the ensemble output (where final K&A mappings should be)
    ensemble_path = 'json_output/ensemble_output.json'
    print(f"\nLoading ensemble data from: {ensemble_path}")
    try:
        with open(ensemble_path, 'r', encoding='utf-8') as f:
            ensemble_data = json.load(f)
            print("[OK] Successfully loaded ensemble data")
    except FileNotFoundError:
        print(f"Error: File {ensemble_path} not found!")
        return
    except json.JSONDecodeError:
        print(f"Error: File {ensemble_path} contains invalid JSON!")
        return
    
    # 3. Analyze Learning Units in TSC data
    print("\nAnalyzing Learning Units in TSC data:")
    course_proposal_form = tsc_data.get("Course_Proposal_Form", {})
    learning_units = {key: value for key, value in course_proposal_form.items() if key.startswith("LU")}
    
    print(f"Found {len(learning_units)} Learning Units")
    
    # 4. Extract K&A factors from each Learning Unit
    lu_ka_mappings = {}
    for lu_key, topics in learning_units.items():
        print(f"\nAnalyzing {lu_key}:")
        ka_mapping = []
        for topic in topics:
            print(f"  Topic: {topic}")
            # Extract K and A factors using regex
            matches = re.findall(r'\b(K\d+|A\d+)\b', topic)
            if matches:
                print(f"    Found K&A factors: {matches}")
                ka_mapping.extend(matches)
            else:
                print(f"    No K&A factors found in this topic")
        
        # Remove duplicates
        ka_mapping = list(dict.fromkeys(ka_mapping))
        lu_ka_mappings[lu_key] = ka_mapping
        print(f"  Total unique K&A factors: {ka_mapping}")
    
    # 5. Compare with ensemble output
    print("\nComparing with K&A mapping in ensemble output:")
    ensemble_ka_mapping = ensemble_data["Learning Outcomes"].get("Knowledge and Ability Mapping", {})
    
    print(f"K&A mapping in ensemble output: {ensemble_ka_mapping}")
    
    # 6. Check topics array in ensemble output
    print("\nChecking topics array in ensemble output:")
    topics = ensemble_data["TSC and Topics"].get("Topics", [])
    
    print(f"Found {len(topics)} topics")
    
    topic_factors = set()
    for topic in topics:
        print(f"  Topic: {topic}")
        # Extract K and A factors from the topic
        matches = re.findall(r'\b(K\d+|A\d+)\b', topic)
        if matches:
            print(f"    Found K&A factors: {matches}")
            topic_factors.update(matches)
        else:
            print(f"    No K&A factors found in this topic")
    
    print(f"\nUnique K&A factors in topics: {topic_factors}")
    
    # 7. Check knowledge and ability lists
    print("\nChecking knowledge and ability lists:")
    knowledge_factors = set([k.split(":")[0].strip() for k in ensemble_data['Learning Outcomes']['Knowledge']])
    ability_factors = set([a.split(":")[0].strip() for a in ensemble_data['Learning Outcomes']['Ability']])
    
    print(f"Knowledge factors: {knowledge_factors}")
    print(f"Ability factors: {ability_factors}")
    
    # 8. Run the validation logic to check missing factors
    print("\nRunning validation logic to find missing factors:")
    missing_factors = []
    
    # Check each Knowledge factor
    for k in knowledge_factors:
        if k not in topic_factors:
            missing_factors.append(f"Knowledge factor {k} is missing from topics")
    
    # Check each Ability factor
    for a in ability_factors:
        if a not in topic_factors:
            missing_factors.append(f"Ability factor {a} is missing from topics")
    
    if missing_factors:
        print("\n[FAIL] Found missing factors:")
        for missing in missing_factors:
            print(f"  - {missing}")
    else:
        print("\n[OK] All K&A factors are properly mapped to topics")
    
    # 9. Check the LU structure in Course Outline
    print("\nChecking LU structure in Course Outline:")
    # Fixed path to Course Outline -> Learning Units
    course_outline = ensemble_data.get("Course Outline", {}).get("Learning Units", {})
    if not course_outline:
        print(f"Course Outline structure not found directly. Checking alternative paths...")
        # Try a different path - this is the correct path
        course_outline = ensemble_data.get("Assessment Methods", {}).get("Course Outline", {}).get("Learning Units", {})
    
    if course_outline:
        for lu_key, lu_data in course_outline.items():
            print(f"\n{lu_key}:")
            descriptions = lu_data.get("Description", [])
            for desc in descriptions:
                if isinstance(desc, dict) and "Topic" in desc:
                    topic = desc["Topic"]
                    details = desc.get("Details", [])
                    print(f"  Topic: {topic}")
                    # Extract K and A factors from the topic
                    matches = re.findall(r'\b(K\d+|A\d+)\b', topic)
                    if matches:
                        print(f"    Found K&A factors: {matches}")
                    else:
                        print(f"    No K&A factors found in this topic")
                    print(f"    Subtopics: {details}")
                else:
                    print(f"  Invalid topic format: {desc}")
    else:
        print("No Course Outline structure found in the expected paths!")
    
    # 10. Provide a summary and potential solution
    print("\n=== Summary and Recommendation ===")
    if missing_factors:
        print("\nIssue detected: K&A factors are missing from the Topics array.")
        print("\nPossible causes:")
        print("1. The K&A factors no longer appear in the topics in the TSC file")
        print("2. The topics array in ensemble_output.json doesn't include K&A factors")
        print("3. The update_knowledge_ability_mapping function isn't correctly extracting K&A factors")
        
        # Special check: look for KA factors in Learning Unit titles
        print("\nChecking for K&A factors in Learning Unit titles:")
        lu_titles = ensemble_data["TSC and Topics"].get("Learning Units", [])
        ka_in_lu_titles = False
        for lu_title in lu_titles:
            matches = re.findall(r'\b(K\d+|A\d+)\b', lu_title)
            if matches:
                ka_in_lu_titles = True
                print(f"  Found K&A factors in LU title: {lu_title}")
                print(f"  Factors: {matches}")
        
        if ka_in_lu_titles:
            print("\nThe K&A factors are present in the Learning Unit titles but not in the topics!")
            print("This suggests the validation logic should be updated to look for K&A factors in LU titles too.")
            
            print("\nRecommended solution:")
            print("1. Modify the validate_knowledge_and_ability function to check both topics AND Learning Unit titles")
            print("2. Fix the update_knowledge_ability_mapping function to extract K&A from LU titles rather than topics")
        else:
            print("\nRecommended solution:")
            print("Check the Topics extraction logic to ensure K&A factors are included in the topics")
    else:
        print("\nNo issues detected with K&A mapping.")

if __name__ == "__main__":
    analyze_ka_mappings() 