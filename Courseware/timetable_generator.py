# timetable_generator.py

import re
import json
from autogen import UserProxyAgent, AssistantAgent

def generate_timetable(context, num_of_days, llm_config):
    user_proxy = UserProxyAgent(
        name="User",
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",
        code_execution_config={"work_dir": "output", "use_docker": False}
    )

    timetable_generator_agent = AssistantAgent(
        name="Timetable_Generator",
        llm_config=llm_config,
        system_message=f"""
        You are a timetable generator for WSQ courses.
        Your task is to create a detailed lesson plan timetable for a WSQ course based on the provided course information and context, following all specified rules and requirements.

        ### Instructions:

        1. **Course Data**:
        - Use the provided course context data, including course details, Learning Units (LUs), topics, Learning Outcomes (LOs), Assessment Methods (AMs), and Instructional Methods (IMs).
        - **Ensure that every single topic and its bullet points from the context are included and covered in the timetable. Do not omit any topics or bullet points.**

        2. **Number of Days**:
        - Use exactly {num_of_days} days for the timetable. Distribute topics, activities, and sessions evenly across these days.
        
        3. **Handling Too Many or Too Few Topics**:

        - **If there are too many topics to fit into the {num_of_days} days**:
            - **Prioritize covering all topics and bullet points within the allotted days by adjusting session durations.**
            - **Increase the number of bullet points covered per session.**
            - **Combine similar bullet points for the topic where appropriate to optimize time.**
            - **Ensure that the daily schedule does not exceed 8 hours (0930hrs - 1830hrs).**

        - **If there are too few topics to fill the {num_of_days} days**:
            - **Extend session durations to allow for deeper exploration of topics.**
            - **Break Topics sessions into multiple sessions to fill up the lesson plan.**
            - **Ensure that each day's schedule is fully utilized without exceeding daily time constraints.**

        4. **Daily Schedule**:
        - **Day 1 First Timeslot**:
            - **Time**: "0930hrs - 0945hrs (15 mins)"
                - **Instructions**: "Digital Attendance and Introduction to the Course\n\n- Trainer Introduction\n- Learner Introduction\n- Overview of Course Structure"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "N/A"

        - **Subsequent Days First Timeslot**:
            - **Time**: "0930hrs - 0940hrs (10 mins)"
                - **Instructions**: "Digital Attendance (AM)"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "N/A"

        - **Mandatory Sessions with Fixed Time Slots**:
            - **Morning Break**:
                - **Time**: "1050hrs - 1100hrs (10 mins)"
                - **Instructions**: "Morning Break"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "N/A"
                
            - **Lunch Break**:
                - **Time**: "1200hrs - 1245hrs (45 mins)"
                - **Instructions**: "Lunch Break"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "N/A"

            - **PM Attendance**:
                - **Time**: "1330hrs - 1340hrs (10 mins)"
                - **Instructions**: "Digital Attendance (PM)"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "N/A"

            - **Afternoon Break**:
                - **Time**: "1500hrs - 1510hrs (10 mins)"
                - **Instructions**: "Afternoon Break"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "N/A"

            - **End-of-Day Recap**:
                - Include on all days except the final day consisting of assessments.
                - **Instructions**: "Recap All Contents and Close"
                - **Instructional_Methods**: "Lecture, Group Discussion"
                - **Resources**: "Slide page #, TV, Whiteboard"

        5. **Final Day Assessment Schedule**:
        - Allocate assessment times precisely according to the `Total_Delivery_Hours` specified for each assessment method in `Assessment_Methods_Details`.
        - The assessments must be scheduled sequentially, starting at the designated assessment start time.
        - The assessments must be scheduled at the end of the last day.
        - Include a 10-minute **Digital Attendance (Assessment)** session immediately before the first assessment begins.
        - Use the following format for assessments:

            - **Assessment Attendance (Last Day)**:
                - **Time**: 10 minutes before the first assessment starts
                - **Instructions**: "Digital Attendance (Assessment)"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "N/A"

            - **For Each Assessment Method (Last Day)**:
                - **Time**: "[Start Time] - [End Time] ([Duration])"
                - **Instructions**: "Final Assessment: [Assessment Method Full Name] ([Method Abbreviation])"
                - **Instructional_Methods**: "Assessment"
                - **Resources**: "Assessment Questions, Assessment Plan"

            - **Course Feedback Session (Last Day)**:
                - **Time**: "1810hrs - 1830hrs (20 mins)"
                - **Instructions**: "Course Feedback and TRAQOM Survey"
                - **Instructional_Methods**: "N/A"
                - **Resources**: "Feedback Forms, Survey Links"

        - Ensure that the total assessment time matches the `Total_Assessment_Hours` specified.
        - Ensure that Assessment Attendance, Assessments, and Course Feedback Session are consecutive with NO GAPS OR OVERLAPS.
        
        6. **Session Structure**:
        - **Topics**:
            - **Duration**: Ranging from 30 mins to 120 mins.
            - For each topic, the instructions must follow this format:
                - **Instructions**: "**Topic X: [Topic Title] (K#, A#)**\n\n[Bullet Points or Additional Details]"
            - **Content Distribution Rule**:
                - **Each Topic session must be associated from a topic bullet point.**
                - **There is no maximum limit on the number of bullet points per session.**
                - **Ensure that the topics and their bullet points are distributed evenly across the calculated number of days, fitting within the daily time constraints.**
                - **Do not omit any topics or bullet points from the context.**

        - **Instructional Methods Alignment**:
            - Only include instructional methods that are specified in the `Instructional_Methods` list within the context JSON for each Learning Unit (LU).
            - Do not include any instructional methods not present in the context.
            - Use specified IMs for each LU, strictly only selecting pairs from:
                - "Lecture, Didactic Questioning"
                - "Lecture, Peer Sharing"
                - "Lecture, Group Discussion"
            - Select the pair only if the instructional methods are specified in the context for that LU.

        - **Resources**:
            - "Slide page #"
            - "TV"
            - "Whiteboard"
            - "Wi-Fi"

        - **Activities and Facilitator Guidance**:
            - **Duration**: Exactly 10 mins.
            - Follow immediately after the corresponding topic.
            - **Instructions**:
                - Activity header needs to include the "Activity: " prefix.
                - Activity header format depends on the Instructional Method:
                    - For "Demonstration, Practice" or "Demonstration, Group Discussion":
                        ```
                        "Activity: Demonstration on [Description]"
                        ```
                    - For "Case Study":
                        ```
                        "Activity: Case Study on [Description]"
                        ```
                - Include Facilitator's Guidance:
                    - "Facilitator will explain and demonstrate the activities to learners."
                    - "Facilitators are encouraged to invite learners to share their own answers with the class."
                    - "Facilitators are encouraged to share their own personal experiences to incorporate real-life scenarios."
                    - For "Case Study" activities, include:
                        - "Facilitator will break the class into groups of 3 to 5 participants."
                        - "Facilitator will explain the case study to learners."

            - **Instructional Methods Alignment**:
                - Only include instructional methods that are specified in the `Instructional_Methods` list within the context JSON for each Learning Unit (LU).
                - Do not include any instructional methods not present in the context.
                - Use specified IMs for each LU, strictly only selecting pairs from:
                    - "Demonstration, Practice"
                    - Change "Practical" to "Practice"
                    - "Demonstration, Group Discussion"
                    - "Case Study"
                - Select the pair only if the instructional methods are specified in the context.

            - **Resources for Activities**:
                - "Slide page #"
                - "TV"
                - "Whiteboard"
                - "Wi-Fi"

        ### Output Format
        - Return a JSON object with the following structure:

        ```json
        {{
            "lesson_plan": [
                {{
                    "Day": "Day X",
                    "Sessions": [
                        {{
                            "Time": "Start - End (duration)",
                            "Instructions": "Session content",
                            "Instructional_Methods": "Method pair",
                            "Resources": "Required resources"
                        }},
                        // Additional sessions for the day
                    ]
                }},
                // Additional days
            ]
        }}
        ```
        - Ensure all timings are consecutive without gaps or overlaps.
        - Each day must total exactly 8 hours, including all sessions, breaks, lunch, and assessments.
        - Ensure that the total number of days in the timetable matches {num_of_days}. Do not generate more days than specified.
        - Use the time format: "0930hrs - 0945hrs (15 mins)".
    """
    )

    agent_task = f"""
        1. Take the complete dictionary provided:
        {context}
        2. Use the provided JSON dictionary, which includes all the course information, to generate the lesson plan timetable.

        **Instructions:**
        1. Adhere to all the rules and guidelines.
        2. Include the timetable data under the key 'lesson_plan' within a JSON dictionary.
        3. Return the JSON dictionary containing the 'lesson_plan' key.
        4. Include the word 'json' in your response.
    """

    chat_results = user_proxy.initiate_chats(
        [
            {
                "chat_id": 1,
                "recipient": timetable_generator_agent,
                "message": agent_task,
                "silent": False,
                "summary_method": "last_msg",
                "max_turns": 1
            }
        ]
    )

    timetable_response = timetable_generator_agent.last_message()["content"]

    # Extract the timetable JSON from the response
    try:
        json_pattern = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)
        json_match = json_pattern.search(timetable_response)
        if not json_match:
            raise Exception("No JSON found in timetable generator response")
        json_str = json_match.group(1)
        timetable_data = json.loads(json_str)
        if 'lesson_plan' not in timetable_data:
            raise Exception("No lesson_plan key found in timetable data")
        return timetable_data
    except Exception as e:
        raise Exception(f"Failed to parse timetable JSON: {str(e)}")
