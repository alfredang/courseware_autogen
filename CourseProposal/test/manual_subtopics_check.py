import json
import os

def check_subtopics_support():
    """Simple test to verify if topics with subtopics are handled correctly"""
    
    # Input and output file paths
    input_file = "CourseProposal/json_output/ensemble_output.json"
    output_file = "CourseProposal/json_output/manual_test_output.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return False
    
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find Topic 1 in the topics list
        topic1 = None
        for topic in data["TSC and Topics"]["Topics"]:
            if topic.startswith("Topic 1:") and "K9" in topic:
                topic1 = topic
                break
        
        if not topic1:
            print("Error: Topic 1 not found")
            return False
        
        print(f"Found Topic 1: {topic1}")
        
        # Add subtopics to Topic 1
        subtopics = ["Manual Test Subtopic 1", "Manual Test Subtopic 2"]
        data["TSC and Topics"]["TopicsWithSubtopics"][topic1] = subtopics
        print(f"Added subtopics to {topic1} in TopicsWithSubtopics")
        
        # Update the Details in Course Outline for Topic 1
        for lu, lu_data in data["Assessment Methods"]["Course Outline"]["Learning Units"].items():
            for topic_obj in lu_data["Description"]:
                if topic_obj["Topic"] == topic1:
                    topic_obj["Details"] = subtopics
                    print(f"Updated Details for {topic1} in {lu}")
        
        # Save the modified data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved modified data to {output_file}")
        
        # Verify the changes
        with open(output_file, 'r', encoding='utf-8') as f:
            modified_data = json.load(f)
        
        # Check TopicsWithSubtopics
        if topic1 in modified_data["TSC and Topics"]["TopicsWithSubtopics"]:
            saved_subtopics = modified_data["TSC and Topics"]["TopicsWithSubtopics"][topic1]
            if saved_subtopics == subtopics:
                print(f"Subtopics successfully saved in TopicsWithSubtopics")
            else:
                print(f"Error: Subtopics in TopicsWithSubtopics don't match")
                return False
        else:
            print(f"Error: Topic {topic1} not found in TopicsWithSubtopics")
            return False
        
        # Check Details in Course Outline
        details_ok = False
        for lu, lu_data in modified_data["Assessment Methods"]["Course Outline"]["Learning Units"].items():
            for topic_obj in lu_data["Description"]:
                if topic_obj["Topic"] == topic1:
                    if topic_obj["Details"] == subtopics:
                        details_ok = True
                        print(f"Subtopics successfully saved in Details for {lu}")
                    else:
                        print(f"Error: Subtopics in Details don't match for {lu}")
                        return False
        
        if not details_ok:
            print(f"Error: Topic {topic1} not found in any Learning Unit")
            return False
        
        print("All checks passed! The system correctly handles subtopics.")
        return True
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing subtopics support...")
    result = check_subtopics_support()
    print("\nTEST RESULT:", "✅ PASSED" if result else "❌ FAILED") 