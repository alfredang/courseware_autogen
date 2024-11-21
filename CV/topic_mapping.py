import json

# Sample JSON data (You can replace this with reading from a file)
json_data = '''

{
    "Course Information": {
        "Course Title": "Design Thinking and Agile Problem Solving",
        "Name of Organisation": "TRAINOCATE (S) PTE. LTD.",
        "Classroom Hours": 7,
        "Number of Assessment Hours": 2,
        "Course Duration (Number of Hours)": 16,
        "Industry": "Infocomm Technology"
    },
    "Learning Outcomes": {
        "Learning Outcomes": [
            "LO1: Articulate the principles of innovation, creativity, and design thinking processes to guide team members.",
            "LO2: Establish metrics to evaluate the outcomes of design ideas and prototypes through the stages of the design thinking process.",
            "LO3: Facilitate the application of design thinking processes and methodologies, emphasizing their importance to participants.",
            "LO4: Frame design concepts that align with organisational strategies.",
            "LO5: Promote agile principles as a design thinking tool to solve organisational challenges.",
            "LO6: Remove obstacles to implementing design thinking by integrating agile management principles.",
            "LO7: Equip stakeholders with the mindset to leverage design thinking approaches through case studies."
        ],
        "Knowledge": [
            "K1: Concept of design thinking",
            "K2: Importance of design thinking",
            "K3: Stages in the design thinking process",
            "K4: How design thinking is used in other organisations",
            "K5: Methods of applying design thinking for the organisation",
            "K6: Concept of innovation management"
        ],
        "Ability": [
            "A1: Articulate to team members the principles and concepts of innovation, creativity and design thinking processes.",
            "A2: Equip stakeholders with the mind set to develop design thinking approaches as strategies for creativity and innovation.",
            "A3: Facilitate the appropriate use of design thinking processes and methodologies by participants.",
            "A4: Establish metrics to measure outcomes of design ideas and prototypes.",
            "A5: Frame design concepts in alignment with the organisation's strategies and values.",
            "A6: Promote design thinking as a tool for solving problems and challenges for the organisation.",
            "A7: Remove obstacles and hindrances to implementing design thinking for the organisation."
        ],
        "Knowledge and Ability Mapping": {
            "KA1": [
                "A1, K1",
                "A2, K6"
            ],
            "KA2": [
                "A3, K2",
                "A4, K3"
            ],
            "KA3": [
                "A5, K4",
                "A6, K5",
                "A7, K5"
            ]
        }
    },
    "TSC and Topics": {
        "TSC Title": [
            "Design Thinking Practice"
        ],
        "TSC Code": [
            "ICT-ACE-4014-1.1"
        ],
        "Topics": [
            "Topic 1 Empathize and Define",
            "Topic 2 Ideate and Prototype",
            "Topic 3 Test and Iterate",
            "Topic 4 Introduction to Agile Principles",
            "Topic 5 Agile Planning and Execution",
            "Topic 6 Test, Review, and Adapt",
            "Topic 7 Case Studies and Real-World Applications"
        ],
        "Learning Units": [
            "LU1 Design Thinking Framework",
            "LU2 Agile Problem-Solving Framework for Design Thinking"
        ]
    },
    "Assessment Methods": {
        "Assessment Methods": [
            "Written Assessment",
            "Case Study"
        ],
        "Amount of Practice Hours": "N.A.",
        "Course Outline": {
            "Learning Units": {
                "LU1": {
                    "Description": [
                        {
                            "Topic": "Empathize and Define",
                            "Details": [
                                "Techniques for understanding user needs",
                                "Methods for defining clear problem statements",
                                "Exercises: Empathy mapping and problem definition"
                            ]
                        },
                        {
                            "Topic": "Ideate and Prototype",
                            "Details": [
                                "Strategies for brainstorming and generating creative solutions",
                                "Steps to create and refine prototypes",
                                "Activities: Brainstorming sessions and prototyping workshops"
                            ]
                        },
                        {
                            "Topic": "Test and Iterate",
                            "Details": [
                                "Importance of gathering user feedback",
                                "Methods for testing and iterating solutions",
                                "Workshops: Testing prototypes and iterative improvements"
                            ]
                        }
                    ]
                },
                "LU2": {
                    "Description": [
                        {
                            "Topic": "Introduction to Agile Principles",
                            "Details": [
                                "Core values and principles of Agile methodology",
                                "Benefits of Agile in problem-solving and project management",
                                "Discussion: Agile principles and their application"
                            ]
                        },
                        {
                            "Topic": "Agile Planning and Execution",
                            "Details": [
                                "Steps for effective Agile planning",
                                "Techniques for incremental development",
                                "Activities: Agile planning exercises and mock sprints"
                            ]
                        },
                        {
                            "Topic": "Test, Review, and Adapt",
                            "Details": [
                                "Methods for continuous testing and feedback collection",
                                "Strategies for iterative review and adaptation",
                                "Workshops: Testing solutions, reviewing progress, and adapting plans"
                            ]
                        },
                        {
                            "Topic": "Case Studies and Real-World Applications",
                            "Details": [
                                "Analysing successful problem-solving cases in the tech industry",
                                "Applying learned skills to hypothetical scenarios",
                                "Group Work: Case study analysis and presentations"
                            ]
                        }
                    ]
                }
            }
        }
    }
}
'''

# Load the JSON data
data = json.loads(json_data)

# Function to map Ks and As to Topics
def map_ka_to_topics(ka_mapping, topics_list, abilities, knowledge):
    topic_ka_map = {}
    ka_keys = list(ka_mapping.keys())
    topic_index = 0

    # Iterate over KA mappings and map them to topics
    for ka_key in ka_keys:
        for item in ka_mapping[ka_key]:
            a_k_pair = item.split(', ')
            ability_code = a_k_pair[0]
            knowledge_code = a_k_pair[1]
            topic = topics_list[topic_index]
            if topic not in topic_ka_map:
                topic_ka_map[topic] = {'A': [], 'K': []}
            topic_ka_map[topic]['A'].append(ability_code)
            topic_ka_map[topic]['K'].append(knowledge_code)
        topic_index += 1
    return topic_ka_map

# Extract Learning Outcomes, Knowledge, and Abilities
learning_outcomes = data['Learning Outcomes']['Learning Outcomes']
knowledge_list = data['Learning Outcomes']['Knowledge']
ability_list = data['Learning Outcomes']['Ability']
ka_mapping = data['Learning Outcomes']['Knowledge and Ability Mapping']

# Create dictionaries for quick lookup
knowledge_dict = {k.split(': ')[0]: k.split(': ')[1] for k in knowledge_list}
ability_dict = {a.split(': ')[0]: a.split(': ')[1] for a in ability_list}
lo_dict = {f"LO{index+1}": lo for index, lo in enumerate(learning_outcomes)}

# Extract Topics and Learning Units
learning_units = data['Assessment Methods']['Course Outline']['Learning Units']

# Get list of Topics per LU
lu_topics = {}
for lu_key, lu_content in learning_units.items():
    lu_topics[lu_key] = [topic_desc['Topic'] for topic_desc in lu_content['Description']]

# Map KA to Topics
topics_list = [topic for lu in lu_topics.values() for topic in lu]
topic_ka_map = map_ka_to_topics(ka_mapping, topics_list, ability_list, knowledge_list)

# Map LOs to Topics (Assuming one LO per topic in order)
lo_list = list(lo_dict.keys())
topic_lo_map = {}
for index, topic in enumerate(topics_list):
    if index < len(lo_list):
        topic_lo_map[topic] = lo_list[index]

# Generate the formatted output
for lu_key, lu_content in learning_units.items():
    lu_title = [lu for lu in data['TSC and Topics']['Learning Units'] if lu_key in lu][0]
    print(f"{lu_title}\tTopics:")
    for topic_desc in lu_content['Description']:
        topic = topic_desc['Topic']
        K_codes = ', '.join(topic_ka_map[topic]['K']) if topic in topic_ka_map else ''
        A_codes = ', '.join(topic_ka_map[topic]['A']) if topic in topic_ka_map else ''
        print(f"Topic {topics_list.index(topic)+1}: {topic} ({K_codes}, {A_codes})")
        for detail in topic_desc['Details']:
            print(f"• {detail}")
        # Print LO
        if topic in topic_lo_map:
            lo_code = topic_lo_map[topic]
            print(f"\n{lo_code} – {lo_dict[lo_code]}")
        # Print K and A descriptions
        if topic in topic_ka_map:
            for k_code in topic_ka_map[topic]['K']:
                print(f"{k_code}: {knowledge_dict[k_code]}")
            for a_code in topic_ka_map[topic]['A']:
                print(f"{a_code}: {ability_dict[a_code]}")
        print()
