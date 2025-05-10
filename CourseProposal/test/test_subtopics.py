"""
Test script to verify the document parser's enhanced support for topic subtopics.
"""
import json
import os
import sys
import importlib.util

# Function to import a module from a file path
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Add sample topic with subtopics to a test JSON file
def create_test_json():
    # Create a minimal test JSON with a topic and subtopics
    test_data = {
        "Course Information": {
            "Course Title": "Test Course",
            "Name of Organisation": "Test Org"
        },
        "Learning Outcomes": {
            "Learning Outcomes": ["LO1: Test learning outcome"],
            "Knowledge": ["K1: Test knowledge"],
            "Ability": ["A1: Test ability"],
            "Knowledge and Ability Mapping": {"KA1": ["K1", "A1"]}
        },
        "TSC and Topics": {
            "TSC Title": "Test TSC",
            "TSC Code": ["TEST-CODE-1.1"],
            "Topics": [],
            "Learning Units": ["LU1: Test Learning Unit"],
            "TopicsWithSubtopics": {
                "T1: Fundamentals of storytelling": [
                    "• Subtopic 1: Explore key elements",
                    "• Subtopic 2: Analyze narrative structures"
                ],
                "T2: Basic AI models": [
                    "• Subtopic 1: Introduction to models",
                    "• Subtopic 2: Training techniques"
                ]
            }
        },
        "Assessment Methods": {
            "Assessment Methods": ["Written Exam", "Practical Exam"],
            "Course Outline": {
                "Learning Units": {
                    "LU1": {
                        "Description": [
                            {
                                "Topic": "Topic 1: Fundamentals of storytelling (K1)",
                                "Details": ["Detail 1", "Detail 2"]
                            },
                            {
                                "Topic": "Topic 2: Basic AI models (A1)",
                                "Details": ["Detail 1", "Detail 2"]
                            }
                        ]
                    }
                }
            }
        }
    }
    
    with open("test_data.json", "w") as f:
        json.dump(test_data, f, indent=4)
    
    return test_data

# Test the combine_los_and_topics function
def test_combine_los_and_topics():
    # Import functions directly from files
    excel_conversion_pipeline = import_module_from_path(
        "excel_conversion_pipeline", 
        os.path.join(os.path.dirname(__file__), "utils", "excel_conversion_pipeline.py")
    )
    
    # Load the test data
    test_data = create_test_json()
    
    # Run the function from the imported module
    result = excel_conversion_pipeline.combine_los_and_topics(test_data)
    
    print("======= Test: combine_los_and_topics =======")
    print(result)
    print("============================================")
    
    # Check if the result contains subtopics
    if "○" in result:
        print("✅ Subtopics are included in the course outline")
    else:
        print("❌ Subtopics are NOT included in the course outline")

# Test the create_course_dataframe function
def test_create_course_dataframe():
    # Import functions directly from files
    excel_conversion_pipeline = import_module_from_path(
        "excel_conversion_pipeline", 
        os.path.join(os.path.dirname(__file__), "utils", "excel_conversion_pipeline.py")
    )
    
    # Load the test data
    test_data = create_test_json()
    
    # Run the function from the imported module
    df = excel_conversion_pipeline.create_course_dataframe(test_data)
    
    print("\n======= Test: create_course_dataframe =======")
    print(df)
    print("=============================================")
    
    # Check if subtopics appear in the Topic column
    topic_col = df["Topic (T#: Topic title)"].astype(str)
    if any("○" in topic for topic in topic_col):
        print("✅ Subtopics are included in the course dataframe")
    else:
        print("❌ Subtopics are NOT included in the course dataframe")

# Run the tests
if __name__ == "__main__":
    try:
        print("Starting tests for subtopics handling...")
        
        # Add parent directory to path if needed
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        # Run the tests
        test_combine_los_and_topics()
        test_create_course_dataframe()
        
        # Clean up
        if os.path.exists("test_data.json"):
            os.remove("test_data.json")
            
        print("\nTests completed!")
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        raise 