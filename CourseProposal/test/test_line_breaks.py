"""
Test script to verify line breaks are properly displayed in Excel output
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

def test_line_breaks():
    """Test line break handling in Excel XML generation"""
    # Import necessary modules
    excel_replace_module = import_module_from_path(
        "excel_replace_xml", 
        os.path.join(os.path.dirname(__file__), "utils", "excel_replace_xml.py")
    )
    
    # Create a temporary file for testing XML handling
    temp_dir = tempfile.mkdtemp()
    test_xml_path = os.path.join(temp_dir, "test_sheet.xml")
    test_output_excel = os.path.join(temp_dir, "test_output.xlsx")
    test_template_path = "templates/course_proposal_form_01apr2025_template.xlsx"
    
    # Sample course outline with line breaks
    course_outline = """Learning Outcomes
LO1: Use generative AI techniques to develop compelling script elements enriched with narrative structure and creative storytelling.
LO2: Identify effective prompt terms and narrative components to enhance AI-generated storyboards for visual storytelling.
LO3: Utilise generative AI tools to refine video scripts for clarity, tone, and narrative consistency.
LO4: Analyse generative AI outputs for ethical issues, bias, and copyright risks, applying appropriate corrective actions.

Course Outline:
LU1: Storytelling with Generative AI 
Topics:
•	T1: Fundamentals of storytelling 
•	T2: Basic AI models for script generation 
•	T3: Storytelling and storyboarding with generative AI 
•	T4: Generating stories with generative AI 

LU2: Storyboarding with Generative AI 
Topics:
•	T1: Fundamentals of storyboarding 
•	T2: Storyboard breakdown and text prompts for images 
•	T3: AI tool limitation and solutions to generate better images 
•	T4: Apply iterative approve to image generation 

LU3: Creating AI Generated Video 
Topics:
•	T1: AI Video tools for generating text, voiceover and video 
•	T2: Generating AI video for storyboard 

LU4: Generative AI Ethics and Best Practices 
Topics:
•	T1: Gen AI and ethics awareness 
•	T2: Best Practices to minimise plagiarism risk 
•	T3: Analyse AI output for bias and taking corrective steps 
•	T4: Copyright risk and avoid copyright infringement 
"""
    
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
    
    # Test JSON data files
    test_mapping = {
        "#Company": "Test Org",
        "#CourseTitle": "Test Course",
        "#TCS_Code_Skill": "TEST-CODE-1.1 Test TSC",
        "#Course_Outline": course_outline,
        "#Course_Background1": "This is a test course background",
        "#Sequencing_rationale": "This is a test sequencing rationale"
    }
    
    # Create necessary JSON files
    test_mapping_path = os.path.join(temp_dir, "test_mapping.json")
    test_ensemble_path = os.path.join(temp_dir, "test_ensemble.json")
    
    with open(test_mapping_path, 'w') as f:
        json.dump(test_mapping, f, indent=4)
    
    # Create a minimal ensemble output for testing
    ensemble_output = {
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
            "Learning Outcomes": ["LO1: Test learning outcome"],
            "Knowledge": ["K1: Test knowledge"],
            "Ability": ["A1: Test ability"],
            "Knowledge and Ability Mapping": {"KA1": ["K1", "A1"]}
        },
        "TSC and Topics": {
            "TSC Title": ["Test TSC"],
            "TSC Code": ["TEST-CODE-1.1"],
            "Topics": ["Topic 1: Test Topic (K1, A1)"],
            "Learning Units": ["LU1: Test Learning Unit"],
            "TopicsWithSubtopics": {
                "Topic 1: Test Topic (K1, A1)": [
                    "• Test subtopic 1",
                    "• Test subtopic 2"
                ]
            }
        },
        "Assessment Methods": {
            "Assessment Methods": ["Written Exam", "Practical Exam"],
            "Amount of Practice Hours": 2,
            "Course Outline": {
                "Learning Units": {
                    "LU1": {
                        "Description": [
                            {
                                "Topic": "Topic 1: Test Topic (K1, A1)",
                                "Details": [
                                    "• Test detail 1",
                                    "• Test detail 2",
                                    "• Test detail 3"
                                ]
                            }
                        ]
                    }
                }
            },
            "Instructional Methods": "Interactive Presentation, Brainstorming"
        }
    }
    
    with open(test_ensemble_path, 'w') as f:
        json.dump(ensemble_output, f, indent=4)
    
    try:
        # Test running update_cell_in_sheet function
        with open(test_xml_path, 'w', encoding='utf-8') as f:
            f.write(minimal_xml)
            
        # Update the cell with the course outline text
        excel_replace_module.update_cell_in_sheet(test_xml_path, "A1", course_outline)
        
        # Try to parse the XML to ensure it's well-formed
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(test_xml_path)
            print("✅ XML is well-formed after updating cell")
            
            # Now test the full Excel generation process
            print("\nTesting Excel generation with line breaks...")
            excel_replace_module.process_excel_update(
                test_mapping_path, 
                test_template_path, 
                test_output_excel, 
                test_ensemble_path
            )
            
            # Check if the file was created
            if os.path.exists(test_output_excel):
                print(f"✅ Excel file successfully generated at: {test_output_excel}")
                print(f"  You can open this file to verify the line breaks are properly displayed.")
            else:
                print(f"❌ Excel file was not created")
        except Exception as e:
            print(f"❌ XML parsing error: {str(e)}")
            print("Check the XML for malformed content")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        for f in [test_xml_path, test_mapping_path, test_ensemble_path]:
            if os.path.exists(f):
                os.remove(f)
        # Don't remove the output Excel file so it can be inspected

if __name__ == "__main__":
    # Add parent directory to path if needed
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Run the test
    print("Starting line break handling test...")
    test_line_breaks()
    print("Test completed!") 