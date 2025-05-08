import json
from CourseProposal.utils.excel_conversion_pipeline import combine_los_and_topics

def test_course_outline():
    # Load the ensemble_output.json
    with open('CourseProposal/json_output/ensemble_output.json', 'r') as f:
        ensemble_data = json.load(f)
    
    # Generate the course outline
    outline = combine_los_and_topics(ensemble_data)
    
    # Print the full outline
    print("==== COURSE OUTLINE ====")
    print(outline)
    print("==== END OF COURSE OUTLINE ====")

if __name__ == "__main__":
    test_course_outline() 