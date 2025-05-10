import json
import os
import sys
import pandas as pd
# Add the parent directory to sys.path so Python can find the CourseProposal module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from CourseProposal.utils.excel_conversion_pipeline import create_course_dataframe, combine_los_and_topics

def test_excel_subtopics():
    """
    Test how subtopics in the "Details" field are handled by the Excel conversion pipeline.
    Specifically, verify that combine_los_and_topics function correctly processes subtopics.
    """
    # Load the ensemble_output.json file
    with open('json_output/ensemble_output.json', 'r', encoding='utf-8') as f:
        ensemble_data = json.load(f)
    
    print("\n=== Testing subtopics handling in Excel conversion pipeline ===")
    
    # Test the combine_los_and_topics function
    combined_text = combine_los_and_topics(ensemble_data)
    print("\nOutput of combine_los_and_topics function:")
    print(combined_text)
    
    # Check if subtopics are visible in the output
    if "Test1 Test1 Test1" in combined_text or "Test2 Test2 Test2" in combined_text:
        print("\n✓ Subtopics are included in the combined text")
    else:
        print("\n✗ Subtopics are NOT included in the combined text")
    
    # Test the create_course_dataframe function
    course_df = create_course_dataframe(ensemble_data)
    print("\nOutput of create_course_dataframe function:")
    print(course_df.head())
    
    # Save the dataframe to a CSV for inspection
    csv_path = 'json_output/test_course_dataframe.csv'
    course_df.to_csv(csv_path, index=False)
    print(f"\nSaved course dataframe to {csv_path} for inspection")
    
    # Check if subtopics are handled in the "Applicable K&A Statement" column
    # by searching for the Test1/Test2 content
    subtopics_found = False
    for idx, row in course_df.iterrows():
        if "Topic 1: Fundamentals of storytelling" in row["Topic (T#: Topic title)"]:
            print(f"\nFound Topic 1 in row {idx}:")
            print(f"  Topic: {row['Topic (T#: Topic title)']}")
            print(f"  K&A Statement: {row['Applicable K&A Statement']}")
            
            # Check if subtopics are included in K&A Statement
            if isinstance(row['Applicable K&A Statement'], str) and ("Test1" in row['Applicable K&A Statement'] or "Test2" in row['Applicable K&A Statement']):
                subtopics_found = True
                print("  ✓ Subtopics found in K&A Statement")
            else:
                print("  ✗ Subtopics NOT found in K&A Statement")
    
    print("\nConclusion:")
    if subtopics_found:
        print("Excel conversion pipeline includes subtopics in the output")
    else:
        print("Excel conversion pipeline does NOT include subtopics in the output")
        print("This is expected as subtopics are meant to be content details, not K&A statements")

if __name__ == "__main__":
    test_excel_subtopics() 