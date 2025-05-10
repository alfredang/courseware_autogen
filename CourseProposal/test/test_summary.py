import sys
import os
import json
import traceback
import pandas as pd

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from CourseProposal.utils.excel_conversion_pipeline import create_course_dataframe, create_instructional_dataframe, create_assessment_dataframe, create_summary_dataframe

def test_summary_dataframe():
    try:
        print("Loading ensemble_output.json...")
        json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_output')
        ensemble_path = os.path.join(json_dir, 'ensemble_output.json')
        ensemble_output = json.load(open(ensemble_path, 'r', encoding='utf-8'))
        
        print("\nCreating course dataframe...")
        course_df = create_course_dataframe(ensemble_output)
        print(f"Course dataframe created with shape: {course_df.shape}")
        
        print("\nCreating instructional dataframe...")
        instructional_df = create_instructional_dataframe(ensemble_output)
        print(f"Instructional dataframe created with shape: {instructional_df.shape}")
        
        print("\nCreating assessment dataframe...")
        assessment_df = create_assessment_dataframe(ensemble_output)
        print(f"Assessment dataframe created with shape: {assessment_df.shape}")
        
        print("\nCreating summary dataframe...")
        summary_df = create_summary_dataframe(course_df, instructional_df, assessment_df)
        print(f"Summary dataframe created with shape: {summary_df.shape}")
        
        # Print the first few rows of the summary dataframe
        print("\nFirst 2 rows of summary dataframe:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(summary_df.head(2))
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_summary_dataframe()
    sys.exit(0 if success else 1) 