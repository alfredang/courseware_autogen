import sys
import os
import json
import traceback

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from CourseProposal.utils.excel_conversion_pipeline import create_instructional_dataframe
from CourseProposal.utils.excel_conversion_pipeline import create_instruction_description_dataframe

def test_dataframes():
    try:
        ensemble_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_output', 'ensemble_output.json')
        print(f"Loading files from: {ensemble_json_path}")
        ensemble_output = json.load(open(ensemble_json_path, 'r', encoding='utf-8'))
        
        print("\nTesting create_instructional_dataframe function...")
        df = create_instructional_dataframe(ensemble_output)
        print(f"Success! DataFrame shape: {df.shape}")
        
        print("\nTesting create_instruction_description_dataframe function...")
        # You'd need to have the im_agent_data.json file, skip if not available
        try:
            im_agent_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_output', 'im_agent_data.json')
            df2 = create_instruction_description_dataframe(
                ensemble_json_path, 
                im_agent_json_path
            )
            print(f"Success! Description DataFrame shape: {df2.shape}")
        except FileNotFoundError:
            print("Skipping description dataframe test - im_agent_data.json not found")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dataframes()
    sys.exit(0 if success else 1) 