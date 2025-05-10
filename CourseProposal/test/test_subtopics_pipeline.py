"""
Test script to verify the enhanced subtopics pipeline functionality.
"""
import json
import os
import sys
import logging
from CourseProposal.utils.document_parser import parse_document


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_subtopics_pipeline():
    """
    Test the end-to-end pipeline for parsing and processing subtopics.
    This test focuses only on the course dataframe with subtopics.
    """
    # 1. Use sample data with subtopics
    try:
        # Get test file paths
        input_file = "CourseProposal/json_output/output_TSC_raw.json"
        test_output_file = "CourseProposal/json_output/test_with_added_subtopics.json"
        
        logger.info(f"Loading test data from {input_file}")
        
        # Add sample subtopics to the test file
        if not create_sample_with_subtopics(input_file, test_output_file):
            logger.error("Failed to create sample with subtopics")
            return
        
        # 2. Load the test file with subtopics
        with open(test_output_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # Ensure Course Information and Learning Outcomes are present for Excel processing
        if "Course Information" not in test_data:
            test_data["Course Information"] = {"Course Title": "Test Course", "Name of Organisation": "Test Org", "Number of Assessment Hours": 2}
        
        if "Learning Outcomes" not in test_data:
            test_data["Learning Outcomes"] = {"Learning Outcomes": ["LO1: Test Learning Outcome"], "Knowledge": ["K1: Test Knowledge"], "Ability": ["A1: Test Ability"]}
            
        logger.info(f"Processing test data for Excel export")
        
        # 3. Export only the course dataframe with subtopics
        export_course_dataframe_with_subtopics(test_data)
        
        logger.info(f"Successfully exported course dataframe with subtopics to Excel")
        
    except Exception as e:
        logger.error(f"Error testing subtopics pipeline: {e}")
        import traceback
        traceback.print_exc()

def create_sample_with_subtopics(input_file, output_file):
    """
    Create a sample file with added subtopics for testing.
    This simulates what the document parser would process from a real document.
    """
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found")
        return False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Initialize TopicsWithSubtopics if not present
    if "TSC and Topics" not in data:
        data["TSC and Topics"] = {}
    
    if "TopicsWithSubtopics" not in data["TSC and Topics"]:
        data["TSC and Topics"]["TopicsWithSubtopics"] = {}
    
    # Get all topics from the parser output
    topics = data["TSC and Topics"].get("Topics", [])
    
    # Add sample subtopics to topics
    if topics:
        # Add subtopics to first topic
        data["TSC and Topics"]["TopicsWithSubtopics"][topics[0]] = [
            "Test subtopic 1 for demonstration",
            "Test subtopic 2 for demonstration"
        ]
        
        # Add subtopics to another topic if available
        if len(topics) > 1:
            data["TSC and Topics"]["TopicsWithSubtopics"][topics[1]] = [
                "Another test subtopic",
                "With bullet point examples"
            ]
    
    # Add Course Outline structure if not present
    if "Assessment Methods" not in data:
        data["Assessment Methods"] = {}
    
    if "Course Outline" not in data["Assessment Methods"]:
        data["Assessment Methods"]["Course Outline"] = {"Learning Units": {}}
    
    # Build Course Outline with topics and subtopics
    course_outline = data["Assessment Methods"]["Course Outline"]["Learning Units"]
    
    # Get Learning Units
    learning_units = data["TSC and Topics"].get("Learning Units", [])
    
    # Group topics by Learning Units
    for i, lu in enumerate(learning_units):
        lu_key = f"LU{i+1}"
        course_outline[lu_key] = {"Description": []}
        
        # Find topics related to this LU (simplified for test)
        lu_topics = []
        if i < len(topics):
            lu_topics.append(topics[i])
        
        # Add topics and their subtopics to the LU
        for topic in lu_topics:
            topic_entry = {
                "Topic": topic,
                "Details": data["TSC and Topics"]["TopicsWithSubtopics"].get(topic, [])
            }
            course_outline[lu_key]["Description"].append(topic_entry)
    
    # Save the modified data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Created sample file with subtopics at {output_file}")
    return True

def test_ensemble_output_details():
    """
    Test that the 'Details' field in ensemble_output.json is an empty list for topics without subtopics,
    and contains subtopics only for those that do.
    """
    with open('json_output/ensemble_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    course_outline = data["Assessment Methods"]["Course Outline"]["Learning Units"]
    print("\n=== Testing 'Details' field in ensemble_output.json ===")
    for lu, lu_data in course_outline.items():
        for desc in lu_data["Description"]:
            topic = desc["Topic"]
            details = desc["Details"]
            print(f"{topic} -> Details: {details}")
            # For this test, we expect only 'Topic 1: Fundamentals of storytelling (K9)' to have subtopics
            if topic == "Topic 1: Fundamentals of storytelling (K9)":
                assert details == [
                    "Test1 Test1 Test1",
                    "Test2 Test2 Test2"
                ], "Details should match subtopics for this topic."
            else:
                assert details == [], f"Details should be empty for topic: {topic}"
    print("All 'Details' fields are correct.")

if __name__ == "__main__":
    logger.info("Testing subtopics pipeline")
    test_subtopics_pipeline()
    test_ensemble_output_details() 