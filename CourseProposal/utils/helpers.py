import json
import re
import sys
import os

def validate_knowledge_and_ability():
    try:
        # Read data from the JSON file
        with open('CourseProposal/json_output/ensemble_output.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Extract Knowledge and Ability factors from the data
        knowledge_factors = set([k.split(":")[0].strip() for k in data['Learning Outcomes']['Knowledge']])
        ability_factors = set([a.split(":")[0].strip() for a in data['Learning Outcomes']['Ability']])

        # Extract topics and their factors
        topics = data['TSC and Topics']['Topics']
        topic_factors = []

        # Collect all K and A factors present in topics
        extra_factors = set()
        for topic in topics:
            # Extract K and A factors from the topic (assuming it's in the form of 'K[number], A[number]')
            factors = re.findall(r'(K\d+|A\d+)', topic)
            topic_factors.append(set(factors))

            # Check for extra factors (those not in Knowledge or Ability)
            for factor in factors:
                if factor not in knowledge_factors and factor not in ability_factors:
                    extra_factors.add(factor)

        # Validate that each Knowledge and Ability factor is accounted for by at least one topic
        all_factors_accounted_for = True
        missing_factors = []

        # Check each Knowledge factor
        for k in knowledge_factors:
            if not any(k in topic for topic in topic_factors):
                missing_factors.append(f"Knowledge factor {k} is missing from topics")
                all_factors_accounted_for = False

        # Check each Ability factor
        for a in ability_factors:
            if not any(a in topic for topic in topic_factors):
                missing_factors.append(f"Ability factor {a} is missing from topics")
                all_factors_accounted_for = False

        # Handle extra factors (those not in Knowledge or Ability)
        if extra_factors:
            all_factors_accounted_for = False
            for extra in extra_factors:
                missing_factors.append(f"Extra factor {extra} found in topics but not in Knowledge or Ability list")

        # Print the custom error message if any factors are missing, else print success
        if not all_factors_accounted_for:
            error_message = "FAIL: " + "; ".join(missing_factors)
            print(error_message)
            sys.exit(error_message)  # Terminate the script with error code
        else:
            print("SUCCESS")

    except Exception as e:
        # Catch any unforeseen errors and print a custom error message before exiting
        print(f"ERROR: {str(e)}")
        sys.exit(error_message)


def extract_final_aggregator_json(file_path: str = "group_chat_state.json"):
    """
    Reads the specified JSON file (default: 'group_chat_state.json'),
    finds the aggregator agent's final response, and extracts the
    substring from the first '{' to the last '}'.
    
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    aggregator_key_name = "aggregator"  # Exact agent name
    found_key = None
    if "agent_states" not in data or not isinstance(data["agent_states"], dict):
        print(f"Warning: 'agent_states' not found or not a dictionary in {file_path}.")
        return {}

    for key in data["agent_states"]:
        if key == aggregator_key_name:
            found_key = key
            break

    if not found_key:
        print(f"No key for agent '{aggregator_key_name}' found in agent_states of {file_path}.")
        return {}

    aggregator_state = data["agent_states"][found_key]
    if not isinstance(aggregator_state, dict) or "agent_state" not in aggregator_state or \
       not isinstance(aggregator_state["agent_state"], dict) or "llm_context" not in aggregator_state["agent_state"] or \
       not isinstance(aggregator_state["agent_state"]["llm_context"], dict) or "messages" not in aggregator_state["agent_state"]["llm_context"]:
        print(f"Unexpected structure for agent '{found_key}' state in {file_path}.")
        return {}

    messages = aggregator_state["agent_state"]["llm_context"]["messages"]
    if not messages or not isinstance(messages, list):
        print(f"No messages found or messages is not a list for agent '{found_key}' in {file_path}.")
        return {}

    final_message_obj = messages[-1]
    if not isinstance(final_message_obj, dict) or "content" not in final_message_obj:
        print(f"Final message for agent '{found_key}' has unexpected structure or no content in {file_path}.")
        return {}

    final_message = final_message_obj.get("content", "")

    # Remove code block markers if present
    if final_message.startswith("```json"):
        final_message = final_message[len("```json"):].strip()
    if final_message.startswith("```"):
        final_message = final_message[len("```"):].strip()
    if final_message.endswith("```"):
        final_message = final_message[:-3].strip()

    # Now extract JSON
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        print("Message content was:", repr(final_message))
        return None

    json_str = final_message[start_index:end_index + 1].strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Failed to parse aggregator content as valid JSON.")
        print("Error:", e)
        print("String was:", repr(json_str))
        return None

def extract_final_editor_json(file_path: str = "research_group_chat_state.json"):
    """
    Reads the specified JSON file (default: 'research_group_chat_state.json'),
    finds the editor agent's final response, and extracts the
    substring from the first '{' to the last '}'.
    
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify the editor key
    editor_agent_name = "editor"  # Exact agent name
    found_key = None
    if "agent_states" not in data or not isinstance(data["agent_states"], dict):
        print(f"Warning: 'agent_states' not found or not a dictionary in {file_path}.")
        return {}

    for key in data["agent_states"]:
        if key == editor_agent_name:
            found_key = key
            break

    if not found_key:
        print(f"No key for agent '{editor_agent_name}' found in agent_states of {file_path}.")
        return {}

    # 2. Get the editor agent state and retrieve the final message
    editor_state = data["agent_states"][found_key]
    if not isinstance(editor_state, dict) or "agent_state" not in editor_state or \
       not isinstance(editor_state["agent_state"], dict) or "llm_context" not in editor_state["agent_state"] or \
       not isinstance(editor_state["agent_state"]["llm_context"], dict) or "messages" not in editor_state["agent_state"]["llm_context"]:
        print(f"Unexpected structure for agent '{found_key}' state in {file_path}.")
        return {}

    messages = editor_state["agent_state"]["llm_context"]["messages"]
    if not messages or not isinstance(messages, list):
        print(f"No messages found or messages is not a list for agent '{found_key}' in {file_path}.")
        return {}
        
    final_message_obj = messages[-1]
    if not isinstance(final_message_obj, dict) or "content" not in final_message_obj:
        print(f"Final message for agent '{found_key}' has unexpected structure or no content in {file_path}.")
        return {}

    final_message = final_message_obj.get("content", "")
    if not final_message or not isinstance(final_message, str):
        print(f"Final message for agent '{found_key}' is empty or not a string in {file_path}.")
        return {}

    # 3. Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # 4. Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Failed to parse editor content as valid JSON.")
        return None

def rename_keys_in_json_file(filename):
    key_mapping = {
    "course_info": "Course Information",
    "learning_outcomes": "Learning Outcomes",
    "tsc_and_topics": "TSC and Topics",
    "assessment_methods": "Assessment Methods"
    }
    # Load the JSON data from the file
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    if not data or not isinstance(data, dict):
        print(f"Warning: {filename} is empty or not a dict. Skipping key renaming.")
        return
    # Rename keys according to the key_mapping
    for old_key, new_key in key_mapping.items():
        if old_key in data:
            data[new_key] = data.pop(old_key)
    # Save the updated JSON data back to the same file
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)
    print(f"Updated JSON saved to {filename}")

def update_knowledge_ability_mapping(tsc_json_path, ensemble_output_json_path):
    # Load the JSON files
    with open(tsc_json_path, 'r', encoding='utf-8') as tsc_file:
        tsc_data = json.load(tsc_file)
    
    with open(ensemble_output_json_path, 'r', encoding='utf-8') as ensemble_file:
        ensemble_data = json.load(ensemble_file)
    
    # Extract the learning units from output_TSC
    course_proposal_form = tsc_data.get("Course_Proposal_Form", {})
    learning_units = {key: value for key, value in course_proposal_form.items() if key.startswith("LU")}
    
    # Prepare the Knowledge and Ability Mapping structure in ensemble_output if it does not exist
    if "Knowledge and Ability Mapping" not in ensemble_data["Learning Outcomes"]:
        ensemble_data["Learning Outcomes"]["Knowledge and Ability Mapping"] = {}

    # Loop through each Learning Unit to extract and map K and A factors
    for index, (lu_key, topics) in enumerate(learning_units.items(), start=1):
        ka_key = f"KA{index}"
        ka_mapping = []

        # Extract K and A factors from each topic within the Learning Unit
        for topic in topics:
            # Match K and A factors in the topic string using regex
            matches = re.findall(r'\b(K\d+|A\d+)\b', topic)
            if matches:
                ka_mapping.extend(matches)

        # Ensure only unique K and A factors are added
        ka_mapping = list(dict.fromkeys(ka_mapping))  # Remove duplicates while preserving order

        # Add the KA mapping to the ensemble_data
        ensemble_data["Learning Outcomes"]["Knowledge and Ability Mapping"][ka_key] = ka_mapping

    # Save the updated JSON to the same file path
    with open(ensemble_output_json_path, 'w', encoding='utf-8') as outfile:
        json.dump(ensemble_data, outfile, indent=4, ensure_ascii=False)

    print(f"Updated Knowledge and Ability Mapping saved to {ensemble_output_json_path}")

def extract_final_agent_json(file_path: str = "assessment_justification_agent_state.json"):
    """
    Reads the specified JSON file (default: 'assessment_justification_agent_state.json'),
    finds the editor agent's final response, and extracts the
    substring from the first '{' to the last '}'.
    
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify the assessment_justification_agent key
    agent_name_to_find = "assessment_justification_agent"  # Exact agent name
    found_key = None
    if "agent_states" not in data or not isinstance(data["agent_states"], dict):
        print(f"Warning: 'agent_states' not found or not a dictionary in {file_path}.")
        return {}
        
    for key in data["agent_states"]:
        if key == agent_name_to_find:
            found_key = key
            break

    if not found_key:
        print(f"No key for agent '{agent_name_to_find}' found in agent_states of {file_path}.")
        return {}

    # 2. Get the agent state and retrieve the final message
    agent_state_data = data["agent_states"][found_key]
    if not isinstance(agent_state_data, dict) or "agent_state" not in agent_state_data or \
       not isinstance(agent_state_data["agent_state"], dict) or "llm_context" not in agent_state_data["agent_state"] or \
       not isinstance(agent_state_data["agent_state"]["llm_context"], dict) or "messages" not in agent_state_data["agent_state"]["llm_context"]:
        print(f"Unexpected structure for agent '{found_key}' state in {file_path}.")
        return {}
        
    messages = agent_state_data["agent_state"]["llm_context"]["messages"]
    if not messages or not isinstance(messages, list):
        print(f"No messages found or messages is not a list for agent '{found_key}' in {file_path}.")
        return {}

    final_message_obj = messages[-1]
    if not isinstance(final_message_obj, dict) or "content" not in final_message_obj:
        print(f"Final message for agent '{found_key}' has unexpected structure or no content in {file_path}.")
        return {}

    final_message = final_message_obj.get("content", "")
    if not final_message or not isinstance(final_message, str):
        print(f"Final message for agent '{found_key}' is empty or not a string in {file_path}.")
        return {}

    # 3. Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # 4. Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Failed to parse editor content as valid JSON.")
        return None

def extract_tsc_agent_json(file_path: str = "tsc_agent_state.json"):
    """
    Reads the specified JSON file (default: 'tsc_agent_state.json'),
    finds the editor agent's final response, and extracts the
    substring from the first '{' to the last '}'.
    
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Identify the tsc_agent key
    tsc_agent_name = "tsc_agent"  # Exact agent name
    found_key = None # Renamed from editor_key for clarity
    if "agent_states" not in data or not isinstance(data["agent_states"], dict):
        print(f"Warning: 'agent_states' not found or not a dictionary in {file_path}.")
        return {}

    for key in data["agent_states"]:
        if key == tsc_agent_name:
            found_key = key
            break

    if not found_key:
        print(f"No key for agent '{tsc_agent_name}' found in agent_states of {file_path}.") # Updated log message
        return {}

    # 2. Get the tsc_agent state and retrieve the final message
    agent_state_data = data["agent_states"][found_key] # Renamed from aggregator_state and editor_state
    if not isinstance(agent_state_data, dict) or "agent_state" not in agent_state_data or \
       not isinstance(agent_state_data["agent_state"], dict) or "llm_context" not in agent_state_data["agent_state"] or \
       not isinstance(agent_state_data["agent_state"]["llm_context"], dict) or "messages" not in agent_state_data["agent_state"]["llm_context"]:
        print(f"Unexpected structure for agent '{found_key}' state in {file_path}.")
        return {}

    messages = agent_state_data["agent_state"]["llm_context"]["messages"]
    if not messages or not isinstance(messages, list):
        print(f"No messages found or messages is not a list for agent '{found_key}' in {file_path}.") # Updated log message
        return {}

    final_message_obj = messages[-1]
    if not isinstance(final_message_obj, dict) or "content" not in final_message_obj:
        print(f"Final message for agent '{found_key}' has unexpected structure or no content in {file_path}.")
        return {}
        
    final_message = final_message_obj.get("content", "")
    if not final_message or not isinstance(final_message, str):
        print(f"Final message for agent '{found_key}' is empty or not a string in {file_path}.") # Updated log message
        return {}

    # Remove code block markers if present
    if final_message.startswith("```json"):
        final_message = final_message[len("```json"):].strip()
    if final_message.startswith("```"):
        final_message = final_message[len("```"):].strip()
    if final_message.endswith("```"):
        final_message = final_message[:-3].strip()

    # 3. Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print("No JSON braces found in the final aggregator message.")
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # 4. Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Failed to parse editor content as valid JSON.")
        print("Error:", e)
        print("String was:", repr(json_str))
        return None


# Function to recursively flatten lists within the JSON structure
def flatten_json(obj):
    if isinstance(obj, dict):
        # Recursively apply to dictionary values
        return {k: flatten_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Flatten the list and apply to each element in the list
        return flatten_list(obj)
    else:
        return obj

# Function to flatten any nested list
def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))  # Recursively flatten any nested lists
        else:
            flat_list.append(item)
    return flat_list

import json

def append_validation_output(
    ensemble_output_path: str = "ensemble_output.json",
    validation_output_path: str = "validation_output.json",
    analyst_responses: list = None
):
    """
    Reads data from `ensemble_output.json` and appends the new course information 
    into `validation_output.json`. If `validation_output.json` already exists, 
    it will append the new course data instead of overwriting it.

    Additionally, it allows appending `analyst_responses` as a list of dictionaries 
    containing responses about industry performance gaps and course impact.

    Structure:
    {
        "course_info": { Course Title, Industry, Learning Outcomes, TSC Title, TSC Code },
        "analyst_responses": [ {...}, {...} ]  # List of analyst responses
    }
    """

    # Load the existing data if the file exists, otherwise start fresh
    if os.path.exists(validation_output_path):
        with open(validation_output_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # Load ensemble_output.json
    with open(ensemble_output_path, "r", encoding="utf-8") as f:
        ensemble_data = json.load(f)

    # Extract required fields
    course_title = ensemble_data.get("Course Information", {}).get("Course Title", "")
    industry = ensemble_data.get("Course Information", {}).get("Industry", "")
    learning_outcomes = ensemble_data.get("Learning Outcomes", {}).get("Learning Outcomes", [])
    
    # Extract TSC Title and TSC Code (first element if list exists)
    tsc_titles = ensemble_data.get("TSC and Topics", {}).get("TSC Title", [])
    tsc_codes = ensemble_data.get("TSC and Topics", {}).get("TSC Code", [])

    tsc_title = tsc_titles[0] if tsc_titles else ""
    tsc_code = tsc_codes[0] if tsc_codes else ""

    # Build the course information dictionary
    new_course_info = {
        "Course Title": course_title,
        "Industry": industry,
        "Learning Outcomes": learning_outcomes,  # This is already a list
        "TSC Title": tsc_title,
        "TSC Code": tsc_code
    }

    # Update or append course_info
    existing_data["course_info"] = new_course_info

    # Handle analyst_responses (ensure it's a list in the final output)
    if analyst_responses:
        if "analyst_responses" not in existing_data:
            existing_data["analyst_responses"] = []
        existing_data["analyst_responses"].extend(analyst_responses)

    # Write back to validation_output.json
    with open(validation_output_path, "w", encoding="utf-8") as out_f:
        json.dump(existing_data, out_f, indent=2)

    print(f"Updated validation data saved to {validation_output_path}.")

def safe_json_loads(json_str):
    """Fix common JSON issues like unescaped quotes before parsing."""
    # Escape unescaped double quotes within strings
    json_str = re.sub(r'(?<!\\)"(?![:,}\]\s])', r'\"', json_str)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        return None

def load_json_file(file_path):
    """Loads JSON data from a file and ensures it is a list or dict."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if not isinstance(data, (list, dict)):
                print(f"Error: JSON loaded from '{file_path}' is not a list or dict, got {type(data)}")
                return None
            return data
    except FileNotFoundError:
        print(f"Error: JSON file not found at '{file_path}'")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file '{file_path}'. Please ensure it is valid JSON.")
        return None

def extract_lo_keys(json_data):
    """
    Extracts keys that match the pattern '#LO' followed by a number.

    Args:
        json_data (dict): The JSON data as a dictionary.

    Returns:
        list: A list of keys that match the pattern '#LO' followed by a number.
    """
    lo_keys = []
    pattern = re.compile(r'^#LO\d+$')
    for key in json_data.keys():
        print(f"Checking key: {key}")  # Debugging statement
        if pattern.match(key):
            print(f"Matched key: {key}")  # Debugging statement
            lo_keys.append(key)
    return lo_keys

def recursive_get_keys(json_data, key_prefix=""):
    """
    Extracts keys from a JSON dictionary that start with '#Topics' and returns them as a list.

    Args:
        json_data (dict): A dictionary loaded from a JSON file.

    Returns:
        list: A list of strings, where each string is a key from the json_data
              that starts with '#Topics'. For example: ['#Topics[0]', '#Topics[1]', '#Topics[2]', ...].
              Returns an empty list if no keys start with '#Topics'.
    """
    topic_keys = []
    for key in json_data.keys():
        # if key.startswith("#Topics"):
        if key.startswith(key_prefix):
            topic_keys.append(key)
    return topic_keys

def extract_agent_json(file_path: str, agent_name: str):
    """
    Reads the specified JSON file, finds the specified agent's final response,
    and extracts the substring from the first '{' to the last '}'.
    Attempts to parse the extracted substring as JSON, returning
    a Python dictionary. If parsing fails or if no final message
    is found, returns None.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Identify the agent key (support both new and old formats)
    agent_key = None
    for key in data.get("agent_states", {}):
        if key.startswith(f"{agent_name}/") or key == agent_name:
            agent_key = key
            break

    if not agent_key:
        print(f"No {agent_name} key found in agent_states.")
        return None

    # Get the agent state and retrieve the final message
    agent_state = data["agent_states"][agent_key]
    messages = agent_state["agent_state"]["llm_context"]["messages"]
    if not messages:
        print(f"No messages found under {agent_name} agent state.")
        return None

    final_message = messages[-1].get("content", "")
    if not final_message:
        print(f"Final {agent_name} message is empty.")
        return None

    # Remove code block markers if present
    if final_message.startswith("```json"):
        final_message = final_message[len("```json"):].strip()
    if final_message.startswith("```"):
        final_message = final_message[len("```"):].strip()
    if final_message.endswith("```"):
        final_message = final_message[:-3].strip()

    # Extract the substring from the first '{' to the last '}'
    start_index = final_message.find("{")
    end_index = final_message.rfind("}")
    if start_index == -1 or end_index == -1:
        print(f"No JSON braces found in the final {agent_name} message.")
        print("Message content was:", repr(final_message))
        return None

    json_str = final_message[start_index:end_index + 1].strip()

    # Parse the extracted substring as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse {agent_name} content as valid JSON.")
        print("Error:", e)
        print("String was:", repr(json_str))
        return None
