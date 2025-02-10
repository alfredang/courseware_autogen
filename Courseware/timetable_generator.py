# timetable_generator.py

import re
import json
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage

async def generate_timetable(context, num_of_days, model_client):

    timetable_generator_agent = AssistantAgent(
        name="Timetable_Generator",
        model_client=model_client,
        system_message=f"""
You are a timetable generator for WSQ courses.
Your task is to create a detailed lesson plan timetable for a WSQ course based on the provided course information and context. Follow all the specified rules and ensure that your output exactly follows the format described below.

### Instructions:

1. **Course Data**:
    - Use the provided course context data, including course details, Learning Units (LUs), topics, Learning Outcomes (LOs), Assessment Methods (AMs), and Instructional Methods (IMs).
    - **Ensure that every topic and its bullet points from the context are included. Do not omit any topics or bullet points.**

2. **Number of Days**:
    - Use exactly {num_of_days} days for the timetable.
    - Distribute topics, activities, and sessions evenly across these days.

3. **Handling Too Many or Too Few Topics**:
    - **If there are too many topics for the allotted days:** Adjust session durations, increase the number of bullet points covered per session, and combine similar points if needed, while ensuring the total daily schedule does not exceed 8 hours (0930hrs - 1830hrs).
    - **If there are too few topics:** Extend session durations or break topic sessions into multiple parts to fully utilize each day without exceeding the daily constraints.

4. **Fixed Sessions and Breaks**:
    - **Day 1 First Timeslot (always):**
        - **Time**: "0930hrs - 0945hrs (15 mins)"
        - **Instructions**: "Digital Attendance and Introduction to the Course\n\n- Trainer Introduction\n- Learner Introduction\n- Overview of Course Structure"
        - **Instructional_Methods**: "N/A"
        - **Resources**: "N/A"
    - **Subsequent Days First Timeslot:**
        - **Time**: "0930hrs - 0940hrs (10 mins)"
        - **Instructions**: "Digital Attendance (AM)"
        - **Instructional_Methods**: "N/A"
        - **Resources**: "N/A"
    - Include other fixed sessions such as Morning Break, Lunch Break, PM Attendance, Afternoon Break, and an End-of-Day Recap (on non-assessment days) as per your rules.
    - **Final Day Assessments:**  
        Schedule assessments sequentially at the end of the last day (with a pre-assessment Digital Attendance session and a Course Feedback session), ensuring no gaps or overlaps.

5. **Session Structure for Topics and Activities**:
    - **Topic Sessions:**
        - **Time**: Varies (for example, "0945hrs - 1050hrs (65 mins)")
        - **Instructions**: Must follow the format: "**Topic X: [Topic Title] (K#, A#)**" followed by bullet points (each starting with "•").  
        For example:
        ```
        Topic 1: Foundations of Consultative Selling (K1, A1)
        
        • Understanding the Psychology of Consultative Selling
        • Knowing Your Customers with the Consultative Selling Mindset
        ```
    - **Activity Sessions:**
        - **Time**: Fixed at 10 minutes.
        - **Instructions**: **Include only the activity header** (e.g., "Activity: Case Study on Key Criteria for Evaluating Sales Closure Processes"). Do not include the facilitator guidance lines here (they are hardcoded in the template).
    - **Instructional Methods and Resources:**
        - Must match the provided lists and exactly reflect what is specified in the context (for example, "Lecture, Peer Sharing" and "Slide page #, TV, Whiteboard").

6. **Output Format**:
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
                        }}
                        // Additional sessions for the day
                    ]
                }}
                // Additional days
            ]
        }}
        ```
    - **Ensure that:**
        - All timings are consecutive without gaps or overlaps.
        - Each day totals exactly 8 hours (including all sessions, breaks, lunch, and assessments).
        - The total number of days in the timetable is exactly {num_of_days}.
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
    """

    # Process sample input
    response = await timetable_generator_agent.on_messages(
        [TextMessage(content=agent_task, source="user")], CancellationToken()
    )

    try:
        timetable_response = json.loads(response.chat_message.content)
        if 'lesson_plan' not in timetable_response:
            raise Exception("No lesson_plan key found in timetable data")
        return timetable_response

    except Exception as e:
        raise Exception(f"Failed to parse timetable JSON: {str(e)}")
