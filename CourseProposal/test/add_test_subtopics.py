import json
import os

def add_test_subtopics(ensemble_output_path):
    """
    Adds test subtopics to the first topic in ensemble_output.json if there are no subtopics.
    This is for testing the functionality to ensure subtopics are properly displayed.
    
    Args:
        ensemble_output_path (str): Path to the ensemble_output.json file
    """
    try:
        # Load the ensemble output JSON
        with open(ensemble_output_path, 'r', encoding='utf-8') as f:
            ensemble_data = json.load(f)
        
        # Check if TopicsWithSubtopics section exists
        if "TSC and Topics" in ensemble_data and "TopicsWithSubtopics" in ensemble_data["TSC and Topics"]:
            topics_with_subtopics = ensemble_data["TSC and Topics"]["TopicsWithSubtopics"]
            
            # Check if any topics have subtopics
            has_subtopics = any(len(subtopics) > 0 for subtopics in topics_with_subtopics.values())
            
            if not has_subtopics:
                print("No subtopics found in any topics. Adding test subtopics to the first topic...")
                
                # Get the first topic
                first_topic_key = list(topics_with_subtopics.keys())[0]
                
                # Add test subtopics to the first topic
                ensemble_data["TSC and Topics"]["TopicsWithSubtopics"][first_topic_key] = [
                    "Test subtopic 1 for demonstration",
                    "Test subtopic 2 for demonstration"
                ]
                
                # Update the Course Outline section to include these subtopics
                if "Assessment Methods" in ensemble_data and "Course Outline" in ensemble_data["Assessment Methods"]:
                    course_outline = ensemble_data["Assessment Methods"]["Course Outline"]
                    
                    # Find the LU that contains the first topic
                    for lu_key, lu_data in course_outline.get("Learning Units", {}).items():
                        for topic_idx, topic_data in enumerate(lu_data.get("Description", [])):
                            if topic_data.get("Topic") == first_topic_key:
                                # Update the Details array with the test subtopics
                                course_outline["Learning Units"][lu_key]["Description"][topic_idx]["Details"] = [
                                    "Test subtopic 1 for demonstration",
                                    "Test subtopic 2 for demonstration"
                                ]
                                print(f"Updated Details for {first_topic_key} in {lu_key}")
                
                # Save the updated JSON
                with open(ensemble_output_path, 'w', encoding='utf-8') as f:
                    json.dump(ensemble_data, f, indent=4)
                
                print(f"Successfully added test subtopics to {first_topic_key} in {ensemble_output_path}")
            else:
                print("Subtopics already exist in at least one topic. No changes needed.")
        else:
            print("Missing required TopicsWithSubtopics section in the JSON.")
    
    except FileNotFoundError:
        print(f"Error: The file {ensemble_output_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file {ensemble_output_path} contains invalid JSON.")
    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    ensemble_output_path = "CourseProposal/json_output/ensemble_output.json"
    add_test_subtopics(ensemble_output_path) 