import autogen
import dotenv
import json
import os
from autogen import UserProxyAgent, AssistantAgent
from pprint import pprint
import subprocess
import sys
import streamlit as st

def execute_document_parser(input_docx, output_json):
    subprocess.run([sys.executable, "document_parser.py", input_docx, output_json], check=True)
    print("document_parser.py executed successfully.")

def execute_json_docu_replace(input_json, input_docx, output_docx):
    subprocess.run([sys.executable, "json_docu_replace.py", input_json, input_docx, output_docx], check=True)
    print("json_docu_replace.py executed successfully.")

def execute_json_mapping():
    subprocess.run([sys.executable, "json_mapping.py"], check=True)
    print("json_mapping.py executed successfully.")

dotenv.load_dotenv()
# Check for correct number of arguments
if len(sys.argv) != 7:
    print("Usage: python main.py <input_docx> <output_json> <word_template_1> <word_template_2> <word_template_3> <output_docx>")
    sys.exit(1)

# Extract command-line arguments
input_docx = sys.argv[1]
output_json = sys.argv[2]
word_template_1 = sys.argv[3]
word_template_2 = sys.argv[4]
word_template_3 = sys.argv[5]
output_directory = sys.argv[6]

# List of templates for easier iteration
word_templates = [word_template_1, word_template_2, word_template_3]

# Get the directory of the input file to save the output files in the same directory
input_directory = os.path.dirname(input_docx)

# Step 1: Execute document_parser.py
execute_document_parser(input_docx, output_json)

# Load the JSON file into a Python variable
with open(output_json, 'r', encoding="utf-8") as file:
    data = json.load(file)

def check_and_save_json(response, output_filename, agent_name):
    """
    This function checks the chat history in the response object,
    attempts to find and parse JSON content, and saves it to a file.
    The function is dynamic and works with any agent by specifying the agent's name.
    """
    if response and hasattr(response, 'chat_history') and response.chat_history:
        # Loop through the chat history to find the correct entry
        for entry in response.chat_history:
            if entry['role'] == 'user' and entry['name'] == agent_name:
                generated_json_content = entry.get('content', '').strip()

                if generated_json_content:
                    try:
                        # Attempt to parse the JSON content
                        parsed_content = json.loads(generated_json_content)
                        
                        # Save the parsed JSON content to a file
                        with open(output_filename, 'w') as json_file:
                            json.dump(parsed_content, json_file, indent=4)
                        print(f"Generated JSON content from '{agent_name}' has been saved to '{output_filename}'.")
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode JSON from '{agent_name}': {e}")
                else:
                    print(f"No content found in the relevant chat history entry from '{agent_name}'.")
    else:
        print(f"Unexpected response structure or empty chat history for agent '{agent_name}'.")


# Load API key from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Manually create the config list with JSON response format
config_list = [
    {
        "model": "gpt-4o-mini",
        "api_key": OPENAI_API_KEY,
        "response_format": {"type": "json_object"},
    }
]

llm_config = {
    "temperature": 0.5,
    "config_list": config_list,
    "timeout": 120,  # in seconds
}

course_info_extractor = AssistantAgent(
    name="course_info_extractor",
    llm_config=llm_config,
    system_message="""
    You are an assistant tasked with extracting specific information from the provided data. 
    You must return the information in a JSON structure.
    """,
)

user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config={
        "work_dir": "cwgen_output",
        "use_docker": False
    },
)

# Define the agents
analyst = AssistantAgent(
    name="Background_Analyst",
    llm_config=llm_config,
    system_message="""
    You are a courseware consultant designed to help users assess the relevance and potential impact of courses tailored for specific industries. Your goal is to determine how well a course addresses performance gaps within the industry.
    """,
)

# Define the agents
editor = AssistantAgent(
    name="editor",
    llm_config=llm_config,
    system_message="""
    You are an administrative JSON editor, designed to combine outputs from 2 different agents into 1 JSON file for further processing.
    """,
)

# insert extraction pipeline here
course_info_extractor_message = f"""
You are to extract the following variables from {data}, ensure that ALL needed data is extracted:
    1) Title
    2) TSC Title
    3) TSC Code
    Use the term_library below for "Industry", based on the front 3 letters of the TSC code:
    term_library = {{
        'ACC': 'Accountancy',
        'RET': 'Retail',
        'MED': 'Media',
        'ICT': 'Infocomm Technology',
        'BEV': 'Built Environment',
        'DSN': 'Design',
        'DNS': 'Design',
        'AGR': 'Agriculture',
        'ELE': 'Electronics',
        'LOG': 'Logistics',
        'STP': 'Sea Transport',
        'TOU': 'Tourism',
        'AER': 'Aerospace',
        'ATP': 'Air Transport',
        'BPM': 'BioPharmaceuticals Manufacturing',
        'ECM': 'Energy and Chemicals',
        'EGS': 'Engineering Services',
        'EPW': 'Energy and Power',
        'EVS': 'Environmental Services',
        'FMF': 'Food Manufacturing',
        'FSE': 'Financial Services',
        'FSS': 'Food Services',
        'HAS': 'Hotel and Accommodation Services',
        'HCE': 'Healthcare',
        'HRS': 'Human Resource',
        'INP': 'Intellectual Property',
        'LNS': 'Landscape',
        'MAR': 'Marine and Offshore',
        'PRE': 'Precision Engineering',
        'PTP': 'Public Transport',
        'SEC': 'Security',
        'SSC': 'Social Service',
        'TAE': 'Training and Adult Education',
        'WPH': 'Workplace Safety and Health',
        'WST': 'Wholesale Trade',
        'ECC': 'Early Childhood Care and Education',
        'ART': 'Arts'
    }}


    4) Industry
    5) Learning Outcomes, include the terms LO(x): in front of each learning outcome

    An example output is as follows:
    "TSC Title": ["Financial Analysis"],
    "TSC Code": ["ACC-MAC-3004-1.1"],
    "Learning Outcomes":  ["LO1: Calculate profitability ratios to assess an organization's financial health.", "LO2: Calculate performance ratios to evaluate an organization's overall financial performance."]

    Do not add in "TOU -" in front of the TSC Title.
    Ensure that the front 3 letters of the TSC code matches the term library's values accordingly.

    Format the extracted data in JSON format, with this structure, do NOT change the key names or add unnecessary spaces:
    "Course Title": "",
    "Industry": "",
    "TSC Title": "",
    "TSC Code": "",
    "Learning Outcomes": ""
    }}
"""

# insert research analysts
analyst_message = f"""
Using the following information:
1. Course title (e.g., "Data Analytics for Business")
2. Industry: 'HAS': 'Hotel and Accommodation Services',
3. Learning outcomes expected from the course (e.g., "Better decision-making using data, automation of business reports")

Generate 3 distinct sets of answers to two specific survey questions.
Survey Questions and Structure:

{{
Question 1: What are the performance gaps in the industry?
Question 1 Guidelines: You are to provide a short description (1-2 paragraphs) of what the key performance issues are within the specified industry. This will be based on general industry knowledge, considering the context of the course.

Question 2: Why you think this WSQ course will address the training needs for the industry?
Question 2 Guidelines: You are to explain in a short paragraph (1-2 paragraphs) how the course you mentioned can help address those performance gaps in the industry. Each response will be tied to one or two of the learning outcomes you provided, without directly mentioning them.

}}

Rules for Each Response:
Distinct Answers: You will provide three different answers by focusing on different learning outcomes in each response.
Concise Structure: Each response will have no more than two paragraphs, with each paragraph containing fewer than 120 words.

No Mention of Certain Elements:
You won't mention the specific industry in the response.
You won't mention or restate the learning outcomes explicitly.
You won't indicate that I am acting in a director role.

You are to output your response in this JSON format, do not change the keys:
Output Format (for each of the 3 sets):
What are the performance gaps in the industry?
[Answer here based on the industry and course details you provide]

Why do you think this WSQ course will address the training needs for the industry?
[Answer here showing how the course helps address the gaps based on relevant learning outcomes]

By following these steps, you aim to provide actionable insights that match the course content to the training needs within the specified industry.


    }}
"""

editor_message = f"""
You are to combine the outputs from the following agents into a single JSON object, do NOT aggregate output from the validator agent:
    1) course_info_extractor
    2) analyst
Return the combined output into a single JSON file.

Follow this structure and naming convention below:
{{
    "course_info": {{
        "Course Title": "",
        "Industry": "",
        "Learning Outcomes": [
            ""
        ],
        "TSC Title": "",
        "TSC Code": ""
    }},
    "analyst_responses": [
        {{
            "What are the performance gaps in the industry?": "",
            "Why do you think this WSQ course will address the training needs for the industry?": ""
        }}
    ]
}}
"""

extraction_results = user_proxy.initiate_chats(  # noqa: F704
    [
        {
            "chat_id": 1,
            "recipient": course_info_extractor,
            "message": course_info_extractor_message,
            "silent": False,
            "max_turns":1,
            "summary_method": "last_msg",
        },
        {
            "chat_id": 2,
            "prerequisites": [1],
            "recipient": analyst,
            "message": analyst_message,
            "silent": False,
            "max_turns":1,
            "summary_method": "last_msg",
        },        
        {
            "chat_id": 3,
            "prerequisites": [1, 2],
            "recipient": editor,
            "message": editor_message,
            "silent": False,
            "max_turns":1,
            "summary_method": "last_msg",
        },
    ]
)

editor_response = editor.last_message()["content"]

start_index = editor_response.find('{')
end_index = editor_response.rfind('}')

if start_index != -1 and end_index != -1:
    # Extract the JSON substring
    json_string = editor_response[start_index:end_index + 1]
    print("Extracted JSON String -----------")
    print(json_string)

    # Step 3: Try parsing the JSON
    try:
        parsed_output = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        parsed_output = {}
else:
    print("No valid JSON found in the response.")
    parsed_output = {}

# Step 4: Save the parsed output to a JSON file
output_filename = 'ensemble_output.json'
try:
    with open(output_filename, 'w') as json_file:
        json.dump(parsed_output, json_file, indent=4)
    print(f"Output saved to {output_filename}")
except IOError as e:
    print(f"Error saving JSON to file: {e}")


with open('ensemble_output.json', 'r') as file:
    ensemble_output = json.load(file)

# If ensemble_output is a JSON string, parse it first
if isinstance(ensemble_output, str):
    ensemble_output = json.loads(ensemble_output)

# Load mapping template with key:empty list pair
with open('mapping_source.json', 'r') as file:
    mapping_source = json.load(file)

# Step 2: Loop through the responses and create three different output documents
responses = ensemble_output.get('analyst_responses', [])
if len(responses) < 3:
    print("Error: Less than 3 responses found in the JSON file.")
    sys.exit(1)

# Iterate over responses and templates
for i, (response, word_template) in enumerate(zip(responses[:3], word_templates), 1):
    # Check that 'course_info' is in 'data'
    course_info = ensemble_output.get("course_info")
    if not course_info:
        print(f"Error: 'course_info' is missing from the JSON data during iteration {i}.")
        sys.exit(1)

    # Create a temporary JSON file with both course_info and the current response
    temp_response_json = f"temp_response_{i}.json"
    
    # Prepare the content to write to the JSON file
    json_content = {
        "course_info": course_info,
        "analyst_responses": [response]
    }
    
    # Write to the temporary JSON file
    with open(temp_response_json, 'w', encoding="utf-8") as temp_file:
        json.dump(json_content, temp_file, indent=4)

    # Debugging: Print the contents of temp_response_json to confirm correctness
    print(f"Debug: Contents of temp_response_json ({temp_response_json}):")
    with open(temp_response_json, 'r', encoding="utf-8") as temp_file:
        print(temp_file.read())

    # Extract the name of the word template without the file extension
    template_name_without_extension = os.path.splitext(os.path.basename(word_template))[0]
    
    # Define the output file name for this response in the same directory as the input file
    output_docx_version = os.path.join(output_directory, f"{template_name_without_extension}_updated.docx")
    
    # Step 3: Call json_docu_replace.py to generate the Word document for this response using the respective template
    execute_json_docu_replace(temp_response_json, word_template, output_docx_version)

print(f"All processes completed successfully. Final documents saved in the same directory as the input file.")

