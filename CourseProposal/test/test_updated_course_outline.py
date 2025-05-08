import json
from CourseProposal.utils.excel_conversion_pipeline import combine_los_and_topics

def test_updated_course_outline():
    # Load the ensemble_output.json
    with open('CourseProposal/json_output/ensemble_output.json', 'r') as f:
        ensemble_data = json.load(f)
    
    # Generate the updated course outline
    outline = combine_los_and_topics(ensemble_data)
    
    # Print just the first few lines to see the Learning Outcomes section
    print("==== UPDATED LEARNING OUTCOMES FORMAT ====")
    lines = outline.split('\n')
    for i, line in enumerate(lines):
        if i < 10:  # Print first 10 lines to focus on the Learning Outcomes
            print(line)
    print("...")
    print("==== END OF PREVIEW ====")

if __name__ == "__main__":
    test_updated_course_outline() 