import os
import re
import autogen
from autogen.cache import Cache
from typing import List, Dict, Optional
from pydantic import BaseModel
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
]

# Data models
class CourseTopic(BaseModel):
    title: str
    subtopics: List[str]

class CourseData(BaseModel):
    course_title: str
    course_description: List[str]
    learning_outcomes: List[str]
    tsc_title: str
    tsc_code: str
    wsq_funding: Dict[str, str]
    tgs_reference_no: str
    gst_exclusive_price: str
    gst_inclusive_price: str
    session_days: str
    duration_hrs: str
    course_details_topics: List[CourseTopic]
    course_url: str  # Added course_url to match {Course_URL}

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'tertiary-autogen-creds.json', SCOPES  # Replace with your client secrets file
            )
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def copy_template(drive_service, template_id, new_title):
    try:
        body = {'name': new_title}
        new_doc = drive_service.files().copy(
            fileId=template_id, body=body
        ).execute()
        print(f"Created document with ID: {new_doc.get('id')}")
        return new_doc.get('id')
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def find_placeholders(docs_service, document_id):
    doc = docs_service.documents().get(documentId=document_id).execute()
    placeholders = set()

    for element in doc.get('body', {}).get('content', []):
        if 'table' in element:
            # Process table rows and cells
            table = element['table']
            for row in table.get('tableRows', []):
                for cell in row.get('tableCells', []):
                    for content in cell.get('content', []):
                        if 'paragraph' in content:
                            for run in content['paragraph'].get('elements', []):
                                text_run = run.get('textRun')
                                if text_run and 'content' in text_run:
                                    matches = re.findall(r'\{(.*?)\}', text_run['content'])
                                    placeholders.update(matches)
        elif 'paragraph' in element:
            # Process regular text paragraphs
            for run in element['paragraph'].get('elements', []):
                text_run = run.get('textRun')
                if text_run and 'content' in text_run:
                    matches = re.findall(r'\{(.*?)\}', text_run['content'])
                    placeholders.update(matches)

    return placeholders


def find_text_range(docs_service, document_id, search_text):
    """
    Find the start and end indices of the given text in the document.
    """
    doc = docs_service.documents().get(documentId=document_id).execute()
    content = doc.get('body', {}).get('content', [])
    for element in content:
        if 'paragraph' in element:
            for run in element['paragraph'].get('elements', []):
                text_run = run.get('textRun')
                if text_run and 'content' in text_run:
                    text = text_run['content']
                    start_index = run.get('startIndex')
                    if search_text in text and start_index is not None:
                        start = start_index + text.index(search_text)
                        end = start + len(search_text)
                        return start, end
    return None, None

def replace_placeholders_in_doc(docs_service, document_id, replacements):
    try:
        requests = []

        for placeholder, replacement in replacements.items():
            # Replace placeholders
            requests.append({
                'replaceAllText': {
                    'containsText': {
                        'text': f'{{{placeholder}}}',
                        'matchCase': True,
                    },
                    'replaceText': replacement,
                }
            })

        # Execute batch update for replacing text
        docs_service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()

        # Add hyperlink for Course_URL
        if 'Course_URL' in replacements:
            course_url_text = replacements['Course_URL']
            start, end = find_text_range(docs_service, document_id, course_url_text)
            if start is not None and end is not None:
                hyperlink_request = {
                    'updateTextStyle': {
                        'range': {
                            'startIndex': start,
                            'endIndex': end,
                        },
                        'textStyle': {
                            'link': {
                                'url': course_url_text
                            }
                        },
                        'fields': 'link'
                    }
                }
                docs_service.documents().batchUpdate(
                    documentId=document_id, body={'requests': [hyperlink_request]}).execute()

        print(f"Replaced placeholders in document ID: {document_id}")

    except HttpError as error:
        print(f"An error occurred during placeholder replacement: {error}")


def generate_brochure(data: CourseData):
    creds = authenticate()
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Find the template document
    template_name = '(Template) WSQ - Course Title Brochure'
    query = f"name = '{template_name}' and mimeType='application/vnd.google-apps.document'"
    response = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()
    items = response.get('files', [])
    if not items:
        print("Template document not found.")
        return
    template_id = items[0]['id']
    
    # Check if a document with the same name already exists
    new_title = f"{data.course_title} Brochure"
    existing_doc_query = f"name = '{new_title}' and mimeType='application/vnd.google-apps.document' and trashed = false"
    existing_doc_response = drive_service.files().list(
        q=existing_doc_query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()
    existing_docs = existing_doc_response.get('files', [])
    
    if existing_docs:
        # If the document exists, get its fileId
        new_doc_id = existing_docs[0]['id']
        print(f"Found existing document with ID: {new_doc_id}. Overwriting...")
    else:
        # Otherwise, copy the template to create a new document
        new_doc_id = copy_template(drive_service, template_id, new_title)
    
    # Build replacements
    replacements = {}
    data_dict = data.model_dump()
    
    # Map data fields to placeholders
    mapping = {
        'Course_Title': data_dict.get('course_title', 'Not Applicable'),
        'Course_Desc': '\n\n'.join(data_dict.get('course_description', [])),
        'Learning_Outcomes': '\n'.join([lo for lo in data_dict.get('learning_outcomes', [])]),
        'TGS_Ref_No': data_dict.get('tgs_reference_no', 'Not Applicable'),
        'TSC_Title': data_dict.get('tsc_title', 'Not Applicable'),
        'TSC_Code': data_dict.get('tsc_code', 'Not Applicable'),
        'GST_Excl_Price': data_dict.get('gst_exclusive_price', 'Not Applicable'),
        'GST_Incl_Price': data_dict.get('gst_inclusive_price', 'Not Applicable'),
        'Duration_Hrs': data_dict.get('duration_hrs', 'Not Applicable'),
        'Session_Days': data_dict.get('session_days', 'Not Applicable'),
        'Course_URL': data_dict.get('course_url', 'Not Applicable'),
        'Effective_Date': data_dict.get('wsq_funding', {}).get('Effective Date', 'Not Applicable'),
        'Full_Fee': data_dict.get('wsq_funding', {}).get('Full Fee', 'Not Applicable'),
        'GST': data_dict.get('wsq_funding', {}).get('GST', 'Not Applicable'),
        'Baseline_Price': data_dict.get('wsq_funding', {}).get('Baseline', 'Not Applicable'),
        'MCES_SME_Price': data_dict.get('wsq_funding', {}).get('MCES / SME', 'Not Applicable'),
    }

    # Debugging: Print mapping keys and values
    print("Mapping for replacements:")
    for key, value in mapping.items():
        print(f"{key}: {value}")
    
    # Handle {Course_Topics} placeholder
    course_topics = data_dict.get('course_details_topics', [])
    if course_topics:
        topics_text = ''
        for topic in course_topics:
            topics_text += f"{topic['title']}\n"
            for subtopic in topic['subtopics']:
                topics_text += f"{subtopic}\n"
            topics_text += '\n'
        mapping['Course_Topics'] = topics_text.strip()
    else:
        mapping['Course_Topics'] = 'Not Applicable'

    # Add mapping to replacements
    replacements.update(mapping)
    
    # Find placeholders in the document
    placeholders = find_placeholders(docs_service, new_doc_id)
    print(f"Placeholders found in document: {placeholders}")
    
    # Prepare replacements only for placeholders found
    replacements = {k: v for k, v in replacements.items() if k in placeholders}
    print("Replacements to be made:")
    for key, value in replacements.items():
        print(f"{key}: {value}")
    
    # Replace placeholders
    replace_placeholders_in_doc(docs_service, new_doc_id, replacements)
    
    print(f"Brochure generated successfully with document ID: {new_doc_id}")
    return new_doc_id  # Return the document ID for further use

# Set up the agents
llm_config = {
    "config_list": [
        {
            'model': os.getenv("REPLACEMENT_MODEL"),
            'api_key': os.getenv("TERTIARY_INFOTECH_API_KEY"),
            'tags': ['tool'],
        },
    ],
    "timeout": 120,
}

doc_writer_agent = autogen.AssistantAgent(
    name="doc_writer",
    system_message=(
        "You are an assistant that creates brochures by filling in placeholders in a Google Docs template. "
        "Use the provided functions to perform tasks. Reply with TERMINATE when the task is completed."
    ),
    llm_config=llm_config,
)

user_proxy_agent = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": "output", "use_docker": False}
)

@user_proxy_agent.register_for_execution()
@doc_writer_agent.register_for_llm(description="Generate a brochure from CourseData.")
def generate_brochure_wrapper(data: CourseData):
    return generate_brochure(data)

def scrape_course_data(url: str) -> CourseData:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import re
    from typing import List, Dict
    import time

    driver = webdriver.Chrome()
    # Set the window size to a desktop resolution
    driver.set_window_size(1366, 768)

    # Open the course details page
    driver.get(url)

    # Scroll to the bottom to ensure all content loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # wait for content to load

    try:
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "short-description"))
        )

        # Extract Course Title
        try:
            course_title_elem = driver.find_element(By.CSS_SELECTOR, 'div.product-name h1')
            course_title = course_title_elem.text.strip()
        except:
            course_title = "Not Applicable"

        # Extract data from the "short-description" div
        short_description = driver.find_element(By.CLASS_NAME, "short-description")

        # Extract Course Description
        course_description = [p.text for p in short_description.find_elements(By.TAG_NAME, "p")[:2]]  # First 2 paragraphs

        # Extract Learning Outcomes
        learning_outcomes = []
        try:
            # Find the h2 with text 'Learning Outcomes'
            learning_outcomes_h2 = short_description.find_element(By.XPATH, ".//h2[contains(text(), 'Learning Outcomes')]")
            # Find the ul that follows it
            learning_outcomes_ul = learning_outcomes_h2.find_element(By.XPATH, "./following-sibling::ul[1]")
            # Extract the li elements
            learning_outcomes = [li.text.strip() for li in learning_outcomes_ul.find_elements(By.TAG_NAME, 'li')]
        except Exception:
            # Learning Outcomes section not found
            learning_outcomes = []

        # Extract Skills Framework (TSC Title and TSC Code)
        try:
            skills_framework_text = driver.find_element(
                By.XPATH, "//h2[contains(text(), 'Skills Framework')]/following-sibling::p"
            ).text.strip()
            # Extract TSC Title and TSC Code using regex
            match = re.search(r"guideline of\s+(.*?)\s+(\S+)\s+under", skills_framework_text)
            if match:
                tsc_title = match.group(1).strip()
                tsc_code = match.group(2).strip()
            else:
                tsc_title = "Not Applicable"
                tsc_code = "Not Applicable"
        except:
            # Skills Framework section not found
            tsc_title = "Not Applicable"
            tsc_code = "Not Applicable"

        # Extract WSQ Funding table, including Effective Date
        wsq_funding = {}
        try:
            wsq_funding_table = short_description.find_element(By.TAG_NAME, "table")
            # Extract Effective Date from the first row of the table
            first_row = wsq_funding_table.find_element(By.XPATH, ".//tr[1]")
            effective_date_text = first_row.text.strip()
            match_date = re.search(r"Effective for courses starting from\s*(.*)", effective_date_text)
            if match_date:
                wsq_funding["Effective Date"] = match_date.group(1).strip()
            else:
                wsq_funding["Effective Date"] = "Not Available"

            # Now extract the funding data
            # Headers are manually defined due to the table's complex structure
            headers = ['Full Fee', 'GST', 'Baseline', 'MCES / SME']
            # The data is in the last row of the table
            funding_rows = wsq_funding_table.find_elements(By.TAG_NAME, "tr")
            data_row = funding_rows[-1]
            data_cells = data_row.find_elements(By.TAG_NAME, "td")
            if len(data_cells) == len(headers):
                for i in range(len(headers)):
                    wsq_funding[headers[i]] = data_cells[i].text.strip()
            else:
                print("Mismatch in number of headers and data cells")
        except Exception:
            # WSQ Funding table not found
            wsq_funding = {'Effective Date': 'Not Available', 'Full Fee': 'Not Available', 'GST': 'Not Available', 'Baseline': 'Not Available', 'MCES / SME': 'Not Available'}

        # Extract Course Code (TGS Reference no.)
        try:
            sku_div = driver.find_element(By.CLASS_NAME, "sku")
            tgs_reference_no = sku_div.text.strip().replace("Course Code:", "").strip()
        except:
            tgs_reference_no = "Not Applicable"

        # Extract Course Booking (GST-exclusive and GST-inclusive prices)
        try:
            price_box = driver.find_element(By.CLASS_NAME, "price-box")
            gst_exclusive_price = price_box.find_element(By.CSS_SELECTOR, ".regular-price .price").text.strip()
            gst_inclusive_price = price_box.find_element(By.ID, "gtP").text.strip()
        except:
            gst_exclusive_price = "Not Applicable"
            gst_inclusive_price = "Not Applicable"

        # Extract Course Information (Session days, Duration hrs)
        session_days = "Not Applicable"
        duration_hrs = "Not Applicable"
        try:
            course_info_div = driver.find_element(By.CLASS_NAME, "block-related")
            course_info_list = course_info_div.find_elements(By.CSS_SELECTOR, "#bs-pav li")
            for item in course_info_list:
                text = item.text.strip().split(":")
                if len(text) == 2:
                    key = text[0].strip()
                    value = text[1].strip()
                    if key == "Session (days)":
                        session_days = value
                    elif key == "Duration (hrs)":
                        duration_hrs = value
        except:
            pass  # Keep default values

        # Extract Course Details Topics
        course_details_topics = []
        try:
            # Wait for the Course Details section to be present
            course_details_section = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[@class='tabs-panels']//h2[text()='Course Details']/following-sibling::div[@class='std']"
                    )
                )
            )

            # Find all <p><strong>Topic X: ...</strong></p> elements
            topic_elements = course_details_section.find_elements(By.XPATH, ".//p[strong]")

            for idx, p_elem in enumerate(topic_elements):
                strong_elem = p_elem.find_element(By.TAG_NAME, "strong")
                # Get the topic title using textContent
                topic_title = strong_elem.get_attribute('textContent').strip()
                # Normalize spaces
                topic_title = ' '.join(topic_title.split())

                if topic_title.startswith('Topic'):
                    # Get the following siblings
                    subtopics = []
                    next_siblings = p_elem.find_elements(By.XPATH, "following-sibling::*")
                    for elem in next_siblings:
                        if elem.tag_name == 'ul':
                            subtopics.extend([li.get_attribute('textContent').strip() for li in elem.find_elements(By.TAG_NAME, "li")])
                        elif elem.tag_name == 'p':
                            # Check if the next <p> is another topic or "Final Assessment"
                            try:
                                next_strong = elem.find_element(By.TAG_NAME, "strong")
                                next_topic_title = next_strong.get_attribute('textContent').strip()
                                next_topic_title = ' '.join(next_topic_title.split())
                                if next_topic_title.startswith('Topic') or "Final Assessment" in next_topic_title:
                                    break
                            except:
                                continue
                        else:
                            continue
                    # Exclude any subtopics that contain "Assessment"
                    subtopics = [st for st in subtopics if "Assessment" not in st]
                    course_topic = CourseTopic(
                        title=topic_title,
                        subtopics=subtopics
                    )
                    course_details_topics.append(course_topic)
                else:
                    continue  # Skip if not a topic title
        except Exception as e:
            print(f"Error extracting course topics: {e}")
            course_details_topics = []

        # Get course URL
        course_url = url

        # Create and return the CourseData object
        course_data = CourseData(
            course_title=course_title,
            course_description=course_description,
            learning_outcomes=learning_outcomes,
            tsc_title=tsc_title,
            tsc_code=tsc_code,
            wsq_funding=wsq_funding,
            tgs_reference_no=tgs_reference_no,
            gst_exclusive_price=gst_exclusive_price,
            gst_inclusive_price=gst_inclusive_price,
            session_days=session_days,
            duration_hrs=duration_hrs,
            course_details_topics=course_details_topics,
            course_url=course_url
        )

        return course_data

    finally:
        driver.quit()

def main():
    course_url = "https://www.tertiarycourses.com.sg/wsq-mastering-the-art-science-of-working-with-people-teams-using-discasiaplus.html"
    
    # Assuming we have a function scrape_course_data(url) -> CourseData
    # Let's use the same CourseData class as above
    # We'll simulate the scraping agent and get the data

    # For simplicity, we'll directly call the scrape_course_data function here
    # Ensure that scrape_course_data is imported or defined in the script
    
    # Scrape the course data
    course_data = scrape_course_data(course_url)

    # Now, we can pass this course_data to the doc_writer_agent via the conversation

    with Cache.disk() as cache:
        res = user_proxy_agent.initiate_chat(
            doc_writer_agent,
            message=f"Please generate a brochure using the following course data: {course_data.json()}",
            summary_method="reflection_with_llm",
            cache=cache,
        )

    # The agent will use the generate_brochure function to create the brochure
    # The output document ID can be included in the agent's final response

    # Print the final output
    print("Agent's Response:")
    print(res.summary)

if __name__ == '__main__':
    main()
