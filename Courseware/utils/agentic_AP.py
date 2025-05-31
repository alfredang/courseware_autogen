"""
File: agentic_AP.py

===============================================================================
Assessment Plan Generation Module
===============================================================================
Description:
    This module is part of the Courseware system and is responsible for generating
    assessment documents by processing structured course data and integrating assessment
    evidence extracted via an AI agent. It extracts structured justifications for various
    assessment methods (such as CS, PP, OQ, and RP), merges these justifications into the
    course data, and then populates DOCX templates to generate both an Assessment Plan (AP)
    document and an Assessment Summary Report (ASR) document.

Main Functionalities:
    • extract_assessment_evidence(structured_data, model_client):
          Uses an AI assistant agent to extract structured assessment evidence details (e.g.,
          type of evidence, submission method, marking process, retention period, and role play
          script requirements) from course learning outcomes and topics.
    • combine_assessment_methods(structured_data, evidence_data):
          Merges the extracted assessment evidence into the existing structured course data
          under "Assessment_Methods_Details" based on method abbreviations.
    • is_evidence_extracted(context):
          Checks whether all required evidence fields (evidence, submission, marking process,
          and retention period) are already present for each assessment method.
    • generate_assessment_plan(context, name_of_organisation, sfw_dataset_dir):
          Populates an Assessment Plan DOCX template with the course and assessment evidence data,
          integrates the organization's logo, and returns the path to the generated document.
    • generate_asr_document(context, name_of_organisation):
          Populates an Assessment Summary Report DOCX template with course details and returns the
          file path of the generated document.
    • generate_assessment_documents(context, name_of_organisation, sfw_dataset_dir=None):
          Coordinates the overall process by ensuring that all assessment evidence is extracted,
          merging evidence into the structured data, and generating both the AP and ASR documents.

Dependencies:
    - Standard Libraries: tempfile, json, asyncio
    - Streamlit: For configuration and accessing API keys via st.secrets.
    - Pydantic: For modeling assessment method data.
    - Autogen AgentChat and OpenAIChatCompletionClient: For generating structured evidence using AI.
    - DocxTemplate (from docxtpl): For rendering DOCX templates.
    - Custom Helper Functions: retrieve_excel_data and process_logo_image from Courseware/utils/helper.

Usage:
    - Ensure that all necessary API keys and configurations are set in st.secrets.
    - Prepare a structured course context dictionary that includes assessment method details.
    - Call generate_assessment_documents(context, name_of_organisation, sfw_dataset_dir) to generate
      the Assessment Plan and Assessment Summary Report documents.
    - The function returns a tuple with file paths to the generated documents.

Author:
    Derrick Lim
Date:
    3 March 2025
===============================================================================
"""

import tempfile
import streamlit as st
import json
import asyncio
from pydantic import BaseModel
from typing import List, Union, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken
from docxtpl import DocxTemplate
from Courseware.utils.helper import retrieve_excel_data, process_logo_image

class AssessmentMethod(BaseModel):
    evidence: Union[str, List[str]]
    submission: Union[str, List[str]]
    marking_process: Union[str, List[str]]
    retention_period: str
    no_of_scripts: Union[str, None] = None  # Optional field for "RP"

class AssessmentMethods(BaseModel):
    PP: Optional[AssessmentMethod] = None
    CS: Optional[AssessmentMethod] = None
    RP: Optional[AssessmentMethod] = None
    OQ: Optional[AssessmentMethod] = None

class EvidenceGatheringPlan(BaseModel):
    assessment_methods: AssessmentMethods


async def extract_assessment_evidence(structured_data, model_client):   
    """
    Extracts structured assessment evidence data from course details using an AI agent.

    This function processes course learning outcomes, topics, and assessment methods 
    to generate a structured justification for assessment evidence, submission, marking process, 
    and retention periods.

    Args:
        structured_data (dict): 
            The original structured data containing course details.
        model_client: 
            An AI model client instance used to extract structured assessment evidence.

    Returns:
        dict: 
            A dictionary containing the structured assessment evidence details.

    Raises:
        json.JSONDecodeError: 
            If the AI-generated response is not valid JSON.
        Exception: 
            If the AI response is missing required fields.
    """
    
    # Build evidence extraction task
    evidence_task = f"""
    Your task is to generate the assessment evidence gathering plan based on the following course data:
    
    Course Title: {structured_data.get('Course_Title', 'N/A')}
    Assessment Methods: {structured_data.get('Assessment_Methods_Details', [])}
    
    For each assessment method, provide:
    1. Evidence type/format
    2. Submission method
    3. Marking process
    4. Retention period (typically 3-5 years)
    
    Return the data as a structured JSON with this format:
    {{
      "assessment_methods": {{
        "WA-SAQ": {{
          "Evidence": ["list of evidence types"],
          "Submission": ["submission methods"],
          "Marking_Process": ["marking steps"],
          "Retention_Period": "retention period"
        }},
        "CS": {{
          "Evidence": [
            {{ "LO": "LO1", "Evidence": "Evidence description for LO1" }},
            {{ "LO": "LO2", "Evidence": "Evidence description for LO2" }}
          ],
          "Submission": ["submission methods"],
          "Marking_Process": ["marking steps"],
          "Retention_Period": "retention period"
        }},
        // Other assessment methods as needed
      }}
    }}
    """

    # Create the assistant using the provided model client
    evidence_assistant = AssistantAgent(
        name="Evidence_Extractor",
        model_client=model_client,
        system_message="You are an expert in assessment design who creates structured evidence gathering plans."
    )

    # Process the evidence task
    response = await evidence_assistant.on_messages(
        [TextMessage(content=evidence_task, source="user")], CancellationToken()
    )
    
    # Extract JSON from the response, handling various formats
    response_content = response.chat_message.content
    
    # Try to extract JSON from markdown code blocks if present
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_content)
    
    if json_match:
        json_content = json_match.group(1)
    else:
        # If no code blocks, try the raw content
        json_content = response_content
    
    # Clean up the content - remove any TERMINATE marker or other non-JSON text
    json_content = json_content.strip()
    
    try:
        evidence_data = json.loads(json_content)
        return evidence_data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response_content}")
        # Provide a fallback structure if parsing fails
        return {
            "assessment_methods": {
                "WA-SAQ": {
                    "Evidence": ["Written responses to short answer questions"],
                    "Submission": ["Submit electronically via learning portal"],
                    "Marking_Process": ["Marked against model answers", "Minimum passing score is 70%"],
                    "Retention_Period": "3 years after course completion"
                },
                "CS": {
                    "Evidence": [
                        {"LO": "LO1", "Evidence": "Analysis of case scenario"},
                        {"LO": "LO2", "Evidence": "Proposed conflict resolution strategies"},
                        {"LO": "LO3", "Evidence": "Team conflict management plan"},
                        {"LO": "LO4", "Evidence": "Evaluation of resolution effectiveness"}
                    ],
                    "Submission": ["Submit in digital format (PDF/Word document)"],
                    "Marking_Process": ["Assessed using rubric", "Feedback provided within 7 working days"],
                    "Retention_Period": "3 years after course completion"
                }
            }
        }

def combine_assessment_methods(structured_data, evidence_data):
    """
    Merges assessment evidence details into the structured data under 'Assessment_Methods_Details'.

    This function updates the existing assessment method details in the structured data 
    with extracted evidence-related information, including evidence type, submission method, 
    marking process, and retention period.

    Args:
        structured_data (dict): 
            The original structured course data.
        evidence_data (dict): 
            The extracted assessment evidence details.

    Returns:
        dict: 
            Updated structured data with merged assessment evidence details.
    """

    # Extract evidence data for assessment methods
    evidence_methods = evidence_data.get("assessment_methods", {})

    # Iterate over Assessment_Methods_Details to integrate evidence data
    for method in structured_data.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")

        # Match the evidence data based on the abbreviation
        if method_abbr in evidence_methods:
            evidence_details = evidence_methods[method_abbr]
            
            
            if "WA-SAQ" in method_abbr:
            # Update the method with detailed evidence data
                method.update({
                    "Evidence": evidence_details.get("evidence", ""),
                    "Submission": evidence_details.get("submission", ""),
                    "Marking_Process": evidence_details.get("marking_process", ""),
                    "Retention_Period": evidence_details.get("retention_period", "")
                })

            if "PP" in method_abbr or "CS" in method_abbr or "OQ" in method_abbr:
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

AP_TEMPLATE_DIR = "Courseware/input/Template/AP_TGS-Ref-No_Course-Title_v1.docx"  
ASR_TEMPLATE_DIR = "Courseware/input/Template/ASR_TGS-Ref-No_Course-Title_v1.docx"  

# Check if assessment methods already contain necessary details
def is_evidence_extracted(context):
    """
    Checks whether all necessary assessment evidence fields are already present in the context.

    This function verifies if evidence-related fields such as "Evidence", "Submission", 
    "Marking_Process", and "Retention_Period" are available for each assessment method.

    Args:
        context (dict): 
            The course context dictionary containing assessment method details.

    Returns:
        bool: 
            True if all required fields are present, False otherwise.
    """

    for method in context.get("Assessment_Methods_Details", []):
        method_abbr = method.get("Method_Abbreviation")
        # Skip checking for WA-SAQ entirely, as it is hardcoded in the template.
        if method_abbr == "WA-SAQ":
            continue
        # For other methods, check the required keys.
        for key in ["Evidence", "Submission", "Marking_Process", "Retention_Period"]:
            # For RP, skip checking "Evidence" and "Submission"
            if method_abbr == "RP" and key in ["Evidence", "Submission"]:
                continue
            if method.get(key) is None:
                return False
    return True

def generate_assessment_plan(context: dict, name_of_organisation, sfw_dataset_dir) -> str:
    """
    Generates an Assessment Plan (AP) document by populating a DOCX template with course assessment details.

    This function retrieves assessment-related data, including structured assessment evidence, 
    inserts an organization's logo, and saves the populated Assessment Plan document.

    Args:
        context (dict): 
            The structured course data including assessment methods.
        name_of_organisation (str): 
            The name of the organization, used to retrieve and insert the corresponding logo.
        sfw_dataset_dir (str): 
            The file path to the Excel dataset containing additional course-related data.

    Returns:
        str: 
            The file path of the generated Assessment Plan document.

    Raises:
        FileNotFoundError: 
            If the template file or organization's logo file is missing.
        KeyError: 
            If required assessment details are missing.
        IOError: 
            If there are issues with reading/writing the document.
    """

    if not is_evidence_extracted(context):
        print("Extracting missing assessment evidence...")

        evidence_model_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            temperature=0.2,
            api_key=st.secrets["DEEPSEEK_API_KEY"],
            model_info={
                "family": "unknown",
                "function_calling": False,
                "json_output": False,
                "vision": False,
                "structured_output": False
            }
        )

        evidence = asyncio.run(extract_assessment_evidence(structured_data=context, model_client=evidence_model_client))
        print("Evidence")
        print(evidence)
        context = combine_assessment_methods(context, evidence)
        print("Evidence combined into context:")
        print(context)
    else:
        print("Skipping assessment evidence extraction as all required fields are already present.")

    doc = DocxTemplate(AP_TEMPLATE_DIR)

    context = retrieve_excel_data(context, sfw_dataset_dir)

    # Add the logo to the context
    context['company_logo'] = process_logo_image(doc, name_of_organisation)
    context['Name_of_Organisation'] = name_of_organisation
    doc.render(context, autoescape=True)

    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file

def generate_asr_document(context: dict, name_of_organisation) -> str:
    """
    Generates an Assessment Summary Report (ASR) document.

    This function populates an ASR DOCX template with the given course context 
    and organization's details before saving the document.

    Args:
        context (dict): 
            The structured course data used for the summary report.
        name_of_organisation (str): 
            The name of the organization, used to include the correct details in the document.

    Returns:
        str: 
            The file path of the generated Assessment Summary Report document.

    Raises:
        FileNotFoundError: 
            If the template file is missing.
        IOError: 
            If there are issues with reading/writing the document.
    """

    doc = DocxTemplate(ASR_TEMPLATE_DIR)
    context['Name_of_Organisation'] = name_of_organisation

    doc.render(context)

    # Use a temporary file to save the document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        doc.save(tmp_file.name)
        output_path = tmp_file.name  # Get the path to the temporary file

    return output_path  # Return the path to the temporary file

def generate_assessment_documents(context: dict, name_of_organisation, sfw_dataset_dir=None):
    """
    Generates both the Assessment Plan (AP) and Assessment Summary Report (ASR) documents.

    This function first ensures that assessment evidence is extracted and merged into 
    the structured course data. It then generates the corresponding DOCX files.

    Args:
        context (dict): 
            The structured course data including assessment methods.
        name_of_organisation (str): 
            The name of the organization, used for document customization.
        sfw_dataset_dir (str, optional): 
            The file path to the Excel dataset containing course-related data. 
            Defaults to a predefined dataset file.

    Returns:
        tuple:
            - `str`: File path of the generated Assessment Plan document.
            - `str`: File path of the generated Assessment Summary Report document.

    Raises:
        Exception: 
            If any issue occurs during the document generation process.
    """
    
    try:
        # Use the provided template directory or default
        if sfw_dataset_dir is None:
            sfw_dataset_dir = "Courseware/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"

        # Generate the Assessment Plan document
        ap_output_path = generate_assessment_plan(context, name_of_organisation, sfw_dataset_dir)
        # Generate the Assessment Summary Report document
        asr_output_path = generate_asr_document(context, name_of_organisation)

        return ap_output_path, asr_output_path
    except Exception as e:
        print(f"An error occurred during document generation: {e}")
        return None, None