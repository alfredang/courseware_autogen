import sys
import os
import json
import traceback

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from CourseProposal.utils.json_mapping import map_values
from CourseProposal.utils.excel_conversion_pipeline import combine_los_and_topics

def test_mapping():
    try:
        print("Loading files...")
        # Use absolute paths
        json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'json_output')
        ensemble_path = os.path.join(json_dir, 'ensemble_output.json')
        research_path = os.path.join(json_dir, 'research_output.json')
        mapping_path = os.path.join(json_dir, 'mapping_source.json')
        
        ensemble_output = json.load(open(ensemble_path, 'r', encoding='utf-8'))
        research_output = json.load(open(research_path, 'r', encoding='utf-8'))
        mapping_source = json.load(open(mapping_path, 'r', encoding='utf-8'))
        
        print("Testing combine_los_and_topics function...")
        try:
            result = combine_los_and_topics(ensemble_output)
            print("Success! combine_los_and_topics function executed without errors.")
            print(f"First 200 characters of output: {result[:200]}...")
        except Exception as e:
            print(f"Error in combine_los_and_topics: {e}")
            print("Traceback:")
            traceback.print_exc()
            return False
        
        print("\nTesting map_values function...")
        try:
            result = map_values(mapping_source, ensemble_output, research_output)
            print("Success! map_values function executed without errors.")
            return True
        except Exception as e:
            print(f"Error in map_values: {e}")
            print("Traceback:")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mapping()
    sys.exit(0 if success else 1) 