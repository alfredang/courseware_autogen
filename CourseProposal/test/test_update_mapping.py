import json
from CourseProposal.utils.excel_conversion_pipeline import combine_los_and_topics

def update_mapping():
    # Load the ensemble_output.json
    with open('CourseProposal/json_output/ensemble_output.json', 'r') as f:
        ensemble_data = json.load(f)
    
    # Generate the course outline
    outline = combine_los_and_topics(ensemble_data)
    
    # Load the generated_mapping.json
    with open('CourseProposal/json_output/generated_mapping.json', 'r') as f:
        mapping_data = json.load(f)
    
    # Update the #Course_Outline field
    mapping_data["#Course_Outline"] = outline
    
    # Write the updated mapping back to the file
    with open('CourseProposal/json_output/generated_mapping.json', 'w') as f:
        json.dump(mapping_data, f, indent=4)
    
    print("Updated #Course_Outline in generated_mapping.json successfully!")

if __name__ == "__main__":
    update_mapping() 