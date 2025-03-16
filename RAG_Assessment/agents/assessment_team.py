from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
import json
import asyncio
import os
from dotenv import load_dotenv
from CourseProposal.model_configs import get_model_config
import pydantic

# use structured output for this group, perhaps a selector group chat, and then 
# have it take into account the sources
# and redo the question and answers to fit a coherent story, and then add it all back together

def research_task(ensemble_output):
    system_message=f"""
        You are an expert question-answer crafter with deep domain expertise. Your task is to generate a scenario-based question and answer pair for a given knowledge statement while strictly grounding your response in the provided retrieved content. You must not hallucinate or fabricate details.

        Guidelines:
        1. Base your response entirely on the retrieved content. If the content does not directly address the knowledge statement, do not invent new details. Instead, use minimal general context only to bridge gaps, but ensure that every key element of the final question and answer is explicitly supported by the retrieved content.
        2. Craft a realistic scenario in 2-3 sentences that reflects the context from the retrieved content while clearly addressing the given knowledge statement.
        3. Formulate one direct, simple question that ties the scenario to the knowledge statement. The question should be directly answerable using the retrieved content.
        4. Provide concise, practical bullet-point answers that list the key knowledge points explicitly mentioned in the retrieved content.         
        5. Ensure the overall assessment strictly follows the SAQ structure.
        6. Do not mention about the source of the content in the scenario or question.
        7. Structure the final output in **valid JSON** with the format:

        ```json
        {{
            "scenario": "<scenario>",
            "question_statement": "<question>",
            "knowledge_id": "<knowledge_id>",
            "answer": [
                "<bullet_point_1>",
                "<bullet_point_2>",
                "<bullet_point_3>"
            ]
        }}
        ```
        
        7. Return the JSON between triple backticks followed by 'TERMINATE'.
        """
    return research_task

def create_research_team(ensemble_output, model_choice: str) -> RoundRobinGroupChat:

    chosen_config = get_model_config(model_choice)
    model_client = ChatCompletionClient.load_component(chosen_config)

    # insert research analysts
    writer_task = f"""
        Please generate one question-answer pair using the following:
        - Course Title: '{course_title}'
        - Assessment duration: '{assessment_duration}',
        - Knowledge Statement: '{k_statement}'
        - Retrieved Content: {content}

        Instructions:
        1. Craft a realistic scenario in 2-3 sentences that provides context related to the retrieved content, but also explicitly addresses the knowledge statement.
        2. Even if the retrieved content or course title seems unrelated to the knowledge statement, creatively bridge the gap by inferring or using general knowledge. For example, if the content is about Microsoft 365 Copilot and the knowledge statement is about "Organisation's processes," generate a scenario where a department is reexamining its internal workflows using Copilot as a tool.
        3. Formulate a single, straightforward short-answer question that aligns the knowledge statement with the scenario. The question should prompt discussion on how the elements from the retrieved content could be used to address or improve the area indicated by the knowledge statement.
        4. Provide concise, practical bullet points as the answer.    
        Return the question and answer as a JSON object directly.
        """

    performance_gap_message = f"""
    You are responsible for identifying the performance gaps and post-training benefits to learners that the course will address.
    Based on the extracted data, answer the following question:
    (ii) Performance gaps that the course will address for the given course title and learning outcomes: {ensemble_output.get('Course Information', {}).get('Course Title', [])}, {ensemble_output.get('Learning Outcomes', {}).get('Learning Outcomes', [])}.
    Do not use any control characters such as newlines.

    Your task is to perform the following:
    1. For each Learning Outcome (LO), provide one unique performance gap, one corresponding attribute gained, and one post-training benefit to learners. Do not repeat performance gaps or attributes across different LOs.
    2. However, in the event that there are only 2 Learning Outcomes, you are to provide 3 unique performance gaps and corresponding attributes gained.
    3. However, in the event that there are more than 5 Learning Outcomes, your answers are to be limited to 5 unique performance gaps and corresponding attributes gained.

    Format your response in the given JSON structure under "Performance Gaps".
    Your answer for (ii.) is to be given in a point format with three distinct sections, appended together as one list element with new line separators, this is an example with only 3 Learning Outcomes, hence 3 points each:
    {{

    Performance gaps:
    Learners struggle/are unclear with [specific skill or knowledge gap].
    (perform this analysis for the LOs)

    Attributes gained:
    Ability/Proficiency to [specific skill or knowledge learned].
    (perform this analysis for the LOs)

    Post training benefits:
    (perform this analysis for the LOs)

    }}

    """

    sequencing_rationale_message = f"""
    You are an experienced course developer. Your task is to justify the rationale of sequencing 
    using a step-by-step curriculum framework for the course titled: {ensemble_output.get('Course Information', {}).get('Course Title', [])}.
    Have one pointer within Performance Gaps and Attributes Gained for each Learning Outcome
    Do not use any control characters such as newlines.
    Do not mention any course names in your analysis.
    Ensure that all Learning Units are accounted for in your analysis.

    Reference the following JSON variables in your response:
    1. Learning outcomes: {ensemble_output.get('Learning Outcomes', {}).get('Learning Outcomes', [])}
    2. Learning units: {ensemble_output.get('TSC and Topics', {}).get('Learning Units', [])}
    3. Course outline: {ensemble_output.get('Assessment Methods', {}).get('Course Outline', [])}

    Output your response for (iii.) in the following format, for example:
    {{
        Sequencing Explanation: For this course, the step-by-step sequencing is employed to scaffold the learners' comprehension and application of video marketing strategies using AI tools. The methodology is crucial as it system-atically breaks down the intricate facets of video marketing, inbound marketing strategies, and AI tools into digestible units. This aids in gradually building the learners' knowledge and skills from fundamental to more complex concepts, ensuring a solid foundation before advancing to the next topic. The progression is designed to foster a deeper understanding and the ability to effectively apply the learned concepts in real-world marketing scenarios.

        LU1: 
            Title: Translating Strategy into Action and Fostering a Customer-Centric Culture
            Description: LU1 lays the foundational knowledge by introducing learners to the organization's inbound marketing strategies and how they align with the overall marketing strategy. The facilitator will guide learners through translating these strategies into actionable plans and understanding the customer decision journey. This unit sets the stage for fostering a customer-centric culture with a particular focus on adhering to organizational policies and guidelines. The integration of AI tools in these processes is introduced, giving learners a glimpse into the technological aspects they will delve deeper into in subsequent units.

        LU2: 
            Title: Improving Inbound Marketing Strategies and Content Management
            Description: Building on the foundational knowledge, LU2 dives into the practical aspects of content creation and curation and how AI tools can be utilized for strategy improvement. Learners will be led through exercises to recommend improvements and manage content across various platforms. The hands-on activities in this unit are designed to enhance learners' ability to manage and optimize video content, crucial skills in video marketing with AI tools.

        LU3: 
            Title: Leading Customer Decision Processes and Monitoring Inbound Marketing Effectiveness
            Description: LU3 escalates to a higher level of complexity where learners delve into lead conversion processes, leading customers through decision processes, and evaluating marketing strategy effectiveness. Under the guidance of the facilitator, learners will engage in monitoring and reviewing inbound marketing strategies, thereby aligning theoretical knowledge with practical skills in a real-world context. The synthesis of previous knowledge with advanced concepts in this unit culminates in a comprehensive understanding of video marketing with AI tools, equipping learners with the requisite skills to excel in the modern marketing landscape.

        Conclusion: "Overall, the structured sequencing of these learning units is designed to address the performance gaps identified in the retail industry while equipping learners with the necessary attributes to excel in their roles as machine learning professionals."
            
    }}

    """

    editor_message = f"""
    You are to consolidate the findings without amending any of the output, mapping each agent's output to these terms accordingly.

    Only 3 keys are present, Background Analysis, Performance Analysis, Sequencing Analysis. Do not aggregate any of the Validator's output, only the researching agents. Do not aggregate validator comments, those are not essential.
    Your response will only be the consolidated mapped json findings, do not include any additional comments, completion notices such as "Here is the JSON mapping based on the provided context:" is not needed.

    The json mapping guideline list is as follows:
    {{
        "Background Analysis": {{

        }},
        "Performance Analysis": {{
            "Performance Gaps": [

            ],
            "Attributes Gained": [

            ],
            "Post-Training Benefits to Learners": [

            ]
        }},
        "Sequencing Analysis": {{
        
        "Sequencing Explanation": "",

        "LU1": {{
            "Title": "",
            "Description": ""
        }},

        "LU2": {{
            "Title": "",
            "Description": ""
        }},

        "LU3": {{
            "Title": "",
            "Description": ""
        }},

        "LU4": {{
            "Title": "",
            "Description": ""
        }},

        "Conclusion": "",

        }}
    }}
    """

    writer = AssistantAgent(
        name="writer",
        model_client=model_client,
        system_message=background_message,
    )

    performance_gap_analyst = AssistantAgent(
        name="performance_gap_analyst",
        model_client=model_client,
        system_message=performance_gap_message
    )

    sequencing_rationale_agent = AssistantAgent(
        name="sequencing_rationale_agent",
        model_client=model_client,
        system_message=sequencing_rationale_message,
    )

    editor = AssistantAgent(
        name="editor",
        model_client=model_client,
        system_message=editor_message,
    )

    research_group_chat = RoundRobinGroupChat([background_analyst, performance_gap_analyst, sequencing_rationale_agent, editor], max_turns=4)

    return research_group_chat


async def generate_saq(extracted_data: FacilitatorGuideExtraction, index, model_client, premium_mode):
    """
    Generate SAQ questions and answers asynchronously for all K statements.

    :param extracted_data: Extracted facilitator guide data.
    :param index: The LlamaIndex vector store index.
    :param model_client: The model client for question generation.
    :param premium_mode: Whether to use premium parsing.
    :return: Dictionary in the correct JSON format.
    """
    extracted_data = dict(extracted_data)
    k_topics = get_topics_for_all_k_statements(extracted_data)
    k_content_dict = await retrieve_content_for_knowledge_statement_async(k_topics, index, premium_mode)

    # print(json.dumps(k_content_dict, indent=4))  

    qa_generation_agent = AssistantAgent(
        name="question_answer_generator",
        model_client=model_client,
    )

async def generate_saq_for_k(qa_generation_agent, course_title, assessment_duration, k_statement, content):
    """
    Generate a question-answer pair for a specific K statement asynchronously.

    :param qa_generation_agent: The Autogen AssistantAgent for question-answer generation.
    :param course_title: Course title from extracted_data.
    :param assessment_duration: Duration of the SAQ assessment.
    :param k_statement: The K statement.
    :param content: The retrieved content associated with the K statement.
    :return: Generated question-answer dictionary.
    """
    agent_task = f"""
        Please generate one question-answer pair using the following:
        - Course Title: '{course_title}'
        - Assessment duration: '{assessment_duration}',
        - Knowledge Statement: '{k_statement}'
        - Retrieved Content: {content}

        Instructions:
        1. Craft a realistic scenario in 2-3 sentences that provides context related to the retrieved content, but also explicitly addresses the knowledge statement.
        2. Even if the retrieved content or course title seems unrelated to the knowledge statement, creatively bridge the gap by inferring or using general knowledge. For example, if the content is about Microsoft 365 Copilot and the knowledge statement is about "Organisation's processes," generate a scenario where a department is reexamining its internal workflows using Copilot as a tool.
        3. Formulate a single, straightforward short-answer question that aligns the knowledge statement with the scenario. The question should prompt discussion on how the elements from the retrieved content could be used to address or improve the area indicated by the knowledge statement.
        4. Provide concise, practical bullet points as the answer.    
        Return the question and answer as a JSON object directly.
    """

    response = await qa_generation_agent.on_messages(
        [TextMessage(content=agent_task, source="user")], CancellationToken()
    )

    if not response or not response.chat_message:
        return None

    # Log the raw response for debugging
    # print(f"########### Raw Response for {k_statement}: {response.chat_message.content}\n\n###########")

    qa_result = parse_json_content(response.chat_message.content)

    # Directly extract keys from the parsed JSON object:
    return {
        "scenario": qa_result.get("scenario", "Scenario not provided."),
        "question_statement": qa_result.get("question_statement", "Question not provided."),
        "knowledge_id": k_statement.split(":")[0],
        "answer": qa_result.get("answer", ["Answer not available."])
    }

async def generate_saq(extracted_data: FacilitatorGuideExtraction, index, model_client, premium_mode):
    """
    Generate SAQ questions and answers asynchronously for all K statements.

    :param extracted_data: Extracted facilitator guide data.
    :param index: The LlamaIndex vector store index.
    :param model_client: The model client for question generation.
    :param premium_mode: Whether to use premium parsing.
    :return: Dictionary in the correct JSON format.
    """
    extracted_data = dict(extracted_data)
    k_topics = get_topics_for_all_k_statements(extracted_data)
    k_content_dict = await retrieve_content_for_knowledge_statement_async(k_topics, index, premium_mode)

    # print(json.dumps(k_content_dict, indent=4))  

    qa_generation_agent = AssistantAgent(
        name="question_answer_generator",
        model_client=model_client,
        system_message=f"""
        You are an expert question-answer crafter with deep domain expertise. Your task is to generate a scenario-based question and answer pair for a given knowledge statement while strictly grounding your response in the provided retrieved content. You must not hallucinate or fabricate details.

        Guidelines:
        1. Base your response entirely on the retrieved content. If the content does not directly address the knowledge statement, do not invent new details. Instead, use minimal general context only to bridge gaps, but ensure that every key element of the final question and answer is explicitly supported by the retrieved content.
        2. Craft a realistic scenario in 2-3 sentences that reflects the context from the retrieved content while clearly addressing the given knowledge statement.
        3. Formulate one direct, simple question that ties the scenario to the knowledge statement. The question should be directly answerable using the retrieved content.
        4. Provide concise, practical bullet-point answers that list the key knowledge points explicitly mentioned in the retrieved content.         
        5. Ensure the overall assessment strictly follows the SAQ structure.
        6. Do not mention about the source of the content in the scenario or question.
        7. Structure the final output in **valid JSON** with the format:

        ```json
        {{
            "scenario": "<scenario>",
            "question_statement": "<question>",
            "knowledge_id": "<knowledge_id>",
            "answer": [
                "<bullet_point_1>",
                "<bullet_point_2>",
                "<bullet_point_3>"
            ]
        }}
        ```
        
        7. Return the JSON between triple backticks followed by 'TERMINATE'.
        """,
    )

    assessment_duration = next(
        (assessment.get("duration", "") for assessment in extracted_data.get("assessments", []) if "SAQ" in assessment.get("code", "")),
        ""
    )
    # print(f"############# ASSESSMENT DURATION\n{assessment_duration}\n#############")
    
    # Create async tasks for generating a Q&A pair for each knowledge statement
    tasks = [
        generate_saq_for_k(qa_generation_agent, extracted_data["course_title"], assessment_duration, k, content)
        for k, content in k_content_dict.items()
    ]
    results = await asyncio.gather(*tasks)
    questions = [q for q in results if q is not None]

    # Return the output with the same structure as before
    return {
        "course_title": extracted_data["course_title"],
        "duration": assessment_duration,
        "questions": questions
    }

async def generate_pp_scenario(data, model_client) -> str:
    """
    Uses the autogen agent to generate a realistic practical performance assessment scenario.
    
    Args:
        data (FacilitatorGuideExtraction): The extracted course data.
        model_client: The model client used to initialize the agent.
    
    Returns:
        str: The generated scenario.
    """
    course_title = data["course_title"]

    learning_outcomes = [lu["learning_outcome"] for lu in data["learning_units"]]
    abilities = [ability["text"] for lu in data["learning_units"] for topic in lu["topics"] for ability in topic["tsc_abilities"]]
    
    outcomes_text = "\n".join([f"- {lo}" for lo in learning_outcomes])
    abilities_text = "\n".join([f"- {ability}" for ability in abilities])
    
    agent_task = f"""
    You are tasked with designing a realistic practical performance assessment scenario for the course '{course_title}'.
    
    The scenario should align with the following:
    
    Learning Outcomes:
    {outcomes_text}
    
    Abilities:
    {abilities_text}
    
    The scenario should describe a company or organization facing practical challenges and provide background context aligning to the Learning Outcomes and abilities.
    End the scenario by stating the learner's role in the company.
    Ensure the scenario is concise (1 paragraph), realistic, and action-oriented.
    """
    
    # Instantiate the autogen agent for scenario generation
    scenario_agent = AssistantAgent(
        name="scenario_generator",
        model_client=model_client,
        system_message="You are an expert in instructional design. Create a concise, realistic scenario based on the provided course details."
    )
    
    response = await scenario_agent.on_messages(
        [TextMessage(content=agent_task, source="user")],
        CancellationToken()
    )
    
    scenario = response.chat_message.content.strip()
    return scenario

async def generate_pp_for_lo(qa_generation_agent, course_title, assessment_duration, scenario, learning_outcome, learning_outcome_id, retrieved_content, ability_ids, ability_texts):
    """
    Generate a question-answer pair for a specific Learning Outcome asynchronously.
    
    Args:
        qa_generation_agent: The Autogen AssistantAgent for question-answer generation.
        course_title: Course title.
        assessment_duration: Duration of the assessment.
        scenario: The shared scenario for the practical performance assessment.
        learning_outcome: The Learning Outcome statement.
        learning_outcome_id: The identifier for the Learning Outcome (e.g., LO1).
        retrieved_content: The retrieved content associated with the learning outcome.
        ability_ids: A list of ability identifiers associated with this learning outcome.
        ability_texts: A list of ability statements associated with this learning outcome.
        
    Returns:
        Generated question-answer dictionary with keys: learning_outcome_id, question_statement, answer, ability_id.
    """
    agent_task = f"""
        Generate one practical performance assessment question-answer pair using the following details:
        - Course Title: '{course_title}'
        - Assessment Duration: '{assessment_duration}'
        - Scenario: '{scenario}'
        - Learning Outcome: '{learning_outcome}'
        - Learning Outcome ID: '{learning_outcome_id}'
        - Associated Ability IDs: {', '.join(ability_ids)}
        - Associated Ability Statements: {', '.join(ability_texts)}
        - Retrieved Content: {retrieved_content}
        
        Instructions:
        1. Formulate a direct, hands-on task question in 2 sentences maximum without any prefatory phrases.
        2. The question must end with "Take snapshots of your commands at each step and paste them below."
        4. The answer must start with "The snapshot should include: " followed solely by the final output or solution; do not include any written explanation or narrative.
        5. Include the learning outcome id in your response as "learning_outcome_id".
        6. Include the ability ids in your response as "ability_id".
        7. Return your output in valid JSON.
    """

    response = await qa_generation_agent.on_messages(
        [TextMessage(content=agent_task, source="user")], CancellationToken()
    )

    if not response or not response.chat_message:
        return None

    qa_result = parse_json_content(response.chat_message.content)
    
    return {
        "learning_outcome_id": qa_result.get("learning_outcome_id", learning_outcome_id),
        "question_statement": qa_result.get("question_statement", "Question not provided."),
        "answer": qa_result.get("answer", ["Answer not available."]),
        "ability_id": qa_result.get("ability_id", ability_ids)
    }

async def generate_pp(extracted_data, index, model_client, premium_mode):
    """
    Generate practical performance assessment questions and answers asynchronously for all learning outcomes.

    Args:
        extracted_data: Extracted facilitator guide data.
        index: The LlamaIndex vector store index.
        model_client: The model client for question generation.

    Returns:
        Dictionary in the correct JSON format with keys: course_title, duration, scenario, questions.
    """
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    extracted_data = dict(extracted_data)
    
    scenario = await generate_pp_scenario(extracted_data, model_client)

    # Create a query engine for retrieving content related to learning outcomes
    lo_retriever_llm = llama_openai(
        model="gpt-4o-mini", 
        api_key=openai_api_key, 
        system_prompt="You are a content retrieval assistant. Retrieve inline segments that align strictly with the specified topics."
    )
    qa_generation_query_engine = index.as_query_engine(
        similarity_top_k=10,
        llm=lo_retriever_llm,
        response_mode="compact",
    )
    lo_content_dict = await retrieve_content_for_learning_outcomes(extracted_data, qa_generation_query_engine, premium_mode)

    # Autogen setup for generating question-answer pairs per Learning Outcome
    qa_generation_agent = AssistantAgent(
        name="question_answer_generator",
        model_client=model_client,
        system_message=f"""
        You are an expert question-answer crafter with deep domain expertise. Your task is to generate a practical performance assessment question and answer pair for a given Learning Outcome and its associated abilities, strictly grounded in the provided retrieved content.
        
        Guidelines:
        1. Base your response exclusively on the retrieved content.
        2. Generate a direct, hands-on task question in 2 sentences maximum without any prefatory phrases.
        3. The question must end with "Take snapshots of your commands at each step and paste them below."
        4. The answer should start with "The snapshot should include: " followed solely by the exact final output or solution.
        5. Include the learning outcome id in your response as "learning_outcome_id".
        6. Return your output in valid JSON with the following format:
        
        ```json
        {{
            "learning_outcome_id": "<learning_outcome_id>",
            "question_statement": "<question_text>",
            "answer": ["<final output or solution>"],
            "ability_id": ["<list_of_ability_ids>"]
        }}
        ```
        
        Return the JSON between triple backticks followed by 'TERMINATE'.
        """
    )
    
    assessment_duration = ""
    for assessment in extracted_data["assessments"]:
        if "PP" in assessment["code"]:
            assessment_duration = assessment["duration"]
            break

    # Create async tasks for generating a Q&A pair for each Learning Outcome
    tasks = []
    for item in lo_content_dict:
        learning_outcome = item["learning_outcome"]
        learning_outcome_id = item.get("learning_outcome_id", "")
        retrieved_content = item["retrieved_content"]
        ability_ids = item.get("abilities", [])
        ability_texts = item.get("ability_texts", [])
        tasks.append(generate_pp_for_lo(
            qa_generation_agent, 
            extracted_data["course_title"], 
            assessment_duration, 
            scenario, 
            learning_outcome, 
            learning_outcome_id,
            retrieved_content,
            ability_ids,
            ability_texts
        ))
    
    results = await asyncio.gather(*tasks)
    questions = [q for q in results if q is not None]

    # Return the final structured output
    return {
        "course_title": extracted_data["course_title"],
        "duration": assessment_duration,
        "scenario": scenario,
        "questions": questions
    }