from agents.excel_agents import create_course_agent, create_ka_analysis_agent, course_task, ka_task
import json
import asyncio
from autogen_agentchat.ui import Console
from utils.helpers import extract_agent_json, load_json_file
from utils.excel_conversion_pipeline import create_assessment_dataframe

# # Gemini
# gemini_config = {
#     "provider": "OpenAIChatCompletionClient",
#     "config": {
#         "model": "gemini-2.0-flash-exp",
#         "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
#         "api_key": GEMINI_API_KEY,
#         "model_info": {
#             "family": "unknown",
#             "function_calling": False,
#             "json_output": True,
#             "vision": False
#         }
#     }
# }

model_choice = "Gemini-Flash-2.0-Exp"

async def main():
    # Load the existing research_output.json
    with open('json_output/research_output.json', 'r', encoding='utf-8') as f:
        research_output = json.load(f)

    course_agent = create_course_agent(research_output, model_choice=model_choice)
    stream = course_agent.run_stream(task=course_task())
    await Console(stream)

    course_agent_state = await course_agent.save_state()
    with open("json_output/course_agent_state.json", "w") as f:
        json.dump(course_agent_state, f)
    course_agent_data = extract_agent_json("json_output/course_agent_state.json", "course_agent")

    # Initialize excel_data.json with an empty list
    excel_data_path = "json_output/excel_data.json"
    with open(excel_data_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    # Load existing data from excel_data.json
    try:
        with open(excel_data_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Append new data
    existing_data.append(course_agent_data)

    # Write updated data back to excel_data.json
    with open(excel_data_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)

    ensemble_output_path = "json_output/ensemble_output.json"
    ensemble_output = load_json_file(ensemble_output_path)

    instructional_methods_path = "json_output/instructional_methods.json"
    instructional_methods_output = load_json_file(instructional_methods_path)

    # K and A analysis pipeline
    instructional_methods_data = create_assessment_dataframe(ensemble_output)
    ka_agent = create_ka_analysis_agent(ensemble_output, instructional_methods_data, model_choice=model_choice)
    stream = ka_agent.run_stream(task=ka_task())
    await Console(stream)

    # TSC JSON management
    state = await ka_agent.save_state()
    with open("json_output/ka_agent_state.json", "w") as f:
        json.dump(state, f)
    ka_agent_data = extract_agent_json("json_output/ka_agent_state.json", "ka_analysis_agent")

    # Load existing data from excel_data.json again
    try:
        with open(excel_data_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Append new data
    existing_data.append(ka_agent_data)

    # Write updated data back to excel_data.json
    with open(excel_data_path, "w", encoding="utf-8") as out:
        json.dump(existing_data, out, indent=2)

if __name__ == "__main__":
    asyncio.run(main())