import json

# Load JSON files
with open('mapping_source.json') as f:
    mapping_source = json.load(f)

with open('ensemble_output.json') as f:
    ensemble_output = json.load(f)

with open('research_output.json') as f:
    research_output = json.load(f)

# Define the mapping rules
def map_values(mapping_source, ensemble_output, research_output):
    background_analysis = ""
    for key, value in research_output["Background Analysis"].items():
        background_analysis += f"{value.strip()}\n\n"  # Adding a new line at the end of each section
    mapping_source["#Placeholder[0]"] = [background_analysis.strip()]

    performance_analysis = ""
    performance_analysis += "Performance gaps were identified through survey forms distributed to external stakeholders:\n\n"

    # Iterate through the performance analysis
    for key, value in research_output["Performance Analysis"].items():
        if key == "Performance gaps":
            # Add bullet points for performance gaps
            performance_analysis += f"{key}:\n"
            if isinstance(value, list):
                # Indent and format each performance gap as a bullet point
                for item in value:
                    performance_analysis += f"• \t{item.strip()}\t\n"
            else:
                performance_analysis += f"• \t{value.strip()}\t\n"
            performance_analysis += "\n"  # Add space after bullet points

    performance_analysis += "Through targeted training programs, learners will gain the following attributes to address the identified performance gaps after the training:\n\n"

    for key, value in research_output["Performance Analysis"].items():
        if key == "Attributes gained":
            # Add bullet points for attributes gained
            performance_analysis += f"{key}:\n"
            if isinstance(value, list):
                # Indent and format each attribute gained as a bullet point
                for item in value:
                    performance_analysis += f"• \t{item.strip()}\t\n"
            else:
                performance_analysis += f"• \t{value.strip()}\t\n"
            performance_analysis += "\n"  # Add space after bullet points

    # Strip any leading or trailing spaces and assign to the placeholder
    mapping_source["#Placeholder[1]"] = [performance_analysis.strip()]

    # Map only the "Sequencing Explanation" to #Rationale[0]
    if "Sequencing Explanation" in research_output["Sequencing Analysis"]:
        mapping_source["#Rationale[0]"] = [research_output["Sequencing Analysis"]["Sequencing Explanation"]]

    # Mapping for Hours
    mapping_source["#Hours[0]"] = [ensemble_output["Course Information"]["Classroom Hours"]]
    mapping_source["#Hours[1]"] = [ensemble_output["Course Information"]["Number of Assessment Hours"]]
    mapping_source["#Hours[2]"] = [ensemble_output["Course Information"]["Course Duration (Number of Hours)"]]
    mapping_source["#Hours[3]"] = [ensemble_output["Assessment Methods"]["Amount of Practice Hours"]]

    mapping_source["#Conclusion[0]"] = [research_output["Sequencing Analysis"]["Conclusion"]]

    # Mapping for Course Title
    mapping_source["#CourseTitle"] = [ensemble_output["Course Information"]["Course Title"]]

    # Mapping for TSC
    mapping_source["#TCS[0]"] = [ensemble_output["TSC and Topics"]["TSC Title"]]
    mapping_source["#TCS[1]"] = [ensemble_output["TSC and Topics"]["TSC Code"]]

    # Mapping for Topics (iterating and appending sequentially)
    topics = ensemble_output["TSC and Topics"]["Topics"]
    for i, topic in enumerate(topics):
        mapping_source[f"#Topics[{i}]"] = [topic]  # Ensure each topic is mapped to the correct key

    # Mapping for Learning Outcomes
    learning_outcomes = ensemble_output["Learning Outcomes"]["Learning Outcomes"]
    for i, lo in enumerate(learning_outcomes):
        if f"#LO[{i}]" in mapping_source:
            mapping_source[f"#LO[{i}]"] = [lo]
    
    # Mapping for Learning Units
    learning_units = ensemble_output["TSC and Topics"]["Learning Units"]
    for i, lu in enumerate(learning_units):
        if f"#LU[{i}]" in mapping_source:
            mapping_source[f"#LU[{i}]"] = [lu]

    # Mapping for Learning Unit Descriptions (from research_output)
    for i in range(1, 6):  # LU1 to LU5
        lu_key = f"LU{i}"
        if lu_key in research_output["Sequencing Analysis"]:
            # Map the descriptions to #LUex[i]
            mapping_source[f"#LUex[{i-1}]"] = [research_output["Sequencing Analysis"][lu_key]["Description"]]

    # Mapping for Knowledge and Abilities
    knowledge = ensemble_output["Learning Outcomes"]["Knowledge"]
    abilities = ensemble_output["Learning Outcomes"]["Ability"]
    for i, (k, a) in enumerate(zip(knowledge, abilities)):
        if f"#K[{i}]" in mapping_source:
            mapping_source[f"#K[{i}]"] = [k]
        if f"#A[{i}]" in mapping_source:
            mapping_source[f"#A[{i}]"] = [a]

    # Mapping for KA (iterating and appending sequentially)
    ka_mappings = ensemble_output["Learning Outcomes"]["Knowledge and Ability Mapping"]
    for i, ka in enumerate(ka_mappings.values()):
        if f"#KA[{i}]" in mapping_source:
            mapping_source[f"#KA[{i}]"] = ka

    # Ensure any key with no mapping retains an empty list
    for key in mapping_source:
        if not mapping_source[key]:
            mapping_source[key] = []
    return mapping_source

# Apply the mapping
updated_mapping_source = map_values(mapping_source, ensemble_output, research_output)

# Output the updated mapping source for verification
print(json.dumps(updated_mapping_source, indent=4))

# Step 2: Save the parsed output to a JSON file
output_filename = 'generated_mapping.json'
try:
    with open(output_filename, 'w') as json_file:
        json.dump(updated_mapping_source, json_file, indent=4)
    print(f"Output saved to {output_filename}")
except IOError as e:
    print(f"Error saving JSON to file: {e}")
