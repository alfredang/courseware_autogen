# agentic_FG.py
import os
import dotenv
import re
import tempfile
import streamlit as st
from autogen import UserProxyAgent, AssistantAgent
import pandas as pd
import json
from PIL import Image
from docx.shared import Inches
from docxtpl import DocxTemplate, InlineImage

def generate_facilitators_guide(context, name_of_organisation, llm_config, sfw_dataset_dir=None):
    """
    Generate a Facilitator's Guide document based on the provided Course Proposal (CP) document.

    Args:
        context (dict): The structured course information.
        name_of_organisation (str): Name of the organisation (used for logos and other settings).
        sfw_dataset_dir (str, optional): Path to the SFW Excel dataset.
            If None, a default template path will be used.

    Returns:
        str: Path to the generated Facilitataor's Guide document.
    """

    FG_TEMPLATE_DIR = "Courseware/input/Template/FG_TGS-Ref-No_Course-Title_v1.docx"  

    # Ensure 'lesson_plan' exists in context
    if 'lesson_plan' not in context:
        raise ValueError("Lesson plan not found in context. Ensure it is generated before calling this function.")

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
        1. Extract the TSC_Code from the provided course information JSON dictionary.
        2. Call the `retrieve_excel_data` function with only the TSC_Code to get the relevant data.
        3. Add the retrieved data (TSC_Sector, TSC_Sector_Abbr, TSC_Category, Proficiency_Level, Proficiency_Description) to the original JSON dictionary.
        4. **Return the updated dictionary with all original information plus the new Excel data. Do not truncate or omit any parts of the data. Include all fields and data in full. Do not replace any content with '...' or '[ ... ]'.**
        Include the word 'json' in your response.
        """
    )
    
    # FG Template Agent
    fg_assistant = AssistantAgent(
        name="FG_Template_Agent",
        system_message="""
            You are responsible for generating the FG document using the collected data.
            
            **Key Responsibilities:**
            1. **Document Generation:**
                - **Receive the updated dictionary containing all the course information.**
                - **Receive the timetable dictionary (lesson_plan).**
                - **Combine the course information dictionary and the timetable dictionary into one final context dictionary.**
                - **Include the timetable dictionary under the key 'lesson_plan' within the context dictionary.**
                - **Ensure that the 'lesson_plan' is included inside the 'context' dictionary as a key.**
                - **Call the `generate_document` function using only the `context` arguments. Do not pass any additional arguments.**
                - **Verify the document was actually generated successfully.**
                - **If generation fails, retry once with corrected parameters.**

            **Important Notes:**
            - **When combining dictionaries, make sure all necessary data is included in the `context` dictionary.**
            - **Do not pass 'lesson_plan' or any other data as separate keyword arguments to `generate_document`.**

            **Example function call:**
            ```python
            generate_document(context=context_dict)
            ```

            **Do not proceed until you have confirmed successful document generation.**
        """,
        llm_config=llm_config,
    )

    # Function to retrieve data from Excel file
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
    @fg_assistant.register_for_llm(name="generate_document", description="Generate the Facilitator Guide document")
    def generate_document(context: dict) -> str:
        doc = DocxTemplate(FG_TEMPLATE_DIR)
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
        1. Take the complete JSON dictionary provided:
        {context}
        2. Extract the TSC_Code from the provided course information JSON dictionary.
        3. Call the `retrieve_excel_data` function with only the TSC_Code to get the relevant data.
        4. Add the retrieved data (TSC_Sector, TSC_Sector_Abbr, TSC_Category, Proficiency_Level, Proficiency_Description) to the original JSON dictionary.
        5. **Return the updated dictionary with all original information plus the new Excel data. Do not truncate or omit any parts of the data. Include all fields and data in full. Do not replace any content with '...' or '[ ... ]'.**
        Include the word 'json' in your response.
        """,
        "fg_assistant": f"""
        1. You have received the course information JSON dictionary and the timetable JSON dictionary.
        2. Call the `generate_document` function with the arguments: context=final_context_dictionary.
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
                "recipient": fg_assistant,
                "message": agent_tasks["fg_assistant"],
                "silent": False,
                "summary_method": "last_msg",
                "max_turns": 2

            }
        ]
    )
    print("\n\n########################### FG AUTOGEN COST #############################")
    for i, chat_res in enumerate(chat_results):
        print(f"*****{i}th chat*******:")
        print("Conversation cost: ", chat_res.cost)
    print("########################### FG AUTOGEN COST #############################\n\n")

    fg_output_path = None
    for chat_res in chat_results:
        # Check if "TERMINATE" is in the last message content
        last_message_content = chat_res.chat_history[-1].get("content")
        if last_message_content is not None and "TERMINATE" in last_message_content:
            for _, message in enumerate(chat_res.chat_history):
                content = message.get('content')
                if content is not None:
                    match = re.search(r'Output Path:\s*(.*\.docx)', content)
                    if match:
                        fg_output_path = match.group(1).strip()
                        break

    # Check if we successfully extracted both pieces of information
    if fg_output_path:
        return fg_output_path
    else:
        raise Exception("Facilitator's Guide generation failed.")


# import dotenv
# # Load environment variables
# dotenv.load_dotenv()

# # Load API key from environment
# # OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
# GENERATION_MODEL_NAME = st.secrets["GENERATION_MODEL"]
# REPLACEMENT_MODEL_NAME = st.secrets["REPLACEMENT_MODEL"]

# if not OPENAI_API_KEY:
#     raise ValueError("OPENAI_API_KEY not found in environment variables.")
# if not GENERATION_MODEL_NAME:
#     raise ValueError("MODEL_NAME not found in environment variables.")
# if not REPLACEMENT_MODEL_NAME:
#     raise ValueError("MODEL_NAME not found in environment variables.")

# gen_config_list = [{"model": GENERATION_MODEL_NAME,"api_key": OPENAI_API_KEY}]
# rep_config_list = [{"model": REPLACEMENT_MODEL_NAME,"api_key": OPENAI_API_KEY}]

# def generate_document(context: dict, name_of_organisation, FG_TEMPLATE_DIR) -> str:
#     doc = DocxTemplate(FG_TEMPLATE_DIR)
#     logo_filename = name_of_organisation.lower().replace(" ", "_") + ".jpg"
#     logo_path = f"Courseware/utils/logo/{logo_filename}"

#     if not os.path.exists(logo_path):
#         raise FileNotFoundError(f"Logo file not found for organisation: {name_of_organisation}")

#     # Open the logo image to get its dimensions
#     image = Image.open(logo_path)
#     width_px, height_px = image.size  # Get width and height in pixels
    
#     # Define maximum dimensions (in inches)
#     max_width_inch = 7  # Adjust as needed
#     max_height_inch = 2.5  # Adjust as needed

#     # Get DPI and calculate current dimensions in inches
#     dpi = image.info.get('dpi', (96, 96))  # Default to 96 DPI if not specified
#     width_inch = width_px / dpi[0]
#     height_inch = height_px / dpi[1]

#     # Scale dimensions if they exceed the maximum
#     width_ratio = max_width_inch / width_inch if width_inch > max_width_inch else 1
#     height_ratio = max_height_inch / height_inch if height_inch > max_height_inch else 1
#     scaling_factor = min(width_ratio, height_ratio)

#     # Apply scaling
#     width_docx = Inches(width_inch * scaling_factor)
#     height_docx = Inches(height_inch * scaling_factor)

#     # Create an InlineImage object with the desired dimensions
#     logo_image = InlineImage(doc, logo_path, width=width_docx, height=height_docx)

#     # Add the logo to the context
#     context['company_logo'] = logo_image

#     doc.render(context)
#     # Use a temporary file to save the document
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
#         doc.save(tmp_file.name)
#         output_path = tmp_file.name  # Get the path to the temporary file

#     return output_path  # Return the path to the temporary file

# llm_config = {"config_list": rep_config_list, "timeout": 360}
# selected_org = "Tertiary Infotech Pte Ltd"
# context = {

#     "Date": "22 Dec 2024",

#     "Year": "2024",

#     "Name_of_Organisation": "Tertiary Infotech Pte. Ltd.",

#     "Course_Title": "AI Digital Human Application for Education, Customer Service and Presentation",

#     "TSC_Title": "Artificial Intelligence Application",

#     "TSC_Code": "AER-TEM-4026-1.1",

#     "Total_Training_Hours": "14 hrs",

#     "Total_Assessment_Hours": "2 hrs",

#     "Total_Course_Duration_Hours": "16 hrs",

#     "Learning_Units": [

#         {

#             "LU_Title": "LU1: Introduction to AI Digital Humans for Business and Education",

#             "Topics": [

#                 {

#                     "Topic_Title": "Topic 1: Introduction to AI Digital Humans for Business and Education (K1, K6, A3, A5)",

#                     "Bullet_Points": [

#                         "Overview of AI digital human technology",

#                         "Strength and limitations of using AI digital human technology",

#                         "Industry use cases of using AI digital human technology",

#                         "Tailoring AI digital humans for sector-specific needs.",

#                         "Designing an AI digital human on various AI platforms"

#                     ]

#                 }

#             ],

#             "LO": "LO1: Analyze the strengths, limitations, and feasibility of AI digital human technology within industry contexts.",

#             "K_numbering_description": [

#                 {

#                     "K_number": "K1",

#                     "Description": "Range of AI applications"

#                 },

#                 {

#                     "K_number": "K6",

#                     "Description": "Applicability of AI in the industry"

#                 }

#             ],

#             "A_numbering_description": [

#                 {

#                     "A_number": "A3",

#                     "Description": "Identify strengths and limitations of the AI applications"

#                 },

#                 {

#                     "A_number": "A5",

#                     "Description": "Assess feasibility of AI applications to the engineering processes"

#                 }

#             ],

#             "Assessment_Methods": [

#                 "WA-SAQ",

#                 "CS"

#             ],

#             "Instructional_Methods": [

#                 "Lecture",

#                 "Peer Sharing",

#                 "Group Discussion",

#                 "Case study"

#             ]

#         },

#         {

#             "LU_Title": "LU2: Analyze AI Digital Humans for Various Use Cases",

#             "Topics": [

#                 {

#                     "Topic_Title": "Topic 2: Analyze AI Digital Humans for Various Use Cases (K2, K3, A1, A4)",

#                     "Bullet_Points": [

#                         "Core principles of AI algorithm design tailored for educational and business use cases.",

#                         "Analyzing AI digital humans for diverse educational and business use cases – strength and limitations",

#                         "Case studies: Efficiency improvement using AI digital humans."

#                     ]

#                 }

#             ],

#             "LO": "LO2: Evaluate the performance of AI digital human applications and analyze their effectiveness.",

#             "K_numbering_description": [

#                 {

#                     "K_number": "K2",

#                     "Description": "Concepts pertaining to performance effectiveness and analysis"

#                 },

#                 {

#                     "K_number": "K3",

#                     "Description": "Methods of evaluating effectiveness of AI applications"

#                 }

#             ],

#             "A_numbering_description": [

#                 {

#                     "A_number": "A1",

#                     "Description": "Analyse algorithms in the AI applications"

#                 },

#                 {

#                     "A_number": "A4",

#                     "Description": "Evaluate various AI applications to compare strengths and limitations of the AI applications"

#                 }

#             ],

#             "Assessment_Methods": [

#                 "WA-SAQ",

#                 "CS"

#             ],

#             "Instructional_Methods": [

#                 "Lecture",

#                 "Peer Sharing",

#                 "Group Discussion",

#                 "Case study"

#             ]

#         },

#         {

#             "LU_Title": "LU3: Designing and Implementing AI Digital Humans",

#             "Topics": [

#                 {

#                     "Topic_Title": "Topic 3: Designing and Implementing AI Digital Humans (K4, K5, A2, A6)",

#                     "Bullet_Points": [

#                         "Enhancing AI digital humans’ capabilities",

#                         "The efficiency-accuracy tradeoff in AI digital humans’ algorithms.",

#                         "Balancing automation with human-centric values.",

#                         "Ensuring ethical AI practices using AI digital humans."

#                     ]

#                 }

#             ],

#             "LO": "LO3: Assess the design and improvements for AI digital human technology.",

#             "K_numbering_description": [

#                 {

#                     "K_number": "K4",

#                     "Description": "Algorithm design and implementation"

#                 },

#                 {

#                     "K_number": "K5",

#                     "Description": "Methods of evaluating process improvements to the engineering processes using AI"

#                 }

#             ],

#             "A_numbering_description": [

#                 {

#                     "A_number": "A2",

#                     "Description": "Establish the correlation between design of algorithms and efficiency"

#                 },

#                 {

#                     "A_number": "A6",

#                     "Description": "Assess improvements on the engineering and maintenance processes"

#                 }

#             ],

#             "Assessment_Methods": [

#                 "WA-SAQ",

#                 "CS"

#             ],

#             "Instructional_Methods": [

#                 "Lecture",

#                 "Peer Sharing",

#                 "Group Discussion",

#                 "Case study"

#             ]

#         }

#     ],

#     "Assessment_Methods_Details": [

#         {

#             "Assessment_Method": "Written Assessment - Short-Answer Questions (WA-SAQ)",

#             "Method_Abbreviation": "WA-SAQ",

#             "Total_Delivery_Hours": "1 hr",

#             "Assessor_to_Candidate_Ratio": [

#                 "1:3 (Min)",

#                 "1:20 (Max)"

#             ]

#         },

#         {

#             "Assessment_Method": "Case Study (CS)",

#             "Method_Abbreviation": "CS",

#             "Total_Delivery_Hours": "1 hr",

#             "Assessor_to_Candidate_Ratio": [

#                 "1:3 (Min)",

#                 "1:20 (Max)"

#             ]

#         }

#     ],

#     "TGS_Ref_No": "TGS-2024052081",

#     "UEN": "201200696W",

#     "lesson_plan": [

#         {

#             "Day": "Day 1",

#             "Sessions": [

#                 {

#                     "Time": "0930hrs - 0945hrs (15 mins)",

#                     "Instructions": "Digital Attendance and Introduction to the Course\n\n- Trainer Introduction\n- Learner Introduction\n- Overview of Course Structure",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "0945hrs - 1050hrs (65 mins)",

#                     "Instructions": "Topic 1: Introduction to AI Digital Humans for Business and Education (K1, K6, A3, A5)\n\n- Overview of AI digital human technology\n- Strength and limitations of using AI digital human technology\n- Industry use cases of using AI digital human technology",

#                     "Instructional_Methods": "Lecture, Peer Sharing",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1050hrs - 1100hrs (10 mins)",

#                     "Instructions": "Morning Break",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "1100hrs - 1210hrs (70 mins)",

#                     "Instructions": "Topic 1: Introduction to AI Digital Humans for Business and Education (K1, K6, A3, A5)\n\n- Tailoring AI digital humans for sector-specific needs\n- Designing an AI digital human on various AI platforms",

#                     "Instructional_Methods": "Lecture, Group Discussion",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1210hrs - 1220hrs (10 mins)",

#                     "Instructions": "Activity: Case Study on AI digital human technology\n\nFacilitator will break the class into groups of 3 to 5 participants.\nFacilitator will explain the case study to learners.\nFacilitator will explain and demonstrate the activities to learners.\nFacilitators are encouraged to invite learners to share their own answers with the class.\nFacilitators are encouraged to share their own personal experiences to incorporate real-life scenarios.",

#                     "Instructional_Methods": "Case Study",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1220hrs - 1245hrs (25 mins)",

#                     "Instructions": "Lunch Break",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "1245hrs - 1330hrs (45 mins)",

#                     "Instructions": "Topic 2: Analyze AI Digital Humans for Various Use Cases (K2, K3, A1, A4)\n\n- Core principles of AI algorithm design tailored for educational and business use cases.\n- Analyzing AI digital humans for diverse educational and business use cases – strength and limitations",

#                     "Instructional_Methods": "Lecture, Peer Sharing",

#                     "Resources": "Slide page #, TV, Whiteboard, Wi-Fi"

#                 },

#                 {

#                     "Time": "1330hrs - 1340hrs (10 mins)",

#                     "Instructions": "Activity: Demonstration on AI algorithm design tailored for different use cases\n\nFacilitator will explain and demonstrate the activities to learners.\nFacilitators are encouraged to invite learners to share their own answers with the class.\nFacilitators are encouraged to share their own personal experiences to incorporate real-life scenarios.",

#                     "Instructional_Methods": "Demonstration, Group Discussion",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1340hrs - 1500hrs (80 mins)",

#                     "Instructions": "Topic 2: Analyze AI Digital Humans for Various Use Cases (K2, K3, A1, A4)\n\n- Case studies: Efficiency improvement using AI digital humans.",

#                     "Instructional_Methods": "Lecture, Group Discussion",

#                     "Resources": "Slide page #, TV, Whiteboard, Wi-Fi"

#                 },

#                 {

#                     "Time": "1500hrs - 1510hrs (10 mins)",

#                     "Instructions": "Afternoon Break",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "1510hrs - 1630hrs (80 mins)",

#                     "Instructions": "Topic 3: Designing and Implementing AI Digital Humans (K4, K5, A2, A6)\n\n- Enhancing AI digital humans’ capabilities\n- The efficiency-accuracy tradeoff in AI digital humans’ algorithms.\n- Balancing automation with human-centric values.\n- Ensuring ethical AI practices using AI digital humans.",

#                     "Instructional_Methods": "Lecture, Peer Sharing",

#                     "Resources": "Slide page #, TV, Whiteboard, Wi-Fi"

#                 },

#                 {

#                     "Time": "1630hrs - 1640hrs (10 mins)",

#                     "Instructions": "Activity: Demonstration on Designing and Implementing AI Digital Humans\n\nFacilitator will explain and demonstrate the activities to learners.\nFacilitators are encouraged to invite learners to share their own answers with the class.\nFacilitators are encouraged to share their own personal experiences to incorporate real-life scenarios.",

#                     "Instructional_Methods": "Demonstration, Group Discussion",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1640hrs - 1730hrs (50 mins)",

#                     "Instructions": "Recap All Contents and Close",

#                     "Instructional_Methods": "Lecture, Group Discussion",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 }

#             ]

#         },

#         {

#             "Day": "Day 2",

#             "Sessions": [

#                 {

#                     "Time": "0930hrs - 0940hrs (10 mins)",

#                     "Instructions": "Digital Attendance (AM)",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "0940hrs - 1050hrs (70 mins)",

#                     "Instructions": "Topic 3: Designing and Implementing AI Digital Humans (K4, K5, A2, A6)\n\n- Enhancing AI digital humans’ capabilities\n- Ensuring ethical AI practices using AI digital humans.",

#                     "Instructional_Methods": "Lecture, Group Discussion",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1050hrs - 1100hrs (10 mins)",

#                     "Instructions": "Morning Break",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "1100hrs - 1210hrs (70 mins)",

#                     "Instructions": "Topic 3: Designing and Implementing AI Digital Humans (K4, K5, A2, A6)\n\n- The efficiency-accuracy tradeoff in AI digital humans’ algorithms.\n- Balancing automation with human-centric values.",

#                     "Instructional_Methods": "Lecture, Peer Sharing",

#                     "Resources": "Slide page #, TV, Whiteboard, Wi-Fi"

#                 },

#                 {

#                     "Time": "1210hrs - 1220hrs (10 mins)",

#                     "Instructions": "Activity: Case Study on ethics in AI digital human implementation\n\nFacilitator will break the class into groups of 3 to 5 participants.\nFacilitator will explain the case study to learners.\nFacilitator will explain and demonstrate the activities to learners.\nFacilitators are encouraged to invite learners to share their own answers with the class.\nFacilitators are encouraged to share their own personal experiences to incorporate real-life scenarios.",

#                     "Instructional_Methods": "Case Study",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1220hrs - 1245hrs (25 mins)",

#                     "Instructions": "Lunch Break",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "1245hrs - 1330hrs (45 mins)",

#                     "Instructions": "Assessment Attendance (Last Day)",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "1330hrs - 1430hrs (60 mins)",

#                     "Instructions": "Final Assessment: Written Assessment - Short-Answer Questions (WA-SAQ)",

#                     "Instructional_Methods": "Assessment",

#                     "Resources": "Assessment Questions, Assessment Plan"

#                 },

#                 {

#                     "Time": "1430hrs - 1530hrs (60 mins)",

#                     "Instructions": "Final Assessment: Case Study (CS)",

#                     "Instructional_Methods": "Assessment",

#                     "Resources": "Assessment Questions, Assessment Plan"

#                 },

#                 {

#                     "Time": "1530hrs - 1540hrs (10 mins)",

#                     "Instructions": "Afternoon Break",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "N/A"

#                 },

#                 {

#                     "Time": "1540hrs - 1810hrs (150 mins)",

#                     "Instructions": "Recap All Contents and Close",

#                     "Instructional_Methods": "Lecture, Group Discussion",

#                     "Resources": "Slide page #, TV, Whiteboard"

#                 },

#                 {

#                     "Time": "1810hrs - 1830hrs (20 mins)",

#                     "Instructions": "Course Feedback and TRAQOM Survey",

#                     "Instructional_Methods": "N/A",

#                     "Resources": "Feedback Forms, Survey Links"

#                 }

#             ]

#         }

#     ],

#     "TSC_Sector": "Aerospace",

#     "TSC_Sector_Abbr": "AER",

#     "TSC_Category": "Technology Management",

#     "Proficiency_Level": "4",

#     "Proficiency_Description": "Evaluate the effectiveness and sustainability of artificial intelligence (AI) workflows for process improvements"

# }
# FG_TEMPLATE_DIR = "Courseware/input/Template/FG_TGS-Ref-No_Course-Title_v1.docx"  

# lg_output = generate_document(context, selected_org, FG_TEMPLATE_DIR=FG_TEMPLATE_DIR)

# print(lg_output)