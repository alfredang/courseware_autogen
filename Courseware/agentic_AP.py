# agentic_AP.py
import os
import dotenv
import re
import tempfile
import pandas as pd
import streamlit as st
import json
from autogen import UserProxyAgent, AssistantAgent
from PIL import Image
from docx.shared import Inches
from docxtpl import DocxTemplate, InlineImage

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GENERATION_MODEL_NAME = st.secrets["REPLACEMENT_MODEL"]
gen_config_list = [{"model": GENERATION_MODEL_NAME,"api_key": OPENAI_API_KEY}]
llm_config = {"config_list": gen_config_list, "timeout": 360, "cache_seed": None}

def extract_assessment_evidence(structured_data, llm_config):   
    """
    Extract structured data from the raw JSON input using an interpreter agent.

    Args:
        raw_data (dict): The raw unstructured data to be processed.
        llm_config (dict): Configuration for the language model.

    Returns:
        dict: Structured data extracted from the raw input.
    """
        # Build extracted content inline
    lines = []
    learning_units = structured_data.get("Learning_Units", [])

    for lu in learning_units:
        # LU Title
        lines.append(lu.get("LU_Title", ""))
        for topic in lu.get("Topics", []):
            # Topic Title
            lines.append(topic.get("Topic_Title", ""))
            # Bullet Points
            for bullet in topic.get("Bullet_Points", []):
                lines.append(bullet)
        lines.append("")  # Blank line after each LU block

    extracted_content = "\n".join(lines).strip()

    # 1. User Proxy Agent
    user_proxy = UserProxyAgent(
        name="User",
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",  
        max_consecutive_auto_reply=3,
        code_execution_config={"work_dir": "output", "use_docker": False}
    )

    # 2. Interpreter Agent
    evidence_assistant = AssistantAgent(
        name="Evidence Assistant",
        llm_config=llm_config,
        system_message= f"""
        Based on the following course details, you are to provide structured justifications for the selected Assessment Methods, aligning them with Learning Outcomes (LOs) and Topics.

        **Course Details:**
        - **Course Title:** {structured_data.get("Course_Title")}
        - **Learning Outcomes:**  
        {" ".join([lu['LO'] for lu in structured_data.get('Learning_Units', [])])}
        - **Topics Covered:** {extracted_content} 
        - **Assessment Methods:** {", ".join([method['Method_Abbreviation'] for method in structured_data.get('Assessment_Methods_Details', [])])}

        ---
        
        **Your Task:**
        - Generate structured justifications for all applicable assessment methods:
        - **WA-SAQ (Written Assessment - Short Answer Questions)**
        - **CS (Case Study)**
        - **PP (Practical Performance)**
        - **OQ (Oral Questioning)**
        - **RP (Role Play)**

        - For each assessment method, extract the following:
        1. **Type of Evidence**: The specific evidence candidates will submit.
        2. **Manner of Submission**: How candidates submit their work.
        3. **Marking Process**: The evaluation criteria used by assessors.
        4. **Retention Period**: The storage duration for submitted evidence.

        ---
        
        **Rules:**
        - Replace "students" with "candidates."
        - Replace "instructors" with "assessors."
        - Ensure all **LOs** are addressed.
        - **Limit word length**:
        - Bullet points: Max 30 words.
        - Marking Process: Max 6 words per evaluation.
        - **Format must be consistent**:
        - **PP and CS:** Evidence must be in a list of LOs.
        - **WA-SAQ:** Fixed format.
        - **RP:** Special handling with "No. of Role Play Scripts."
        
        ---
        
        **Structured JSON Output Example**
        
        ```json
        {{
            "assessment_methods": {{
                "PP": {{ 
                    "evidence": [
                        "LO1: Candidates will create an Excel workbook using formulas, functions, and Copilot's automation to demonstrate how Microsoft 365 tools can enhance workplace efficiency.",
                        "LO2: Candidates will use Microsoft Word to create and modify tables, automate formatting and review processes with Copilot, and submit the final document.",
                        "LO3: Candidates will develop a multimedia PowerPoint presentation with design and content enhancements assisted by Copilot."
                    ],
                    "submission": [
                        "Candidates will submit their Excel workbooks, Word documents, and PowerPoint presentations.",
                        "Annotated screenshots or documentation showing Copilot’s contributions will be included."
                    ],
                    "marking_process": [
                        "Effectiveness in Using Copilot.",
                        "Quality of Outputs.",
                        "Efficiency and Customization."
                    ],
                    "retention_period": "All submitted evidence will be retained for 3 years."
                }},
                "CS": {{
                    "evidence": [
                        "LO1: Candidates will submit a report demonstrating how they integrated design thinking methodologies and agile principles.",
                        "LO2: Candidates will conduct a problem-framing exercise using stakeholder inputs, create a persona mapping based on user insights, and submit a report.",
                        "LO3: Candidates will lead an innovation project using Agile and design thinking approaches."
                    ],
                    "submission": [
                        "Candidates will submit their case study reports electronically via the learning management system."
                    ],
                    "marking_process": [
                        "Integration of Methodologies.",
                        "Stakeholder Analysis.",
                        "Project Leadership and Tools."
                    ],
                    "retention_period": "All submitted case study reports will be retained for 3 years."
                }},
                "WA-SAQ": {{
                    "evidence": "Written responses to short-answer questions.",
                    "submission": "Candidates will generate answers and submit the hardcopy to the assessor.",
                    "marking_process": "Assessors will evaluate accuracy and comprehensiveness.",
                    "retention_period": "3 years."
                }},
                "RP": {{
                    "evidence": "Role Play",
                    "submission": [
                        "Assessor will evaluate the candidate using an observation checklist."
                    ],
                    "marking_process": [
                        "Effectiveness of sales recommendations.",
                        "Application of sales techniques.",
                        "Presentation of follow-up steps and metrics."
                    ],
                    "retention_period": "3 years.",
                    "no_of_scripts": "Minimum of two distinct role-play scripts will be prepared."
                }}
            }}
        }}
        ```

        ---
        
        **Formatting Notes:**
        - **PP and CS assessments** should include `"evidence"` as a **list** of LOs.
        - **WA-SAQ** should be hardcoded to follow the specified format.
        - **RP** must include `"no_of_scripts"` if applicable.
        
        **Ensure output follows this exact structure with no missing fields.**
        """,
    )


    evidence_task = f"""
    Your task is to generate the assessment evidence gathering plan.
    Return the data as a structured JSON dictionary string encapsulated in ```json and 'TERMINATE'.
    """
    evidence_results = user_proxy.initiate_chat(
        recipient=evidence_assistant,
        message=evidence_task,
        silent=False
    )
    print("\n\n########################### EVIDENCE AUTOGEN COST #############################")
    print(evidence_results.cost)
    print("########################### EVIDENCE AUTOGEN COST #############################\n\n")
    # Get structured data from interpreter
    try:
        last_message_content = evidence_results.chat_history[-1].get("content","")
        if not last_message_content:
            raise Exception("No content found in the agent's last message.")
    
        # Clean the content to ensure it's in the expected format
        last_message_content = last_message_content.strip()
        # Extract JSON from triple backticks
        json_pattern = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)
        json_match = json_pattern.search(last_message_content)
        if json_match:
            json_str = json_match.group(1)
            evidence_data = json.loads(json_str)
        else:
            # Try extracting any JSON present in the content
            json_pattern_alt = re.compile(r'(\{.*\})', re.DOTALL)
            json_match_alt = json_pattern_alt.search(last_message_content)
            if json_match_alt:
                json_str = json_match_alt.group(1)
                evidence_data = json.loads(json_str)
            else:
                raise Exception("No JSON found in the agent's response.")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing context JSON: {e}")

    return evidence_data

def combine_assessment_methods(structured_data, evidence_data):
    """
    Combine evidence data into structured_data under Assessment_Methods_Details.

    Args:
        structured_data (dict): The original structured data.
        evidence_data (dict): The detailed evidence data to combine.

    Returns:
        dict: Updated structured data with evidence details merged into Assessment_Methods_Details.
    """
    # Extract evidence data for assessment methods
    evidence_methods = evidence_data.get("assessment_methods", {})

    # Iterate over Assessment_Methods_Details to integrate evidence data
    for method in structured_data.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")

        # Match the evidence data based on the abbreviation
        if method_abbr in evidence_methods:
            if "OQ" in method_abbr:
                continue
            evidence_details = evidence_methods[method_abbr]
            
            
            if "WA-SAQ" in method_abbr:
            # Update the method with detailed evidence data
                method.update({
                    "Evidence": evidence_details.get("evidence", ""),
                    "Submission": evidence_details.get("submission", ""),
                    "Marking_Process": evidence_details.get("marking_process", ""),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })

            if "PP" in method_abbr or "CS" in method_abbr:
            # Update the method with detailed evidence data
                method.update({
                    "Evidence": evidence_details.get("evidence", []),
                    "Submission": evidence_details.get("submission", []),
                    "Marking_Process": evidence_details.get("marking_process", []),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })

            # Include no_of_scripts for Role Play (RP) assessment
            if method_abbr == "RP":
                method.update({
                    "Evidence": evidence_details.get("evidence", ""),
                    "Submission": evidence_details.get("submission", ""),
                    "Marking_Process": evidence_details.get("marking_process", []),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })
                method["No_of_Scripts"] = evidence_details.get("no_of_scripts", "Not specified")

    return structured_data

def generate_assessment_plan(context, name_of_organisation, llm_config, sfw_dataset_dir=None):
    """
    Generate an Assessment Plan document based on the provided Course Proposal (CP) document.

    Args:
        context (dict): The structured course information.
        name_of_organisation (str): Name of the organisation (used for logos and other settings).
        sfw_dataset_dir (str, optional): Path to the SFW Excel dataset.
            If None, a default template path will be used.

    Returns:
        str: Path to the generated Assessment Plan document.
    """

    AP_TEMPLATE_DIR = "Courseware/input/Template/AP_TGS-Ref-No_Course-Title_v1.docx"  

    # Use the provided template directory or default
    if sfw_dataset_dir is None:
        sfw_dataset_dir = "Courseware/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"

    # Check if assessment methods already contain necessary details
    def is_evidence_extracted(context):
        for method in context.get("Assessment_Methods_Details", []):
            if not all(key in method for key in ["Evidence", "Submission", "Marking_Process", "Retention_Period"]):
                return False  # Missing required fields, needs extraction
        return True  # All required fields are present

    if not is_evidence_extracted(context):
        print("Extracting missing assessment evidence...")
        evidence = extract_assessment_evidence(structured_data=context, llm_config=llm_config)
        context = combine_assessment_methods(context, evidence)
    else:
        print("Skipping assessment evidence extraction as all required fields are already present.")

    # 1. User Proxy Agent (Provides unstructured data to the interpreter)
    user_proxy = UserProxyAgent(
        name="User",
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",  # Automatically provides unstructured data
        code_execution_config={"work_dir": "output", "use_docker": False} # Takes data from a directory
    )

    # Excel Data Retrieval Agent
    excel_data_retriever = AssistantAgent(
        name="Excel_Data_Retriever",    
        llm_config=llm_config,
        system_message="""
        You are an expert in data retrieval from Excel files. Your task is to:
        1. Extract the TSC_Code from the provided course information dictionary.
        2. Use the TSC_Code to retrieve relevant data from the Excel file by calling the `retrieve_excel_data` function.
        3. Add the retrieved data to the original dictionary.
        4. If the TSC Code cannot retrieve any data, or no data is found, return the original dictionary without modifications.
        4. Return the dictionary to the next agent.
        """
    )

    ap_assistant = AssistantAgent( #    Once the template is completed, you will forward the output path of the filled up AP document to the Quality Assurance agent
        name="AP_Assistant",
        system_message="""
        You are responsible for generating the Assessment Plan document. Your tasks are:
        1. Receive the updated dictionary containing all the course information from the previous agent.
        2. Use this dictionary as the context for the document template.
        3. Call the `generate_document` function with the arguments: context=context_dictionary.
        4. Return 'TERMINATE' when the task is done.
        """,
        llm_config=llm_config
    )

    @user_proxy.register_for_execution()
    @excel_data_retriever.register_for_llm(name="retrieve_excel_data", description="Retrieve data from Excel file based on TSC Code")
    def retrieve_excel_data(tsc_code: str) -> dict:
        # Load the Excel file
        excel_data = pd.ExcelFile(sfw_dataset_dir)
        
        # Load the specific sheet named 'TSC_K&A'
        df = excel_data.parse('TSC_K&A')
        
        # Filter the DataFrame based on the TSC Code
        filtered_df = df[df['TSC Code'] == tsc_code]
        
        if not filtered_df.empty:
            row = filtered_df.iloc[0]
            
            # Return the retrieved data as a dictionary
            return {
                "TSC_Sector": str(row['Sector']),
                "TSC_Sector_Abbr": str(tsc_code.split('-')[0]),
                "TSC_Category": str(row['Category']),
                "Proficiency_Level": str(row['Proficiency Level']),
                "Proficiency_Description": str(row['Proficiency Description'])
            }
        else:
            return {"Excel_Data_Error": f"No data found for TSC Code: {tsc_code}"}

    @user_proxy.register_for_execution()
    @ap_assistant.register_for_llm(name="generate_document", description="Generate the Assessment Plan document")
    def generate_document(context: dict) -> str:
        doc = DocxTemplate(AP_TEMPLATE_DIR)

        logo_filename = name_of_organisation.lower().replace(" ", "_") + ".jpg"
        logo_path = f"Courseware/utils/logo/{logo_filename}"

        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo file not found for organisation: {name_of_organisation}")

        # Open the logo image to get its dimensions
        image = Image.open(logo_path)
        width_px, height_px = image.size  # Get width and height in pixels
        
        # Define maximum dimensions (in inches)
        max_width_inch = 7  # Adjust as needed
        max_height_inch = 2.5  # Adjust as needed

        # Get DPI and calculate current dimensions in inches
        dpi = image.info.get('dpi', (96, 96))  # Default to 96 DPI if not specified
        width_inch = width_px / dpi[0]
        height_inch = height_px / dpi[1]

        # Scale dimensions if they exceed the maximum
        width_ratio = max_width_inch / width_inch if width_inch > max_width_inch else 1
        height_ratio = max_height_inch / height_inch if height_inch > max_height_inch else 1
        scaling_factor = min(width_ratio, height_ratio)

        # Apply scaling
        width_docx = Inches(width_inch * scaling_factor)
        height_docx = Inches(height_inch * scaling_factor)

        # Create an InlineImage object with the desired dimensions
        logo_image = InlineImage(doc, logo_path, width=width_docx, height=height_docx)

        # Add the logo to the context
        context['company_logo'] = logo_image

        doc.render(context, autoescape=True)

        # Use a temporary file to save the document
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            doc.save(tmp_file.name)
            output_path = tmp_file.name  # Get the path to the temporary file

        return output_path  # Return the path to the temporary file

    agent_tasks = {
        "excel_data_retriever": f"""
        Please:
        1. Take the complete dictionary provided:
        {context}
        
        2. Extract the TSC_Code from the provided course information JSON dictionary.
        3. Call the `retrieve_excel_data` function with only the TSC_Code to get the relevant data.
        4. Add the retrieved data (TSC_Sector, TSC_Sector_Abbr, TSC_Category, Proficiency_Level, Proficiency_Description) to the original JSON dictionary.
        5. Return the updated JSON dictionary with all original information plus the new Excel data to the next agent.
        6. Include the word 'json' in your response.
        """,
        "ap_assistant": """
        1. You have received the updated course information JSON dictionary.
        1. Use the provided JSON dictionary, which includes all the course information, to create a context for the document template.
        2. Call the `generate_document` function with the arguments: context= JSON dictionary.
        **Example function call:**
        ```python
        generate_document(context=json context)
        ```
        3. Ensure that you only pass 'context' as arguments.
        4. After the function call, include the output path returned by the function in your final message, starting with `Output Path: ` followed by the path.
        5. Return 'TERMINATE' when the task is done.
        """
    }

    chat_results = user_proxy.initiate_chats(
        [
            {
                "chat_id": 1,
                "recipient": excel_data_retriever,
                "message": agent_tasks["excel_data_retriever"],
                "silent": False,
                "summary_method": "last_msg",
                "max_turns": 2
            },
            {
                "chat_id": 2,
                "prerequisites": [1],
                "recipient": ap_assistant,
                "message": agent_tasks["ap_assistant"],
                "silent": False,
                "summary_method": "last_msg",
            }
        ]
    )
    print("\n\n########################### AP AUTOGEN COST #############################")
    for i, chat_res in enumerate(chat_results):
        print(f"*****{i}th chat*******:")
        print("Conversation cost: ", chat_res.cost)
        print("\n\n")
    print("########################### AP AUTOGEN COST #############################\n\n")

    # Extract the output path from the last agent
    ap_output_path = None
    for chat_res in chat_results:
        # Check if "TERMINATE" is in the last message content
        last_message_content = chat_res.chat_history[-1].get("content")
        if last_message_content is not None and "TERMINATE" in last_message_content:
            for _, message in enumerate(chat_res.chat_history):
                content = message.get('content')
                if content is not None:
                    match = re.search(r'Output Path:\s*(.*\.docx)', content)
                    if match:
                        ap_output_path = match.group(1).strip()
                        break
    if ap_output_path:
        return ap_output_path
    else:
        raise Exception("Assessment Plan generation failed.")

# generate_assessment_plan(context=context,name_of_organisation=name_of_organisation,llm_config=llm_config)