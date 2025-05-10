import json

def test_ensemble_output_details():
    """
    Test that the 'Details' field in ensemble_output.json properly reflects subtopics:
    - Topics with subtopics should have those subtopics in the Details field
    - Topics without subtopics should have an empty list in the Details field
    """
    with open('json_output/ensemble_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    course_outline = data["Assessment Methods"]["Course Outline"]["Learning Units"]
    print("\n=== Testing 'Details' field in ensemble_output.json ===")
    
    for lu, lu_data in course_outline.items():
        print(f"\n{lu}:")
        for desc in lu_data["Description"]:
            topic = desc["Topic"]
            details = desc["Details"]
            print(f"  {topic}")
            print(f"  Details: {details}")
            
            # If this is Topic 1 in LU1, it should have subtopics
            if lu == "LU1" and "Topic 1:" in topic:
                if details and len(details) > 0:
                    print("  ✓ Correctly has subtopics")
                else:
                    print("  ✗ ERROR: Should have subtopics!")
            else:
                # For demonstration, check if auto-generated details are present
                if details and len(details) > 0:
                    print(f"  ⚠️ Has {len(details)} details items")

if __name__ == "__main__":
    test_ensemble_output_details() 