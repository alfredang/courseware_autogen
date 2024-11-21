# agentic_AP.py
import os
import dotenv
import re
import tempfile
import pandas as pd
import streamlit as st
from autogen import UserProxyAgent, AssistantAgent
from PIL import Image
from docx.shared import Inches
from docxtpl import DocxTemplate, InlineImage

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

    sfw_dataset_dir = "Courseware/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"

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

        doc.render(context)

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
