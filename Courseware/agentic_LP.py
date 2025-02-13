# agentic_LP.py
import os
import dotenv
import re
import tempfile
import streamlit as st
from autogen import UserProxyAgent, AssistantAgent
from PIL import Image
from docx.shared import Inches
from docxtpl import DocxTemplate, InlineImage


def generate_lesson_plan(context, name_of_organisation, llm_config):
    """
    Generate a Lesson Plan document based on the provided Course Proposal (CP) document.

    Args:
        context (dict): The structured course information.
        name_of_organisation (str): Name of the organisation.

    Returns:
        str: Path to the generated Lesson Plan document.
    """

    LP_TEMPLATE_DIR = "Courseware/input/Template/LP_TGS-Ref-No_Course-Title_v1.docx" 

    # Ensure 'lesson_plan' exists in context
    if 'lesson_plan' not in context:
        raise ValueError("Lesson plan not found in context. Ensure it is generated before calling this function.")

    # 1. User Proxy Agent (Provides unstructured data to the interpreter)
    user_proxy = UserProxyAgent(
        name="User",
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",  # Automatically provides unstructured data
        code_execution_config={"work_dir": "output", "use_docker": False} # Takes data from a directory
    )

    # LP Template Agent
    lp_assistant = AssistantAgent(
        name="LP_Template_Agent",
        system_message="""
        You are responsible for generating the LP document using the collected data.
        
        **Key Responsibilities:**
        1. **Document Generation:**
            - **Receive the updated JSON dictionary containing all the course information.**
            - **Call the `generate_document` function using only the `context` arguments. Do not pass any additional arguments.**
            - **Verify the document was actually generated successfully.**
            - **If generation fails, retry once with corrected parameters.**

        **Example function call:**
        ```python
        generate_document(context=json context)
        ```

        **Do not proceed until you have confirmed successful document generation.**
        """,
        llm_config=llm_config,
    )

    @user_proxy.register_for_execution()
    @lp_assistant.register_for_llm(name="generate_document", description="Generate the Lesson Plan document")
    def generate_document(context: dict) -> str:
        doc = DocxTemplate(LP_TEMPLATE_DIR)
        
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

    agent_task = f"""
        1. Take the complete dictionary provided:
        {context}
        2. You have received the course information JSON dictionary that includes the lesson_plan data.
        3. Call the `generate_document` function with the arguments: context=final_context_dictionary.
        **Example function call:**
        ```python
        generate_document(context=json context)
        ```
        3. Ensure that you only pass 'context' as arguments.
        4. After the function call, include the output path returned by the function in your final message, starting with `Output Path: ` followed by the path.
        5. Return 'TERMINATE' when the task is done.
        """
    
    # Run the agent conversation
    chat_results = user_proxy.initiate_chat(
        recipient=lp_assistant,
        message=agent_task,
        silent=False,
        summary_method="last_msg",
        max_turns=3
    )


    print("\n\n########################### LP AUTOGEN COST #############################")
    print(chat_results.cost)
    print("########################### LP AUTOGEN COST #############################\n\n")

    # Extract the output path from the last agent
    lp_output_path = None

    # Check if "TERMINATE" is in the last message content
    last_message_content = chat_results.chat_history[-1].get("content")
    if last_message_content is not None and "TERMINATE" in last_message_content:
        for _, message in enumerate(chat_results.chat_history):
            content = message.get('content')
            if content is not None:
                match = re.search(r'Output Path:\s*(.*\.docx)', content)
                if match:
                    lp_output_path = match.group(1).strip()
                    break

    if lp_output_path:
            return lp_output_path
    else:
        raise Exception("Lesson Plan generation failed.")