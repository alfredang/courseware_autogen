import sys
import os
import json
# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from CourseProposal.utils.excel_conversion_pipeline import create_course_dataframe

def test_course_dataframe():
    try:
        ensemble_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_output', 'ensemble_output.json')
        print(f"Loading files from: {ensemble_json_path}")
        ensemble_output = json.load(open(ensemble_json_path, 'r', encoding='utf-8'))

        print("\nTesting create_course_dataframe function...")
        df = create_course_dataframe(ensemble_output)
        print(f"Course DataFrame empty: {df.empty}")
        print(f"Course DataFrame shape: {df.shape}")
        
        if df.empty:
            print("\nExamining the data structure to identify the issue:")
            print(f"Learning Units: {len(ensemble_output['TSC and Topics'].get('Learning Units', []))}")
            print(f"Learning Outcomes: {len(ensemble_output['Learning Outcomes'].get('Learning Outcomes', []))}")
            print(f"Knowledge statements: {len(ensemble_output['Learning Outcomes'].get('Knowledge', []))}")
            print(f"Ability statements: {len(ensemble_output['Learning Outcomes'].get('Ability', []))}")
            print(f"Course Outline type: {type(ensemble_output.get('Course Outline', {}))}")
            print(f"Course Outline keys: {ensemble_output.get('Course Outline', {}).keys()}")
            if 'Learning Units' in ensemble_output.get('Course Outline', {}):
                for lu_key, lu_data in ensemble_output['Course Outline']['Learning Units'].items():
                    print(f"LU key: {lu_key}")
                    print(f"  Description count: {len(lu_data.get('Description', []))}")

        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_course_dataframe()
    sys.exit(0 if success else 1) 