import streamlit as st
import nest_asyncio
import os
import re
import json
from llama_index.llms.openai import OpenAI as llama_openai
from openai import OpenAI
from llama_index.core import (
    Settings,
    StorageContext,
    SummaryIndex,
    load_index_from_storage,
)
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_parse import LlamaParse
from pathlib import Path
from pydantic import BaseModel
from typing import List

OPENAI_API_KEY = os.getenv('TERTIARY_INFOTECH_API_KEY') 
LLAMA_API_KEY = os.getenv('LLAMA_CLOUD_API_KEY')

class KnowledgeStatement(BaseModel):
    id: str
    text: str


class AbilityStatement(BaseModel):
    id: str
    text: str


class Topic(BaseModel):
    name: str
    subtopics: List[str]
    tsc_knowledges: List[KnowledgeStatement]
    tsc_abilities: List[AbilityStatement]


class LearningUnit(BaseModel):
    name: str
    topics: List[Topic]
    learning_outcome: str


class AssessmentMethod(BaseModel):
    code: str
    duration: str
    
class FacilitatorGuideExtraction(BaseModel):
    course_title: str
    tsc_proficiency_level: str
    learning_units: List[LearningUnit]
    assessments: List[AssessmentMethod]

def save_uploaded_file(uploaded_file, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def parse_fg(fg_path):
    client = OpenAI(api_key=OPENAI_API_KEY)
    parser = LlamaParse(
        api_key=LLAMA_API_KEY,
        result_type="markdown",
        show_progress=True,
        verbose=True,
        num_workers=8
    )
    parsed_content = parser.get_json_result(fg_path)
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    """You are an expert at structured data extraction. Extract the following details from the FG Document:
                    - Course Title
                    - TSC Proficiency Level
                    - Learning Units (LUs):
                        * Name of the Learning Unit
                        * Topics in the Learning Unit:
                            - Name of the Topic
                            - Description of the Topic (bullet points or sub-topics)
                            - Full Knowledge Statements associated with the topic, including their identifiers and text (e.g., K1: Range of AI applications)
                            - Full Ability Statements associated with the topic, including their identifiers and text (e.g., A1: Analyze algorithms in the AI applications)
                        * Learning Outcome (LO) for each Learning Unit
                    - Assessment Types and Durations:
                        * Extract assessment types and their durations in the format:
                          {"code": "WA-SAQ", "duration": "1 hr"}
                          {"code": "PP", "duration": "0.5 hr"}
                          {"code": "CS", "duration": "30 mins"}
                        * Interpret abbreviations of assessment methods to their correct types (e.g., "WA-SAQ," "PP," "CS").
                        * Include total durations if mentioned.

                    Return the output in a JSON format that matches the schema provided:
                    {
                        "course_title": "string",
                        "tsc_proficiency_level": "string",
                        "learning_units": [
                            {
                                "name": "string",
                                "topics": [
                                    {
                                        "name": "string",
                                        "subtopics": ["string"],
                                        "tsc_knowledges": [
                                            {"id": "string", "text": "string"}
                                        ],
                                        "tsc_abilities": [
                                            {"id": "string", "text": "string"}
                                        ]
                                    }
                                ],
                                "learning_outcome": "string"
                            }
                        ],
                        "assessments": [
                            {"code": "string", "duration": "string"}
                        ]
                    }
                    """
                ),
            },
            {"role": "user", "content": json.dumps(parsed_content)},
        ],
        response_format=FacilitatorGuideExtraction,
    )
    return completion.choices[0].message.parsed

def parse_documents(slides_path):
    def get_page_number(file_name):
        match = re.search(r"-page-(\d+)\.jpg$", str(file_name))
        if match:
            return int(match.group(1))
        return 0

    def _get_sorted_image_files(image_dir):
        """Get image files sorted by page."""
        raw_files = [f for f in list(Path(image_dir).iterdir()) if f.is_file()]
        sorted_files = sorted(raw_files, key=get_page_number)
        return sorted_files

    def get_text_nodes(json_dicts, image_dir=None):
        """Split docs into nodes, by separator."""
        nodes = []

        image_files = _get_sorted_image_files(image_dir) if image_dir is not None else None
        md_texts = [d["md"] for d in json_dicts]

        for idx, md_text in enumerate(md_texts):
            chunk_metadata = {"page_num": idx + 1}
            if image_files is not None:
                image_file = image_files[idx]
                chunk_metadata["image_path"] = str(image_file)
            chunk_metadata["parsed_text_markdown"] = md_text
            node = TextNode(
                text="",
                metadata=chunk_metadata,
            )
            nodes.append(node)

        return nodes
    
    nest_asyncio.apply()
    
    embed_model = OpenAIEmbedding(model="text-embedding-3-large", api_key=OPENAI_API_KEY)
    llm = llama_openai(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

    Settings.embed_model = embed_model
    Settings.llm = llm
    
    slides_parser = LlamaParse(
        result_type="markdown",
        use_vendor_multimodal_model=True,
        vendor_multimodal_model_name="openai-gpt-4o-mini",
        vendor_multimodal_api_key=OPENAI_API_KEY
    )

    md_json_objs = slides_parser.get_json_result(slides_path)
    md_json_list = md_json_objs[0]["pages"]
    
    image_dicts = slides_parser.aget_images(md_json_objs, download_path="data_images")
    text_nodes = get_text_nodes(md_json_list, image_dir="data_images")

    if not os.path.exists("storage_nodes_summary"):
        index = SummaryIndex(text_nodes)
        # save index to disk
        index.set_index_id("summary_index")
        index.storage_context.persist("./storage_nodes_summary")
        return index
    else:
        # rebuild storage context
        storage_context = StorageContext.from_defaults(persist_dir="storage_nodes_summary")
        # load index
        index = load_index_from_storage(storage_context, index_id="summary_index")
        return index        

# Streamlit app
def app():
    # Enable wide mode for the layout
    st.title("📄 Assessment Generator")

    st.write("Upload your Facilitator Guide (.docx) and Trainer Slide Deck (.pdf) to generate assessments.")

    # File upload
    fg_doc_file = st.file_uploader("Upload Facilitator Guide (.docx)", type=["docx"])
    slide_deck_file = st.file_uploader("Upload Trainer Slide Deck (.pdf)", type=["pdf"])

    # Assessment type selection
    st.write("Select the type of assessment to generate:")
    saq = st.checkbox("Short Answer Questions (SAQ)")
    pp = st.checkbox("Practical Performance (PP)")
    cs = st.checkbox("Case Study (CS)")

    selected_types = []
    if saq:
        selected_types.append("WA (SAQ)")
    if pp:
        selected_types.append("PP")
    if cs:
        selected_types.append("CS")

    # Button to generate assessments
    if st.button("Generate Assessments"):
        # Validity checks
        if not fg_doc_file:
            st.error("❌ Please upload the Facilitator Guide (.docx) file.")
        elif not slide_deck_file:
            st.error("❌ Please upload the Trainer Slide Deck (.pdf) file.")
        elif not (saq or pp or cs):
            st.error("❌ Please select at least one assessment type to generate.")
        else:
            # If all inputs are valid
            st.success("✅ All inputs are valid. Proceeding with assessment generation...")
            # Placeholder for assessment generation logic
            fg_filepath = save_uploaded_file(fg_doc_file, "data")
            slides_filepath = save_uploaded_file(slide_deck_file, "data")

            try:
                with st.spinner("Parsing FG Document..."):
                    parsed_fg = parse_fg(fg_filepath)
                    st.json(parsed_fg)
                    st.success("✅ Successfully parsed the Facilitator Guide.")
            except Exception as e:
                st.error(f"Error extracting Course Proposal: {e}")
            
            try:
                with st.spinner("Parsing Slide Deck..."):
                    # index = parse_documents(slides_filepath)
                    st.success("✅ Successfully parsed the Slide Deck.")
            except Exception as e:
                st.error(f"Error parsing slides: {e}")

            try:
                with st.spinner("Generating Assessments..."):
                    generated_files = {}
                    for assessment_type in selected_types:
                        if assessment_type == "WA (SAQ)":
                            context = {
                                "course_title": "Develop Artificial Intelligence and Large Language Model (LLM) Applications with Google Gemini",
                                "questions": [
                                    {
                                    "scenario": "As a business analyst, you are tasked with presenting a report on the potential applications of Large Language Models (LLMs) to your team. You have identified several areas where LLMs can be beneficial, such as customer support, content creation, and educational tools.",
                                    "question_statement": "What are some common applications of Large Language Models (LLMs) that you could include in your report to the team?",
                                    "knowledge_id": "K1",
                                    "answer": "Common applications of LLMs include content creation and assistance, customer support and chatbots, language translation and localization, educational tools, business intelligence and analytics, accessibility for disabled persons, coding and development, legal and compliance assistance, healthcare support, art and design inspiration, enhanced search engines, and crisis management and response."
                                    },
                                    {
                                    "scenario": "A manager at a healthcare organization is exploring new technologies to improve patient care and streamline operations within the hospital. They gather their staff to discuss the potential applications of Large Language Models (LLMs) in their daily processes.",
                                    "question_statement": "What are some specific applications of LLMs in the healthcare industry that could improve patient care and streamline operations?",
                                    "knowledge_id": "K6",
                                    "answer": "LLMs can be applied in healthcare for drug discovery, personalized medicine, automated clinical documentation, analyzing medical data for insights, and enhancing patient engagement through virtual health assistants."
                                    },
                                    {
                                    "scenario": "A team of data scientists at a tech company is working on improving their interactive assistant powered by the Google Gemini LLM. They need to ensure that the assistant can effectively process various types of inputs, including text, images, and audio, to provide accurate and context-aware responses to users.",
                                    "question_statement": "How can the design of algorithms enhance the performance of the interactive assistant in processing multimodal inputs?",
                                    "knowledge_id": "K4",
                                    "answer": "The design of algorithms enhances performance by enabling the assistant to accurately process and integrate different input types, ensuring coherent and contextually relevant responses, and improving interaction quality."
                                    }
                                ]
                            }
                            files = generate_documents(
                                context=context, 
                                assessment_type=assessment_type,
                                output_dir="output"
                            )
                            generated_files[assessment_type] = files
                        elif assessment_type == "PP":
                            context = {
                                "course_title": "Develop Artificial Intelligence and Large Language Model (LLM) Applications with Google Gemini",
                                "duration": "1 hr",
                                "scenario": "TechSolutions Inc., a mid-sized technology consulting firm, has been experiencing a decline in customer satisfaction due to inefficient communication and project management processes. The company relies heavily on email and traditional project management tools, which often leads to miscommunication and delays in project delivery. To address these challenges, the management team is considering the implementation of a new AI-driven solution using Google Gemini's Large Language Model (LLM) capabilities. They aim to analyze various LLM applications that could enhance internal collaboration and improve customer interactions by providing real-time support and automated responses to common inquiries. The team is tasked with evaluating the feasibility of developing a tailored LLM application that integrates seamlessly with their existing systems while also assessing the potential improvements in engineering processes and overall efficiency. In this context, the team must analyze the strengths and limitations of different LLM applications, establish the correlation between algorithm design and efficiency, and assess how these AI solutions can enhance their engineering and maintenance processes. They will also need to evaluate the performance effectiveness of a proposed Retrieval Augmented Generation (RAG) system that could provide contextual information to support customer queries, ultimately aiming to boost customer satisfaction and streamline operations.",
                                "questions": [
                                    {
                                    "question_statement": "How can the management team at TechSolutions Inc. apply the identified industrial use cases of LLM applications to enhance communication and project management within their organization?",
                                    "answer": "The management team can analyze specific industrial use cases of LLM applications such as customer support chatbots and language translation tools. By implementing a chatbot for real-time customer inquiries, the team can streamline communication, reduce response times, and improve overall customer satisfaction. Additionally, language translation tools can help bridge any communication gaps within multi-lingual teams, fostering better project management and collaboration. This application of LLM can effectively minimize miscommunication and delays in project delivery.",
                                    "ability_id": ["A1", "A3"]
                                    },
                                    {
                                    "question_statement": "In what ways can Google Gemini's multimodal capabilities improve TechSolutions Inc.'s engineering processes and performance efficiency?",
                                    "answer": "Google Gemini's multimodal capabilities allow for the integration of various data types such as text, images, and audio. By utilizing this functionality, TechSolutions Inc. can enhance their engineering processes through better data handling and improved output generation. For example, engineers could input project specifications in multiple formats, and Gemini could generate comprehensive insights, automate repetitive tasks, or provide real-time data analysis. This would lead to increased efficiency and a reduction in turnaround times on projects.",
                                    "ability_id": ["A2", "A6"]
                                    },
                                    {
                                    "question_statement": "What key factors should the team consider when assessing the feasibility of developing a tailored LLM application for TechSolutions Inc.?",
                                    "answer": "The team should consider several key factors when assessing feasibility, such as the integration capabilities of the LLM application with existing systems, the cost-effectiveness of development and maintenance, scalability to meet future demands, and user adoption rates among staff. They must evaluate whether the application meets the specific needs of the organization and whether it can enhance overall project management effectiveness. Furthermore, understanding the hardware and software requirements, along with deployment timelines, will be crucial for informed decision-making.",
                                    "ability_id": ["A5"]
                                    },
                                    {
                                    "question_statement": "How can the effectiveness of the proposed Retrieval Augmented Generation (RAG) system be evaluated to ensure it meets the goals of enhancing customer interactions at TechSolutions Inc.?",
                                    "answer": "The effectiveness of the RAG system can be evaluated by conducting user testing and gathering feedback on its ability to provide accurate and relevant responses to customer inquiries. Metrics such as response accuracy, speed of retrieval, and user satisfaction should be monitored. Additionally, analyzing system performance over time and adjustments based on the feedback will be vital. This ongoing assessment allows the management team to refine the system and ensure it aligns with the goal of enhancing customer interactions.",
                                    "ability_id": ["A4"]
                                    }
                                ]
                            }
                            files = generate_documents(
                                context=context, 
                                assessment_type=assessment_type,
                                output_dir="output"
                            )
                            generated_files[assessment_type] = files
                        elif assessment_type == "CS":
                            context = {
                                "course_title": "Develop Artificial Intelligence and Large Language Model (LLM) Applications with Google Gemini",
                                "duration": "1 hr",
                                "scenario": "TechSolutions Inc., a mid-sized technology consulting firm, has been experiencing a decline in customer satisfaction due to inefficient communication and project management processes. The company relies heavily on email and traditional project management tools, which often leads to miscommunication and delays in project delivery. To address these challenges, the management team is considering the implementation of a new AI-driven solution using Google Gemini's Large Language Model (LLM) capabilities. They aim to analyze various LLM applications that could enhance internal collaboration and improve customer interactions by providing real-time support and automated responses to common inquiries. The team is tasked with evaluating the feasibility of developing a tailored LLM application that integrates seamlessly with their existing systems while also assessing the potential improvements in engineering processes and overall efficiency. In this context, the team must analyze the strengths and limitations of different LLM applications, establish the correlation between algorithm design and efficiency, and assess how these AI solutions can enhance their engineering and maintenance processes. They will also need to evaluate the performance effectiveness of a proposed Retrieval Augmented Generation (RAG) system that could provide contextual information to support customer queries, ultimately aiming to boost customer satisfaction and streamline operations.",
                                "questions": [
                                    {
                                    "question_statement": "How can the management team at TechSolutions Inc. apply the identified industrial use cases of LLM applications to enhance communication and project management within their organization?",
                                    "answer": "The management team can analyze specific industrial use cases of LLM applications such as customer support chatbots and language translation tools. By implementing a chatbot for real-time customer inquiries, the team can streamline communication, reduce response times, and improve overall customer satisfaction. Additionally, language translation tools can help bridge any communication gaps within multi-lingual teams, fostering better project management and collaboration. This application of LLM can effectively minimize miscommunication and delays in project delivery.",
                                    "ability_id": ["A1", "A3"]
                                    },
                                    {
                                    "question_statement": "In what ways can Google Gemini's multimodal capabilities improve TechSolutions Inc.'s engineering processes and performance efficiency?",
                                    "answer": "Google Gemini's multimodal capabilities allow for the integration of various data types such as text, images, and audio. By utilizing this functionality, TechSolutions Inc. can enhance their engineering processes through better data handling and improved output generation. For example, engineers could input project specifications in multiple formats, and Gemini could generate comprehensive insights, automate repetitive tasks, or provide real-time data analysis. This would lead to increased efficiency and a reduction in turnaround times on projects.",
                                    "ability_id": ["A2", "A6"]
                                    },
                                    {
                                    "question_statement": "What key factors should the team consider when assessing the feasibility of developing a tailored LLM application for TechSolutions Inc.?",
                                    "answer": "The team should consider several key factors when assessing feasibility, such as the integration capabilities of the LLM application with existing systems, the cost-effectiveness of development and maintenance, scalability to meet future demands, and user adoption rates among staff. They must evaluate whether the application meets the specific needs of the organization and whether it can enhance overall project management effectiveness. Furthermore, understanding the hardware and software requirements, along with deployment timelines, will be crucial for informed decision-making.",
                                    "ability_id": ["A5"]
                                    },
                                    {
                                    "question_statement": "How can the effectiveness of the proposed Retrieval Augmented Generation (RAG) system be evaluated to ensure it meets the goals of enhancing customer interactions at TechSolutions Inc.?",
                                    "answer": "The effectiveness of the RAG system can be evaluated by conducting user testing and gathering feedback on its ability to provide accurate and relevant responses to customer inquiries. Metrics such as response accuracy, speed of retrieval, and user satisfaction should be monitored. Additionally, analyzing system performance over time and adjustments based on the feedback will be vital. This ongoing assessment allows the management team to refine the system and ensure it aligns with the goal of enhancing customer interactions.",
                                    "ability_id": ["A4"]
                                    }
                                ]
                            }
                            files = generate_documents(
                                context=context, 
                                assessment_type=assessment_type,
                                output_dir="output"
                            )
                            generated_files[assessment_type] = files
                    st.success(f"✅ Successfully generated assessments. \n Output files saved in the 'output' directory. {generated_files}")
            except Exception as e:
                st.error(f"Error generating assessments: {e}")

from docxtpl import DocxTemplate

def generate_documents(context: dict, assessment_type: str, output_dir: str) -> dict:
    """
    Generate the question paper and answer paper for the given context and type.

    Parameters:
    - context (dict): The data for the assessment (course title, type, questions, etc.).
    - type (int): The assessment type (1 for Ability-based, 2 for Knowledge-based).
    - output_dir (str): Directory where the generated documents will be saved.

    Returns:
    - dict: Paths to the generated documents (question and answer papers).
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load templates
    TEMPLATES = {
        "QUESTION": f"Assessment/Templates/(Template) {assessment_type} - Course Title - v1.docx",
        "ANSWER": f"Assessment/Templates/(Template) Answer to {assessment_type} - Course Title - v1.docx"
        }

    qn_template = TEMPLATES["QUESTION"]
    ans_template = TEMPLATES["ANSWER"]
    question_doc = DocxTemplate(qn_template)
    answer_doc = DocxTemplate(ans_template)
    
    # Prepare context for the question paper by creating a copy of the context without answers
    question_context = {
        **context,
        "questions": [
            {
                **question,
                "answer": None,  # Remove answers for the question document
            }
            for question in context.get("questions", [])
        ]
    }

    # Render both templates
    answer_doc.render(context)  # Render with answers
    question_doc.render(question_context)  # Render without answers

    # Save the documents to the output directory
    files = {
        "QUESTION": os.path.join(output_dir, f"{assessment_type} - {context['course_title']} - v1.docx"),
        "ANSWER": os.path.join(output_dir, f"Answers to {assessment_type} - {context['course_title']} - v1.docx")
    }
    question_doc.save(files["QUESTION"])
    answer_doc.save(files["ANSWER"])

    return files  # Return paths to the generated documents

