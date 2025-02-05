# agentic_LG.py
import os
import dotenv
import re
import tempfile
import streamlit as st
from autogen import UserProxyAgent, AssistantAgent
from PIL import Image
from docx.shared import Inches
from docxtpl import DocxTemplate, InlineImage

def generate_learning_guide(context, name_of_organisation, llm_config):
    """
    Generate a Learning Guide document based on the provided Course Proposal (CP) document.

    Args:
        context (dict): The structured course information.
        name_of_organisation (str): Name of the organisation (used for logos and other settings).

    Returns:
        str: Path to the generated Learning Guide document.
    """

    LG_TEMPLATE_DIR = "Courseware/input/Template/LG_TGS-Ref-No_Course-Title_v1.docx"  

    # 1. User Proxy Agent (Provides unstructured data to the interpreter)
    user_proxy = UserProxyAgent(
        name="User",
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",  # Automatically provides unstructured data
        code_execution_config={"work_dir": "output", "use_docker": False} # Takes data from a directory
    )

    # 4. Content Generator Agent
    content_generator = AssistantAgent(
        name="Content_Generator",
        llm_config=llm_config,
        system_message="""
        You are an expert in creating detailed and informative content for course descriptions. Your task is to:

        1. Generate a course overview (Learning Overview) of EXACTLY 90-100 words based on the provided Course Title. The overview MUST:
            - Start with "The `course_title` course provides..."
            - Provide a comprehensive introduction to the course content
            - Highlight multiple key concepts or skills that will be covered in all the learning units
            - Use clear and detailed language suitable for potential learners
            - Include specific examples of topics or techniques covered

        2. Generate a learning outcome description (Learning Outcome) of EXACTLY 45-50 words based on the provided Course Title. The learning outcome MUST:
            - Start with "By the end of this course, learners will be able to..."
            - Focus on at least three key skills or knowledge areas that participants will gain
            - Use specific action verbs to describe what learners will be able to do
            - Be detailed, specific, and measurable
            - Reflect the depth and complexity of the course content

        3. Return these as a dictionary with keys "Course_Overview" and "LO_Description".
            ```json
            {
                # All original dictionary keys and values remain unchanged
                ...,
                "Course_Overview": "The [Course Title] course provides...",
                "LO_Description": "By the end of this course, learners will be able to..."
            }
            ```
        Ensure that the content is tailored to the specific course title provided, reflects the depth and focus of the course, and STRICTLY adheres to the specified word counts.
        """
    )

    # 5. LG Assistant
    lg_assistant = AssistantAgent(
        name="LG_Assistant",
        system_message="""
        You are responsible for generating the Learning Guide document. Your tasks are:
        1. Receive the updated JSON dictionary containing all the course information.
        2. Use this JSON dictionary as the context for the document template.
        3. Call the `generate_document` function with the arguments: context= JSON dictionary to render and save the document.

        **Example function call:**
        ```python
        generate_document(context=json context)
        ```

        4. Return 'TERMINATE' when the task is done.
        """,
        llm_config=llm_config
    )

    @user_proxy.register_for_execution()
    @lg_assistant.register_for_llm(name="generate_document", description="Generate the Learning Guide document")
    def generate_document(context: dict) -> str:
        doc = DocxTemplate(LG_TEMPLATE_DIR)
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

    # Example task message that requests JSON output
    agent_tasks = {
        "content_generator": f"""
        Please:
        1. Take the complete dictionary provided:
        {context}
        2. Generate the Course Overview and Learning Outcome description.
        3. Add these to the existing dictionary.
        4. Return the COMPLETE updated dictionary with ALL original fields plus the new content in JSON format.
        """,
        "lg_assistant": """
        1. Use the updated JSON dictionary, which includes all the course information, to create a context for the document template.
        2. Call the `generate_document` function to render and save the document.
        3. After the function call, include the output path returned by the function in your final message, starting with `Output Path: ` followed by the path.
        4. Return 'TERMINATE' when the task is done.
        """
    }

    # Initiate conversations with llm_reflection summary method
    chat_results = user_proxy.initiate_chats(
        [
            {
                "chat_id": 1,
                "recipient": content_generator,
                "message": agent_tasks["content_generator"],
                "silent": False,
                "summary_method": "last_msg",  # Use reflection to summarize in JSON
                "max_turns": 2
            },
            {
                "chat_id": 2,
                "prerequisites": [1],
                "recipient": lg_assistant,
                "message": agent_tasks["lg_assistant"],
                "silent": False,
                "summary_method": "last_msg",
            }
        ]
    )
    print("\n\n########################### LG AUTOGEN COST #############################")
    for i, chat_res in enumerate(chat_results):
        print(f"*****{i}th chat*******:")
        print("Conversation cost: ", chat_res.cost)
    print("########################### LG AUTOGEN COST #############################\n\n")

    # Extract the output path from the last agent
    lg_output_path = None
    for chat_res in chat_results:
        # Check if "TERMINATE" is in the last message content
        last_message_content = chat_res.chat_history[-1].get("content")
        if last_message_content is not None and "TERMINATE" in last_message_content:
            for _, message in enumerate(chat_res.chat_history):
                content = message.get('content')
                if content is not None:
                    match = re.search(r'Output Path:\s*(.*\.docx)', content)
                    if match:
                        lg_output_path = match.group(1).strip()
                        break
    if lg_output_path:
        return lg_output_path
    else:
        raise Exception("Learning Guide generation failed.")
