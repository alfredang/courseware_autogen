"""
Test script to verify Excel generation with real ensemble output data
"""
import os
import sys
import tempfile

def test_excel_with_real_data():
    """
    Test Excel generation with the real ensemble_output.json data
    """
    # Import the necessary modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from CourseProposal.utils import excel_replace_xml
    
    # File paths
    ensemble_output_path = "json_output/ensemble_output.json"
    template_path = "templates/course_proposal_form_01apr2025_template.xlsx"
    
    # Create output in temp directory
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "real_data_output.xlsx")
    
    # Create a temp mapping file with basic fields
    mapping_data = {
        "#Company": "Test Organization",
        "#CourseTitle": "AI Content Generation for Script Development",
        "#TCS_Code_Skill": "MED-MED-3004-1.1 AI Content Generation for Script Development",
        "#Sequencing_rationale": "Topics are sequenced from basic to advanced to ensure progressive skill development."
    }
    
    # Write mapping to temp file
    import json
    mapping_path = os.path.join(temp_dir, "mapping.json")
    with open(mapping_path, 'w') as f:
        json.dump(mapping_data, f, indent=2)
    
    try:
        print(f"Using ensemble output from: {ensemble_output_path}")
        print(f"Using template from: {template_path}")
        print(f"Output will be saved to: {output_path}")
        
        # Process the Excel update
        excel_replace_xml.process_excel_update(
            mapping_path,
            template_path,
            output_path,
            ensemble_output_path
        )
        
        # Verify the output was created
        if os.path.exists(output_path):
            print(f"✅ Excel file successfully generated: {output_path}")
            print("You can open this file to verify the content is displayed correctly.")
        else:
            print(f"❌ Excel file was not created")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Excel generation test with real data...")
    test_excel_with_real_data()
    print("Test completed!") 