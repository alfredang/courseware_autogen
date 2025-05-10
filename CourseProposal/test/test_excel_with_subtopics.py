"""
Test script to verify Excel output with subtopics properly included
"""
import json
import os
import sys
import tempfile
import importlib.util

# Function to import a module from a file path
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Add sample topic with subtopics to a test JSON file
def create_test_data():
    # Create a minimal test JSON with a topic and subtopics
    test_data = {
        "Course Information": {
            "Course Title": "Test Course",
            "Name of Organisation": "Test Org",
            "Classroom Hours": 14,
            "Practical Hours": 2,
            "Number of Assessment Hours": 2,
            "Course Duration (Number of Hours)": 16,
            "Industry": "Media"
        },
        "Learning Outcomes": {
            "Learning Outcomes": [
                "LO1: Test learning outcome 1",
                "LO2: Test learning outcome 2" 
            ],
            "Knowledge": ["K1: Test knowledge"],
            "Ability": ["A1: Test ability"],
            "Knowledge and Ability Mapping": {"KA1": ["K1", "A1"]}
        },
        "TSC and Topics": {
            "TSC Title": ["Test TSC"],
            "TSC Code": ["TEST-CODE-1.1"],
            "Topics": [],
            "Learning Units": [
                "LU1: Test Learning Unit 1",
                "LU2: Test Learning Unit 2"
            ],
            "TopicsWithSubtopics": {
                "T1: Fundamentals of storytelling": [
                    "• Subtopic 1: Explore key elements",
                    "• Subtopic 2: Analyze narrative structures",
                    "• Subtopic 3: Test with XML special chars: < > & \" '"
                ],
                "T2: Basic AI models": [
                    "• Subtopic 1: Introduction to models",
                    "• Subtopic 2: Training techniques",
                    "• Subtopic 3: Complex formatting test\n  - Nested bullet\n  - Another nested item"
                ]
            }
        },
        "Assessment Methods": {
            "Assessment Methods": ["Written Exam", "Practical Exam"],
            "Instructional Methods": ["Classroom", "Practical"],
            "Course Outline": {
                "Learning Units": {
                    "LU1": {
                        "Description": [
                            {
                                "Topic": "Topic 1: Fundamentals of storytelling (K1)",
                                "Details": ["Detail 1", "Detail 2", "Detail with < > & symbols"]
                            }
                        ]
                    },
                    "LU2": {
                        "Description": [
                            {
                                "Topic": "Topic 2: Basic AI models (A1)",
                                "Details": ["Detail 1", "Detail 2", "Detail with line\nbreaks"]
                            }
                        ]
                    }
                }
            }
        }
    }
    
    # Add mapping JSON for excel generation
    mapping_data = {
        "#Company": "Test Org",
        "#CourseTitle": "Test Course",
        "#TCS_Code_Skill": "TEST-CODE-1.1 Test TSC",
        "#Course_Background1": "This is a test course background",
        "#Sequencing_rationale": "This is a test sequencing rationale.\nIt includes line breaks & special characters < > that need to be handled properly in XML."
    }
    
    return test_data, mapping_data

def test_xml_special_characters():
    """Test XML special character handling in update_cell_in_sheet function"""
    # Import necessary modules
    excel_replace_module = import_module_from_path(
        "excel_replace_xml", 
        os.path.join(os.path.dirname(__file__), "utils", "excel_replace_xml.py")
    )
    
    # Create a temporary file for testing XML handling
    temp_dir = tempfile.mkdtemp()
    test_xml_path = os.path.join(temp_dir, "test_sheet.xml")
    
    # Create a minimal XML file
    minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr">
        <is><t>Test</t></is>
      </c>
    </row>
  </sheetData>
</worksheet>
"""
    with open(test_xml_path, 'w', encoding='utf-8') as f:
        f.write(minimal_xml)
    
    # Test text with special characters
    special_chars_text = "Text with XML special chars: < > & \" '\nAnd with line breaks\n• Bullet points\n○ Circle bullets"
    
    try:
        # Call the function
        result = excel_replace_module.update_cell_in_sheet(test_xml_path, "A1", special_chars_text)
        
        # Read back the XML and check it's well-formed
        import xml.etree.ElementTree as ET
        tree = ET.parse(test_xml_path)
        
        print("✅ Successfully updated cell with XML special characters")
        return True
    except Exception as e:
        print(f"❌ XML handling test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(test_xml_path):
            os.remove(test_xml_path)
        os.rmdir(temp_dir)

def test_excel_generation():
    """Test Excel generation with subtopics"""
    # Set up paths for testing
    temp_dir = tempfile.mkdtemp()
    test_ensemble_path = os.path.join(temp_dir, "test_ensemble.json")
    test_mapping_path = os.path.join(temp_dir, "test_mapping.json")
    test_excel_data_path = os.path.join(temp_dir, "test_excel_data.json")
    test_output_excel = os.path.join(temp_dir, "test_output.xlsx")
    test_template_path = "templates/course_proposal_form_01apr2025_template.xlsx"
    
    # Create test data files
    ensemble_data, mapping_data = create_test_data()
    with open(test_ensemble_path, 'w') as f:
        json.dump(ensemble_data, f, indent=4)
    with open(test_mapping_path, 'w') as f:
        json.dump(mapping_data, f, indent=4)
    with open(test_excel_data_path, 'w') as f:
        json.dump([{"course_overview": {"course_description": "Test"}}], f, indent=4)
    
    # Import necessary modules
    excel_replace_module = import_module_from_path(
        "excel_replace_xml", 
        os.path.join(os.path.dirname(__file__), "utils", "excel_replace_xml.py")
    )
    
    # Process Excel update
    try:
        # Test running excel_replace function
        print(f"Testing Excel generation with subtopics")
        excel_replace_module.process_excel_update(
            test_mapping_path, 
            test_template_path, 
            test_output_excel, 
            test_ensemble_path
        )
        
        # Check if the file was created
        if os.path.exists(test_output_excel):
            print(f"✅ Excel file successfully generated at: {test_output_excel}")
            print(f"  You can open this file to verify the subtopics are properly displayed.")
        else:
            print(f"❌ Excel file was not created")
    except Exception as e:
        print(f"❌ Error during Excel generation: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        for f in [test_ensemble_path, test_mapping_path, test_excel_data_path]:
            if os.path.exists(f):
                os.remove(f)
        # Don't remove the output Excel file so it can be inspected

if __name__ == "__main__":
    # Add parent directory to path if needed
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Run the tests
    print("Starting XML special character handling test...")
    xml_test_result = test_xml_special_characters()
    
    if xml_test_result:
        print("\nStarting Excel generation test with subtopics...")
        test_excel_generation()
    
    print("Test completed!") 