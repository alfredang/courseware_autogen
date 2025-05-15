# document_parser.py

from docx import Document
import json
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
import re

def parse_document(input_docx, output_json):
    # Load the document
    doc = Document(input_docx)

    # Initialize containers
    data = {
        "Course Information": {
            "Course Level": ""
        },
        "Learning Outcomes": {
            "Learning Outcomes": [],
            "Knowledge": [],
            "Ability": [],
            "Knowledge and Ability Mapping": {},
            "Course Duration": "",
            "Instructional Methods": "",
            "content": []
        },
        "TSC and Topics": {
            "TSC Title": "",
            "TSC Code": "",
            "Topics": [],
            "Learning Units": []
        },
        "Assessment Methods": {
            "Assessment Methods": [],
            "Amount of Practice Hours": "",
            "Course Outline": {
                "Learning Units": {}
            },
            "content": [],
            "Assessment Details": {
                "Written Exam": "",
                "Practical Exam": "",
                "Total Assessment Hours": ""
            }
        }
    }

    # Function to parse tables
    def parse_table(table):
        rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)
        return rows

    # Function to add text and table content
    def add_content_to_section(section_name, content):
        if isinstance(data[section_name], list):
            # Check for duplication before adding content
            if content not in data[section_name]:
                data[section_name].append(content)
        elif isinstance(data[section_name], dict):
            # Handle nested dictionaries appropriately
            if "content" not in data[section_name]:
                data[section_name]["content"] = []
            if content not in data[section_name]["content"]:
                data[section_name]["content"].append(content)

    # Function to detect bullet points using regex
    def is_bullet_point(text):
        bullet_pattern = r"^[•−–●◦]\s+.*"
        return bool(re.match(bullet_pattern, text))

    # Function to add bullet points under a list
    def add_bullet_point(section_name, bullet_point_text):
        if "bullet_points" not in data[section_name]:
            data[section_name]["bullet_points"] = []
        data[section_name]["bullet_points"].append(bullet_point_text)

    # Function to parse assessment methods and hours
    def parse_assessment_methods(text):
        if "Written Exam" in text:
            hours = re.search(r"Written Exam\s*\((\d+)\s*hr\)", text)
            if hours:
                data["Assessment Methods"]["Assessment Details"]["Written Exam"] = f"{hours.group(1)} hr"
        if "Practical Exam" in text:
            hours = re.search(r"Practical Exam\s*\((\d+)\s*hr\)", text)
            if hours:
                data["Assessment Methods"]["Assessment Details"]["Practical Exam"] = f"{hours.group(1)} hr"
        
        # Calculate total assessment hours
        written_hours = int(data["Assessment Methods"]["Assessment Details"]["Written Exam"].split()[0]) if data["Assessment Methods"]["Assessment Details"]["Written Exam"] else 0
        practical_hours = int(data["Assessment Methods"]["Assessment Details"]["Practical Exam"].split()[0]) if data["Assessment Methods"]["Assessment Details"]["Practical Exam"] else 0
        total_hours = written_hours + practical_hours
        data["Assessment Methods"]["Assessment Details"]["Total Assessment Hours"] = f"{total_hours} hr"

    # Variables to track the current section
    current_section = None

    # Iterate through the elements of the document
    for element in doc.element.body:
        if isinstance(element, CT_P):  # It's a paragraph
            para = Paragraph(element, doc)
            text = para.text.strip()

            # If the text indicates a new section, set current_section
            if text.lower().startswith("course title:"):
                current_section = "Course Information"
                # Extract the course title
                course_title = text[len("Course Title:"):].strip()
                data["Course Information"]["Course Title"] = course_title
            elif text.lower().startswith("course level:"):
                # Extract the course level
                data["Course Information"]["Course Level"] = text[len("Course Level:"):].strip()
            elif text.lower().startswith("organization:"):
                data["Course Information"]["Name of Organisation"] = text[len("Organization:"):].strip()
            elif text.startswith("Learning Outcomes"):
                current_section = "Learning Outcomes"
            elif text.startswith("Course Mapping"):
                current_section = "TSC and Topics"
            elif text.startswith("Assessment Methods:"):
                current_section = "Assessment Methods"
                # Parse assessment methods and hours
                parse_assessment_methods(text)
                # Add to assessment methods list
                methods = text.replace("Assessment Methods:", "").strip()
                data["Assessment Methods"]["Assessment Methods"] = [method.strip() for method in methods.split(",")]
            elif text:
                # Handle specific content types
                if text.startswith("Course Duration:"):
                    data["Learning Outcomes"]["Course Duration"] = text.replace("Course Duration:", "").strip()
                elif text.startswith("Instructional Methods:"):
                    data["Learning Outcomes"]["Instructional Methods"] = text.replace("Instructional Methods:", "").strip()
                # Check if the paragraph is a bullet point using regex
                elif is_bullet_point(text):
                    add_bullet_point(current_section, text)
                else:
                    add_content_to_section(current_section, text)
        elif isinstance(element, CT_Tbl):  # It's a table
            tbl = Table(element, doc)
            table_content = parse_table(tbl)
            if current_section:
                add_content_to_section(current_section, {"table": table_content})

    # Convert to JSON
    json_output = json.dumps(data, indent=4, ensure_ascii=False)

    # Save the JSON to a file in the current working directory
    with open(output_json, "w", encoding="utf-8") as json_file:
        json_file.write(json_output)

    print(f"{input_docx} JSON output saved to {output_json}")

# if __name__ == "__main__":
#     # Get input and output file paths from command-line arguments
#     if len(sys.argv) != 3:
#         print("Usage: python document_parser.py <input_docx> <output_json>")
#         sys.exit(1)
#     input_docx = sys.argv[1]
#     output_json = sys.argv[2]
#     parse_document(input_docx, output_json)