# courseware_generation.py

from Courseware.agentic_LG import generate_learning_guide
from Courseware.agentic_AP import generate_assessment_plan
from Courseware.agentic_FG import generate_facilitators_guide
from Courseware.agentic_LP import generate_lesson_plan
from Courseware.timetable_generator import generate_timetable
from datetime import datetime
from autogen import UserProxyAgent, AssistantAgent
from bs4 import BeautifulSoup
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
from selenium import webdriver

import os
import dotenv
import requests
import json
import re
import streamlit as st
import urllib.parse
import time


# Initialize session state variables
if 'processing_done' not in st.session_state:
    st.session_state['processing_done'] = False
if 'lg_output' not in st.session_state:
    st.session_state['lg_output'] = None
if 'ap_output' not in st.session_state:
    st.session_state['ap_output'] = None
if 'lp_output' not in st.session_state:
    st.session_state['lp_output'] = None
if 'fg_output' not in st.session_state:
    st.session_state['fg_output'] = None
if 'context' not in st.session_state:
    st.session_state['context'] = None

# Function to save uploaded files
def save_uploaded_file(uploaded_file, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Step 1: Parse the CP document
def parse_cp_document(input_dir):
    # Load the document
    doc = Document(input_dir)

    # Initialize containers
    data = {
        "Course_Proposal_Form": {}
    }

    # Function to parse tables with advanced duplication check
    def parse_table(table):
        rows = []
        for row in table.rows:
            # Process each cell and ensure unique content within the row
            cells = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text not in cells:
                    cells.append(cell_text)
            # Ensure unique rows within the table
            if cells not in rows:
                rows.append(cells)
        return rows

    # Function to add text and table content to a section
    def add_content_to_section(section_name, content):
        if section_name not in data["Course_Proposal_Form"]:
            data["Course_Proposal_Form"][section_name] = []
        # Check for duplication before adding content
        if content not in data["Course_Proposal_Form"][section_name]:
            data["Course_Proposal_Form"][section_name].append(content)

    # Variables to track the current section
    current_section = None

    # Iterate through the elements of the document
    for element in doc.element.body:
        if isinstance(element, CT_P):  # It's a paragraph
            para = Paragraph(element, doc)
            text = para.text.strip()
            if text.startswith("Part"):
                current_section = text  # Get the part name (e.g., Part 1, Part 2)
            elif text:
                add_content_to_section(current_section, text)
        elif isinstance(element, CT_Tbl):  # It's a table
            tbl = Table(element, doc)
            table_content = parse_table(tbl)
            if current_section:
                add_content_to_section(current_section, {"table": table_content})

    return data

# Web scraping function integrated directly
def web_scrape(course_title: str, name_of_org: str) -> str:
    # Format the course title for the URL
    formatted_course_title = urllib.parse.quote(course_title)
    search_url = f"https://www.myskillsfuture.gov.sg/content/portal/en/portal-search/portal-search.html?q={formatted_course_title}"
    print(search_url)

    # Set up the Selenium WebDriver (using Chrome here)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        # Load the page with Selenium
        driver.get(search_url)
        time.sleep(3)  # Wait for JavaScript to load content

        # Parse the loaded page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Locate the specific course-holder div with the class "courses-card-holder is-horizontal"
        course_holder = soup.find('div', class_='courses-card-holder is-horizontal')
        if not course_holder:
            return "No courses found in the specified format."

        # Find all relevant course cards within this container
        course_cards = course_holder.find_all('div', class_='card')

        for card in course_cards:
            # Check if the card has the necessary elements for a course listing
            provider_div = card.find('div', class_='course-provider')
            title_element = card.find('h5', class_='card-title')
            
            if provider_div and title_element:
                provider_name_element = provider_div.find('a')
                if provider_name_element:
                    provider_name = provider_name_element.get_text(strip=True)
                    # Check if this matches the given organization name
                    if name_of_org.lower() in provider_name.lower():
                        # Find the link to the course detail page
                        course_link_element = title_element.find('a')
                        if course_link_element and 'href' in course_link_element.attrs:
                            course_detail_url = "https://www.myskillsfuture.gov.sg" + course_link_element['href']
                            
                            # Request the course detail page
                            driver.get(course_detail_url)
                            time.sleep(5)  # Wait for JavaScript to load the detail page
                            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

                            # Extract TGS Ref No (Course ID)
                            tgs_ref_no_element = detail_soup.find('div', class_='course-details-header').find('small')
                            tgs_ref_no = tgs_ref_no_element.find('span').get_text(strip=True) if tgs_ref_no_element else None

                            # Extract UEN number
                            uen_element = detail_soup.find('div', class_='course-provider-info-holder').find_next('small')
                            uen_number = uen_element.find('span').get_text(strip=True) if uen_element else None

                            # Return both TGS Ref No and UEN if available
                            return {
                                "TGS_Ref_No": tgs_ref_no,
                                "UEN": uen_number
                            }
        return "TGS Ref No not found"
    finally:
        driver.quit()

def app():
    # Streamlit UI components
    st.title("Courseware Document Generator")

    # Step 1: Upload Course Proposal (CP) Document
    st.header("Step 1: Upload Course Proposal (CP) Document")
    cp_file = st.file_uploader("Upload Course Proposal (CP) Document", type=["docx"])

    # Step 2: Select Name of Organisation
    st.header("Step 2: Select Name of Organisation")

    organisations = [
        "Tertiary Infotech Pte Ltd",
        "CareTech168 LLP",  
        "Chelsea Kidz Academy Pte Ltd",
        "Firstcom Academy Pte Ltd",
        "Fleuriste Pte Ltd",
        "Genetic Computer School Pte Ltd",
        "Hai Leck Engineering Pte Ltd",
        "IES Academy Pte Ltd",
        "Info-Tech Systems Integrators Pte Ltd",
        "InnoHat Training Pte Ltd",
        "Laures Solutions Pte Ltd",
        "QE Safety Consultancy Pte Ltd",
        "OOm Pte Ltd",
        "Raffles Skills Lab International Training Centre Pte Ltd",
        "TRAINOCATE (S) Pte Ltd",
        "SOQ International Academy Pte Ltd"
    ]

    selected_org = st.selectbox("Select Name of Organisation", organisations)

    # Step 3 (Optional): Upload Updated SFW Dataset
    st.header("Step 3 (Optional): Upload Updated Skills Framework (SFw) Dataset")
    sfw_file = st.file_uploader("Upload Updated SFw Dataset (Excel File)", type=["xlsx"])
    if sfw_file:
        sfw_data_dir = save_uploaded_file(sfw_file, 'input/dataset')
        st.success(f"Updated SFw dataset saved to {sfw_data_dir}")
    else:
        sfw_data_dir = "Courseware/input/dataset/Sfw_dataset-2022-03-30 copy.xlsx"

    # Step 4: Select Document(s) to Generate using Checkboxes
    st.header("Step 4: Select Document(s) to Generate")
    generate_lg = st.checkbox("Learning Guide (LG)")
    generate_ap = st.checkbox("Assessment Plan (AP)")
    generate_lp = st.checkbox("Lesson Plan (LP)")
    generate_fg = st.checkbox("Facilitator's Guide (FG)")


    # Step 4: Generate Documents
    if st.button("Generate Documents"):
        if cp_file is not None and selected_org:
            # Save the uploaded CP file
            # cp_input_dir = save_uploaded_file(cp_file, 'input/CP')
            # st.success(f"CP document saved to {cp_input_dir}")

            # Step 1: Parse the CP document
            raw_data = parse_cp_document(cp_file)

            # Step 2: Add the current date to the raw_data
            current_datetime = datetime.now()
            current_date = current_datetime.strftime("%d %b %Y")
            year = current_datetime.year
            raw_data["Date"] = current_date
            raw_data["Year"] = year

            # Load environment variables
            dotenv.load_dotenv()

            # Load API key from environment
            # OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
            GENERATION_MODEL_NAME = st.secrets["GENERATION_MODEL"]
            REPLACEMENT_MODEL_NAME = st.secrets["REPLACEMENT_MODEL"]

            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in environment variables.")
            if not GENERATION_MODEL_NAME:
                raise ValueError("MODEL_NAME not found in environment variables.")
            if not REPLACEMENT_MODEL_NAME:
                raise ValueError("MODEL_NAME not found in environment variables.")
            
            gen_config_list = [{"model": GENERATION_MODEL_NAME,"api_key": OPENAI_API_KEY}]
            rep_config_list = [{"model": REPLACEMENT_MODEL_NAME,"api_key": OPENAI_API_KEY}]

            config_list_deepseek ={
                "config_list":[
                    {
                        "model": "deepseek/deepseek-r1",
                        "base_url": "https://openrouter.ai/api/v1",
                        "api_key": os.getenv("openrouter_api_key"),  # or omit if set in environment
                        "price": [0.00055, 0.00219],
                    },
                ],
                "cache_seed": None,  # Disable caching.
            }
            llm_config = {"config_list": gen_config_list, "timeout": 360}
            rep_config = {"config_list": rep_config_list, "timeout": 360}

            # 1. User Proxy Agent (Provides unstructured data to the interpreter)
            user_proxy = UserProxyAgent(
                name="User",
                is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
                human_input_mode="NEVER",  # Automatically provides unstructured data
                code_execution_config={"work_dir": "output", "use_docker": False} # Takes data from a directory
            )

            # 2. Interpreter Agent (Converts unstructured data into structured data)
            interpreter = AssistantAgent(
                name="Interpreter",
                llm_config=llm_config,
                system_message="""
                You are an AI assistant that helps extract specific information from a JSON object containing a Course Proposal Form (CP). Your task is to interpret the JSON data, regardless of its structure, and extract the required information accurately.

                ---
                
                **Task:** Extract the following information from the provided JSON data:

                ### Part 1: Particulars of Course

                - Name of Organisation
                - Course Title
                - TSC Title
                - TSC Code
                - Total Training Hours (calculated as the sum of Classroom Facilitation, Workplace Learning: On-the-Job (OJT), Practicum, Practical, E-learning: Synchronous and Asynchronous), formatted with units (e.g., "30 hrs", "1 hr")
                - Total Assessment Hours, formatted with units (e.g., "2 hrs")
                - Total Course Duration Hours, formatted with units (e.g., "42 hrs")

                ### Part 3: Curriculum Design

                From the Learning Units and Topics Table:

                For each Learning Unit (LU):
                - Learning Unit Title (include the "LUx: " prefix)
                - Topics Covered Under Each LU:
                - For each Topic:
                    - **Topic_Title** (include the "Topic x: " prefix and the associated K and A statements in parentheses)
                    - **Bullet_Points** (a list of bullet points under the topic)
                - Learning Outcomes (LOs) (include the "LOx: " prefix for each LO)
                - Numbering and Description for the "K" (Knowledge) Statements (as a list of dictionaries with keys "K_number" and "Description")
                - Numbering and Description for the "A" (Ability) Statements (as a list of dictionaries with keys "A_number" and "Description")
                - **Assessment_Methods** (a list of assessment method abbreviations; e.g., ["WA-SAQ", "CS"])
                - **Instructional_Methods** (a list of instructional method abbreviations or names)

                ### Part E: Details of Assessment Methods Proposed

                For each Assessment Method in the CP, extract:
                - **Assessment_Method** (always use the full term, e.g., "Written Assessment - Short Answer Questions", "Practical Performance", "Case Study", "Oral Questioning", "Role Play")
                - **Method_Abbreviation** (if provided in parentheses or generated according to the rules)
                - **Total_Delivery_Hours** (formatted with units, e.g., "1 hr")
                - **Assessor_to_Candidate_Ratio** (a list of minimum and maximum ratios, e.g., ["1:3 (Min)", "1:5 (Max)"])
                
                **Additionally, if the CP explicitly provides the following fields, extract them. Otherwise, do not include them in the final output:**
                - **Type_of_Evidence**  
                - For PP and CS assessment methods, the evidence may be provided as a dictionary where keys are LO identifiers (e.g., "LO1", "LO2", "LO3") and values are the corresponding evidence text. In that case, convert the dictionary into a list of dictionaries with keys `"LO"` and `"Evidence"`.  
                - If the evidence is already provided as a list (for example, a list of strings or a list of dictionaries), keep it as is.
                - **Manner_of_Submission** (as a list, e.g., ["Submission 1", "Submission 2"])
                - **Marking_Process** (as a list, e.g., ["Process 1", "Process 2"])
                - **Retention_Period** (formatted with units, e.g., "3 years")
                - **No_of_Role_Play_Scripts** (only if the assessment method is Role Play and this information is provided)

                ---
                
                **Instructions:**
                
                - Carefully parse the JSON data and locate the sections corresponding to each part.
                - Even if the JSON structure changes, use your understanding to find and extract the required information.
                - Ensure that the `Topic_Title` includes the "Topic x: " prefix and the associated K and A statements in parentheses exactly as they appear.
                - For Learning Outcomes (LOs), always include the "LOx: " prefix (where x is the number).
                - Present the extracted information in a structured JSON format where keys correspond exactly to the placeholders required for the Word document template.
                - Ensure all extracted information is normalized by:
                    - Replacing en dashes (–) and em dashes (—) with hyphens (-)
                    - Converting curly quotes (“ ”) to straight quotes (")
                    - Replacing other non-ASCII characters with their closest ASCII equivalents.
                - **Time fields** must include units (e.g., "40 hrs", "1 hr", "2 hrs").
                - For `Assessment_Methods`, always use the abbreviations (e.g., WA-SAQ, PP, CS, OQ, RP) as per the following rules:
                    1. Use the abbreviation provided in parentheses if available.
                    2. Otherwise, generate an abbreviation by taking the first letters of the main words (ignoring articles/prepositions) and join with hyphens.
                    3. For methods containing "Written Assessment", always prefix with "WA-".
                    4. If duplicate or multiple variations exist, use the standard abbreviation.
                - **Important:** Verify that the sum of `Total_Delivery_Hours` for all assessment methods equals the `Total_Assessment_Hours`. If individual delivery hours for assessment methods are not specified, divide the `Total_Assessment_Hours` equally among them.
                - For bullet points in each topic, ensure that the number of bullet points exactly matches those in the CP. Re-extract if discrepancies occur.
                - Do not include any extraneous information or duplicate entries.

                **Final Output Format:**

                Return a JSON dictionary object with the following structure (use double quotes for all field names and string values):

                ```json
                {
                    "Date": "...",
                    "Year": "...",
                    "Name_of_Organisation": "...",
                    "Course_Title": "...",
                    "TSC_Title": "...",
                    "TSC_Code": "...",
                    "Total_Training_Hours": "...",  // e.g., "38 hrs"
                    "Total_Assessment_Hours": "...",  // e.g., "2 hrs"
                    "Total_Course_Duration_Hours": "...",  // e.g., "40 hrs"
                    "Learning_Units": [
                        {
                            "LU_Title": "...",
                            "Topics": [
                                {
                                    "Topic_Title": "Topic x: ... (Kx, Ax)",
                                    "Bullet_Points": ["...", "..."]
                                }
                                // Additional topics
                            ],
                            "LO": "LOx: ...",
                            "K_numbering_description": [
                                {
                                    "K_number": "K1",
                                    "Description": "..."
                                }
                                // Additional K statements
                            ],
                            "A_numbering_description": [
                                {
                                    "A_number": "A1",
                                    "Description": "..."
                                }
                                // Additional A statements
                            ],
                            "Assessment_Methods": ["...", "..."],
                            "Instructional_Methods": ["...", "..."]
                        }
                        // Additional Learning Units
                    ],
                    "Assessment_Methods_Details": [
                        {
                            "Assessment_Method": "...", // Full term
                            "Method_Abbreviation": "...", // e.g., WA-SAQ, PP, CS, OQ, RP
                            "Total_Delivery_Hours": "...",  // e.g., "1 hr"
                            "Assessor_to_Candidate_Ratio": ["...", "..."],
                            "Evidence": [ 
                                // For PP and CS, if evidence is provided as a dictionary, convert it to a list of dictionaries:
                                // Example:
                                // { "LO": "LO1", "Evidence": "Candidates will create an Excel workbook..." },
                                // { "LO": "LO2", "Evidence": "Candidates will use Microsoft Word to create..." }
                                // Otherwise, if provided as a list, include it as is.
                            ],
                            "Submission": ["..."],  // Include only if present in the CP
                            "Marking_Process": ["..."],  // Include only if present in the CP
                            "Retention_Period": "...",  // Include only if present in the CP
                            "No_of_Scripts": "..."  // Include only if the method is Role Play and present in the CP
                        }
                        // Additional assessment methods
                    ]
                }
                ```

                Please ensure that the fields **Type_of_Evidence**, **Manner_of_Submission**, **Marking_Process**, **Retention_Period**, and **No_of_Role_Play_Scripts** are extracted only if they exist in the CP; otherwise, omit these keys from the final JSON output.

                TERMINATE
                """
            )
            
            agent_tasks = {
                "interpreter": f"""
                Please extract and structure the following data: {raw_data}.
                **Return the extracted information as a complete JSON dictionary containing the specified fields. Do not truncate or omit any data. Include all fields and their full content. Do not use '...' or any placeholders to replace data.**
                Simply return the JSON dictionary object directly and 'TERMINATE'.
                """
            }

            try:
                with st.spinner('Extracting Information from Course Proposal...'):
                    # Run the interpreter agent conversation
                    chat_result = user_proxy.initiate_chat(
                        interpreter,
                        message=agent_tasks["interpreter"],
                        max_turns=1  # to avoid infinite loop
                    )
                    print("\n\n########################### INTERPRETER AUTOGEN COST #############################")
                    print(chat_result.cost)
                    print("########################### INTERPRETER AUTOGEN COST #############################\n\n")
            except Exception as e:
                st.error(f"Error extracting Course Proposal: {e}")

            # Extract the final context dictionary from the agent's response
            try:
                last_message_content = chat_result.chat_history[-1].get("content", "")
                if not last_message_content:
                    st.error("No content found in the agent's last message.")
                    return
                # Clean the content to ensure it's in the expected format
                last_message_content = last_message_content.strip()
                # Extract JSON from triple backticks
                json_pattern = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)
                json_match = json_pattern.search(last_message_content)
                if json_match:
                    json_str = json_match.group(1)
                    context = json.loads(json_str)
                else:
                    # Try extracting any JSON present in the content
                    json_pattern_alt = re.compile(r'(\{.*\})', re.DOTALL)
                    json_match_alt = json_pattern_alt.search(last_message_content)
                    if json_match_alt:
                        json_str = json_match_alt.group(1)
                        context = json.loads(json_str)
                    else:
                        st.error("No JSON found in the agent's response.")
                        return
            except json.JSONDecodeError as e:
                st.error(f"Error parsing context JSON: {e}")
                return


            # After obtaining the context
            if context:
                # st.json(context)
                # Run web_scrape function to get TGS Ref No and UEN
                try:
                    with st.spinner('Retrieving TGS Ref No and UEN...'):
                        web_scrape_result = web_scrape(context['Course_Title'], context['Name_of_Organisation'])
                        if isinstance(web_scrape_result, dict):
                            # Update context with web_scrape_result
                            context.update(web_scrape_result)
                        else:   
                            st.warning(f"Web scrape result: {web_scrape_result}")
                    st.session_state['context'] = context  # Store context in session state
                except Exception as e:
                    st.error(f"Error in web scraping: {e}")
                    return

                # Generate Learning Guide
                if generate_lg:
                    try:
                        with st.spinner('Generating Learning Guide...'):
                            lg_output = generate_learning_guide(context, selected_org, llm_config)
                        st.success(f"Learning Guide generated: {lg_output}")
                        st.session_state['lg_output'] = lg_output  # Store output path in session state
           
                    except Exception as e:
                        st.error(f"Error generating Learning Guide: {e}")

                # Generate Assessment Plan
                if generate_ap:
                    try:
                        with st.spinner('Generating Assessment Plan...'):
                            ap_output = generate_assessment_plan(context, selected_org, rep_config)
                        st.success(f"Assessment Plan generated: {ap_output}")
                        st.session_state['ap_output'] = ap_output  # Store output path in session state
   
                    except Exception as e:
                        st.error(f"Error generating Assessment Plan: {e}")

                # Check if any documents require the timetable
                needs_timetable = (generate_lp or generate_fg)

                # Generate the timetable if needed and not already generated
                if needs_timetable and 'lesson_plan' not in context:
                    try:
                        with st.spinner("Generating Timetable..."):
                            hours = int(''.join(filter(str.isdigit, context["Total_Course_Duration_Hours"])))
                            num_of_days = hours / 8
                            timetable_data = generate_timetable(context, num_of_days, llm_config)
                            context['lesson_plan'] = timetable_data['lesson_plan']
                        st.session_state['context'] = context  # Update context in session state
                    except Exception as e:
                        st.error(f"Error generating timetable: {e}")
                        return  # Exit if timetable generation fails
                    
                # Now generate Lesson Plan
                if generate_lp:
                    try:
                        with st.spinner("Generating Lesson Plan..."):
                            lp_output = generate_lesson_plan(context, selected_org, rep_config)
                        st.success(f"Lesson Plan generated: {lp_output}")
                        st.session_state['lp_output'] = lp_output  # Store output path in session state
                        # Read the file and provide a download button
     
                    except Exception as e:
                        st.error(f"Error generating Lesson Plan: {e}")

                # Generate Facilitator's Guide
                if generate_fg:
                    try:
                        with st.spinner("Generating Facilitator's Guide..."):
                            fg_output = generate_facilitators_guide(context, selected_org, rep_config)
                        st.success(f"Facilitator's Guide generated: {fg_output}")
                        st.session_state['fg_output'] = fg_output  # Store output path in session state

                    except Exception as e:
                        st.error(f"Error generating Facilitator's Guide: {e}")
                
                st.session_state['processing_done'] = True  # Indicate that processing is done

            else:
                st.error("Context is empty. Cannot proceed with document generation.")
        else:
            st.error("Please upload a CP document and select a Name of Organisation.")
 
    if st.session_state.get('processing_done'):
        st.header("Download Generated Documents")

        # Ensure 'context' exists in session state
        if 'context' in st.session_state:
            context = st.session_state['context']
        else:
            st.error("Context not found in session state.")
            st.stop()  # Stops the script execution
            
        # Learning Guide
        lg_output = st.session_state.get('lg_output')
        if lg_output and os.path.exists(lg_output):
            with open(lg_output, "rb") as f:
                file_bytes = f.read()
            # Check if 'TGS_Ref_No' is in context
            if 'TGS_Ref_No' in context and context['TGS_Ref_No']:
                file_name = f"LG_{context['TGS_Ref_No']}_{context['Course_Title']}_v1.docx"
            else:
                file_name = f"LG_{context['Course_Title']}_v1.docx"
            st.download_button(
                label="Download Learning Guide",
                data=file_bytes,
                file_name=file_name,
                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        # Assessment Plan
        ap_output = st.session_state.get('ap_output')
        if ap_output and os.path.exists(ap_output):
            with open(ap_output, "rb") as f:
                file_bytes = f.read()
            # Check if 'TGS_Ref_No' is in context
            if 'TGS_Ref_No' in context and context['TGS_Ref_No']:
                file_name = f"Assessment Plan_{context['TGS_Ref_No']}_{context['Course_Title']}_v1.docx"
            else:
                file_name = f"Assessment Plan_{context['Course_Title']}_v1.docx"
            st.download_button(
                label="Download Assessment Plan",
                data=file_bytes,
                file_name=file_name,
                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        # Lesson Plan
        lp_output = st.session_state.get('lp_output')
        if lp_output and os.path.exists(lp_output):
            with open(lp_output, "rb") as f:
                file_bytes = f.read()
            # Check if 'TGS_Ref_No' is in context
            if 'TGS_Ref_No' in context and context['TGS_Ref_No']:
                file_name = f"LP_{context['TGS_Ref_No']}_{context['Course_Title']}_v1.docx"
            else:
                file_name = f"LP_{context['Course_Title']}_v1.docx"
            st.download_button(
                label="Download Lesson Plan",
                data=file_bytes,
                file_name=file_name,
                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        # Facilitator's Guide
        fg_output = st.session_state.get('fg_output')
        if fg_output and os.path.exists(fg_output):
            with open(fg_output, "rb") as f:
                file_bytes = f.read()
            # Check if 'TGS_Ref_No' is in context
            if 'TGS_Ref_No' in context and context['TGS_Ref_No']:
                file_name = f"FG_{context['TGS_Ref_No']}_{context['Course_Title']}_v1.docx"
            else:
                file_name = f"FG_{context['Course_Title']}_v1.docx"
            st.download_button(
                label="Download Facilitator's Guide",
                data=file_bytes,
                file_name=file_name,
                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )