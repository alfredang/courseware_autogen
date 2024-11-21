import autogen
from dotenv import load_dotenv
import json
import streamlit as st
import os
from autogen import UserProxyAgent, AssistantAgent
from pprint import pprint
import subprocess
import sys
import re

load_dotenv()

def agent_validation():
    # Load API key from environment
    # OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


    with open('output_TSC.json', 'r', encoding='utf-8') as file:
        output_TSC = json.load(file)
    
    # Manually create the config list with JSON response format
    config_list = [
        {
            "model": "gpt-4o-mini",
            "api_key": OPENAI_API_KEY
        }
    ]

    llm_config = {
        "temperature": 0,
        "config_list": config_list,
        "timeout": 120,  # in seconds
    }

    TSC_validation_agent = AssistantAgent(
        name="TSC_validation_agent",
        llm_config=llm_config,
        system_message="""
        You are a rule-based agent designed to ensure that a document adheres to a set of given rules. 
        """,
    )

    KA_validation_agent = AssistantAgent(
        name="KA_validation_agent",
        llm_config=llm_config,
        system_message="""
        You are a rule-based agent designed to ensure that a document adheres to a set of given rules. 
        """,
    )

    critic_agent = AssistantAgent(
    name="Critic",
    llm_config=llm_config,
    system_message="""
    You are tasked with reviewing the output provided by another agent and determining if it is grounded in facts and is not hallucinating an answer.
    """,
    )

    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        code_execution_config={
            "work_dir": "cwgen_output",
            "use_docker": False
        },
    )
    
    # Add in a reflection message to ensure that it double checks its own interpretations
    def reflection_message(recipient, messages, sender, config):
        print("Reflecting...")
        return f"""
        Review the response, and check again if that is truly the case as mentioned. Do not hallucinate and base your inference on the solely on the verdict and the data.
        In case of a response indicating FAILURE: {{reason, data that led to the failure}}, your task is to analyze the data that led to the failure and decide if it is grounded in facts.


        \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}
        """
    
    nested_chat_queue = [
    {
        "recipient": critic_agent,
        "message": reflection_message,
        "max_turns": 1,
    },
    ]

    user_proxy.register_nested_chats(
        nested_chat_queue,
        trigger=TSC_validation_agent,  # condition=my_condition,
    )


    TSC_validation_agent_message = f"""
    Based on the following document details, you are to parse and ensure that the following rules are followed.
    1. If Practice/Practical Instructional Method is present, there must be some form of time unit assigned to it. If there is no such method, ignore these instructions.
    2. At least 1 Learning Unit (LUs) must be present.
    3. When compared to each other, LUs do not have conflicting K and A factors mapped to them.
    4. All K and A factors are accounted for when taking into context, all the Topics and LUs
    5. LUs and Topics must follow the format as seen below, with LU[number]: [content] and Topic[number]: [content]. A colon must be present.

    Additional Notes for Consideration:
    - K and A factors need not follow a numerical order as these are predetermined. Your only task is to check if any factors are repeated across LUs as this would lead to an error in further mapping.
    - Topics that are nested under a LU should have a correct consolidation of their K and A factors within the LU's title.
    - Ensure that your verdict is grounded in facts provided by the context.

    Incorrect Scenario 1: {{
    LU1: Craft a Compelling Brand Identity (A1, K1, K4)
    LU2: Optimise social media campaign performance (A1, A2, A3, K3, K6)

    Reasoning: There cannot be duplicates of any A or K factors across LUs.
    }}

    Incorrect Scenario 2: {{
    LU1 Craft a Compelling Brand Identity (A1, K1, K4)

    Reasoning: There is no colon present in the LU's naming convention.
    }}

    Incorrect Scenario 3: {{
    "K1 Objectives of campaigns",
    "K2 Components of operational plans",
    "K3 Considerations when selecting the marketing mix",
    "K4 Types of products and/or services to be advertised",
    "K5 Campaign schedules",
    "K6 Means of using data gathered from pre-campaign testing",

    LU1: Craft a Compelling Brand Identity (A1, K1, K4, K7)

    Reasoning: There is no K7, yet it is mapped to the LU.
    }}

    Incorrect Scenario 4: {{
    "TSC Knowledge:",
    "K1 Legal and ethical considerations relating to the management of capability development",
    "K2 Organisational policies and procedures relating to capability development",
    "K3 Relevant professional or industry codes of practice and standards relating to management of capability development as a manager of a department or cross functional team",
    "K4 Implications and impact of coaching and mentoring activities on the individuals participating in the processes",
    "K5 Models and methods of training needs analysis",
    "K6 Market trends and developments on new and emerging skill requirements, talent management and learning and development",
    "K7 Models, methods and tools for identifying, assessing and managing talent",
    "K8 Professional or industry codes of practice and standards relating to talent management",
    "K9 Line manager roles and accountabilities for implementing talent management processes",
    "TSC Abilities:",
    "A1 Review organisational strategies and business plans to identify impact on team competency requirements",
    "A2 Review current skills of team leaders using appropriate methods and tools to identify skills requirements",
    "A3 Work with team leaders to establish their learning priorities and learning and development plans",
    "A4 Identify learning and development opportunities and provide resources and support to facilitate the development of team leader skills",
    "A5 Review capability development approaches for team leaders to identify areas for improvement",
    "A6 Provide coaching to team leaders to enhance their role performance, taking into consideration their emotional states",
    "A7 Review coaching outcomes against coaching goals to identify areas for improvement in the coaching process"

    "LU1: Managerial Leadership & Development (A1, K3, K4, K6)"
    "LU2: Relationship Building & Team Dynamics (A2, A4, K7, K9)"
    "LU3: Coaching Models and Methods (A1, A5, A6, K5)"
    "LU4: Advanced Coaching Practices & Feedback (A7, K2)"

    Reasoning: K8 and A3 are present in the document, but is missing from the LU mappings.
    }}

    If any of these are not present, reply with the message:
    "FAIL: {{Reason for Failure, and the exact line within the data which led to the failure}}

    If all conditions are met, reply with:
    "SUCCESS"

    Document Details:
    {output_TSC}

    """

    validation_chat = user_proxy.initiate_chat(
        TSC_validation_agent,
        message=TSC_validation_agent_message,
        summary_method="last_msg",
        max_turns=2  # Define the maximum turns you want the chat to last
    )

    TSC_validation_agent_message_response = TSC_validation_agent.last_message()["content"]


    # print(assessment_justification_agent_chat)
    print(TSC_validation_agent_message)

    # Process the agent's response
    response = TSC_validation_agent_message_response.strip()

    if response == "SUCCESS":
        # Continue with the rest of the script
        print("Validation successful. Proceeding with the rest of the script.")
    elif response.startswith("FAIL:"):
        reason = response[5:].strip()
        print(f"Validation failed: {reason}")
        sys.exit(1)  # Terminate the script
    else:
        print("Unexpected response from the agent.")
        sys.exit(1)  # Terminate due to unexpected response
            
KA_validation_agent_message = f"""
    You are to validate and confirm that all Knowledge and Ability factors are accounted for by the Topics.
    Topics are structured in this way:
    Topic [number]: [title] (K and A factors)
    Knowledge Factors: {ensemble_output.get('Learning Outcomes', {}).get('Knowledge', [])}
    Ability Factors: {ensemble_output.get('Learning Outcomes', {}).get('Ability', [])}

    The above factors must all be accounted for by the topics, if any are missing or unaccounted for, reply with the message: 
    "FAIL: {{Reason for Failure, missing K or A factor that led to the failure}}

    If all conditions are met, reply with:
    "SUCCESS"
    
    Incorrect Scenario 1: {{
    LU1: Craft a Compelling Brand Identity (A1, K1, K4)
    LU2: Optimise social media campaign performance (A1, A2, A3, K3, K6)

    Reasoning: There cannot be duplicates of any A or K factors across LUs.
    }}

    Incorrect Scenario 2: {{
    LU1 Craft a Compelling Brand Identity (A1, K1, K4)

    Reasoning: There is no colon present in the LU's naming convention.
    }}

    Incorrect Scenario 3: {{
    "K1 Objectives of campaigns",
    "K2 Components of operational plans",
    "K3 Considerations when selecting the marketing mix",
    "K4 Types of products and/or services to be advertised",
    "K5 Campaign schedules",
    "K6 Means of using data gathered from pre-campaign testing",

    LU1: Craft a Compelling Brand Identity (A1, K1, K4, K7)

    Reasoning: There is no K7, yet it is mapped to the LU.
    }}

    Incorrect Scenario 4: {{
    "TSC Knowledge:",
    "K1 Legal and ethical considerations relating to the management of capability development",
    "K2 Organisational policies and procedures relating to capability development",
    "K3 Relevant professional or industry codes of practice and standards relating to management of capability development as a manager of a department or cross functional team",
    "K4 Implications and impact of coaching and mentoring activities on the individuals participating in the processes",
    "K5 Models and methods of training needs analysis",
    "K6 Market trends and developments on new and emerging skill requirements, talent management and learning and development",
    "K7 Models, methods and tools for identifying, assessing and managing talent",
    "K8 Professional or industry codes of practice and standards relating to talent management",
    "K9 Line manager roles and accountabilities for implementing talent management processes",
    "TSC Abilities:",
    "A1 Review organisational strategies and business plans to identify impact on team competency requirements",
    "A2 Review current skills of team leaders using appropriate methods and tools to identify skills requirements",
    "A3 Work with team leaders to establish their learning priorities and learning and development plans",
    "A4 Identify learning and development opportunities and provide resources and support to facilitate the development of team leader skills",
    "A5 Review capability development approaches for team leaders to identify areas for improvement",
    "A6 Provide coaching to team leaders to enhance their role performance, taking into consideration their emotional states",
    "A7 Review coaching outcomes against coaching goals to identify areas for improvement in the coaching process"

    "LU1: Managerial Leadership & Development (A1, K3, K4, K6)"
    "LU2: Relationship Building & Team Dynamics (A2, A4, K7, K9)"
    "LU3: Coaching Models and Methods (A1, A5, A6, K5)"
    "LU4: Advanced Coaching Practices & Feedback (A7, K2)"

    Reasoning: K8 and A3 are present in the document, but is missing from the LU mappings.
    }}

    If any of these are not present, reply with the message:
    "FAIL: {{Reason for Failure, and the exact line within the data which led to the failure}}

    If all conditions are met, reply with:
    "SUCCESS"

    Document Details:
    {output_TSC}

    """

    KA_validation_agent_message = f"""
    Based on the following document details, you are to parse and ensure that the following rules are followed.
    1. If Practice/Practical Instructional Method is present, there must be some form of time unit assigned to it. If there is no such method, ignore these instructions.
    2. At least 1 Learning Unit (LUs) must be present.
    3. When compared to each other, LUs do not have conflicting K and A factors mapped to them.
    4. All K and A factors are accounted for when taking into context, all the Topics and LUs
    5. LUs and Topics must follow the format as seen below, with LU[number]: [content] and Topic[number]: [content]. A colon must be present.

    Additional Notes for Consideration:
    - K and A factors need not follow a numerical order as these are predetermined. Your only task is to check if any factors are repeated across LUs as this would lead to an error in further mapping.
    - Topics that are nested under a LU should have a correct consolidation of their K and A factors within the LU's title.
    - Ensure that your verdict is grounded in facts provided by the context.

    Incorrect Scenario 1: {{
    LU1: Craft a Compelling Brand Identity (A1, K1, K4)
    LU2: Optimise social media campaign performance (A1, A2, A3, K3, K6)

    Reasoning: There cannot be duplicates of any A or K factors across LUs.
    }}

    Incorrect Scenario 2: {{
    LU1 Craft a Compelling Brand Identity (A1, K1, K4)

    Reasoning: There is no colon present in the LU's naming convention.
    }}

    Incorrect Scenario 3: {{
    "K1 Objectives of campaigns",
    "K2 Components of operational plans",
    "K3 Considerations when selecting the marketing mix",
    "K4 Types of products and/or services to be advertised",
    "K5 Campaign schedules",
    "K6 Means of using data gathered from pre-campaign testing",

    LU1: Craft a Compelling Brand Identity (A1, K1, K4, K7)

    Reasoning: There is no K7, yet it is mapped to the LU.
    }}

    Incorrect Scenario 4: {{
    "TSC Knowledge:",
    "K1 Legal and ethical considerations relating to the management of capability development",
    "K2 Organisational policies and procedures relating to capability development",
    "K3 Relevant professional or industry codes of practice and standards relating to management of capability development as a manager of a department or cross functional team",
    "K4 Implications and impact of coaching and mentoring activities on the individuals participating in the processes",
    "K5 Models and methods of training needs analysis",
    "K6 Market trends and developments on new and emerging skill requirements, talent management and learning and development",
    "K7 Models, methods and tools for identifying, assessing and managing talent",
    "K8 Professional or industry codes of practice and standards relating to talent management",
    "K9 Line manager roles and accountabilities for implementing talent management processes",
    "TSC Abilities:",
    "A1 Review organisational strategies and business plans to identify impact on team competency requirements",
    "A2 Review current skills of team leaders using appropriate methods and tools to identify skills requirements",
    "A3 Work with team leaders to establish their learning priorities and learning and development plans",
    "A4 Identify learning and development opportunities and provide resources and support to facilitate the development of team leader skills",
    "A5 Review capability development approaches for team leaders to identify areas for improvement",
    "A6 Provide coaching to team leaders to enhance their role performance, taking into consideration their emotional states",
    "A7 Review coaching outcomes against coaching goals to identify areas for improvement in the coaching process"

    "LU1: Managerial Leadership & Development (A1, K3, K4, K6)"
    "LU2: Relationship Building & Team Dynamics (A2, A4, K7, K9)"
    "LU3: Coaching Models and Methods (A1, A5, A6, K5)"
    "LU4: Advanced Coaching Practices & Feedback (A7, K2)"

    Reasoning: K8 and A3 are present in the document, but is missing from the LU mappings.
    }}

    If any of these are not present, reply with the message:
    "FAIL: {{Reason for Failure, and the exact line within the data which led to the failure}}

    If all conditions are met, reply with:
    "SUCCESS"

    Document Details:
    {output_TSC}

    """

if __name__ == "__main__":
    agent_validation()


