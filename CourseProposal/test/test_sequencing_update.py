import json
import os
from CourseProposal.utils.excel_conversion_pipeline import write_json_file

def update_sequencing_rationale():
    # Load the current data
    with open('CourseProposal/json_output/generated_mapping.json', 'r') as f:
        data = json.load(f)
    
    # New template for sequencing rationale
    new_template = """For this course, the step-by-step sequencing is designed to align with the progressive development of an AI content creator's competencies, from understanding storytelling fundamentals to applying ethical guidelines. The structure supports learners in gradually building both conceptual and applied knowledge, starting from narrative basics and ending with ethical considerations. This logical flow ensures learners can contextualize AI storytelling techniques, implement visual storyboarding, create video content, and address ethical concerns in AI-generated media.

LU1: Storytelling with Generative AI
This foundational unit aligns with LO1 by introducing learners to the essential narrative aspects of AI content creation. Topics such as fundamentals of storytelling (T1), basic AI models for script generation (T2), and generating stories with generative AI (T4) equip learners with the baseline knowledge necessary to create compelling narrative content. The inclusion of practical exercises reinforces real-world application, anchoring theory in practice before learners move on to visual storytelling processes.

LU2: Storyboarding with Generative AI
Building on narrative knowledge, LU2 advances to LO2, focusing on visual storytelling through AI. Learners explore how to create effective storyboards (T1), identify key prompt terms (T2), and apply iterative approaches to image generation (T4). This unit emphasizes the storyboard as a key mechanism for translating narrative concepts into visual content. By understanding AI tool limitations and solutions (T3), learners learn to elevate their visual storytelling from basic concepts to polished visual narratives.

LU3: Creating AI Generated Video
LU3 addresses LO3, providing learners with a comprehensive view of AI video creation tools and techniques. It introduces AI video tools for generating text, voiceover and video (T1) and methods for creating AI video from storyboards (T2). Practical techniques for refining video scripts build on storytelling foundations laid in LU1 and LU2. This sequence ensures that learners are not only creating videos but doing so with attention to clarity, tone, and narrative consistency.

LU4: Generative AI Ethics and Best Practices
Culminating in LO4, this final unit shifts focus from creation to responsible practice. Learners synthesize knowledge from previous units to apply ethical considerations (T1), minimize plagiarism risk (T2), analyze AI output for bias (T3), and avoid copyright infringement (T4). By addressing these critical ethical issues, this unit prepares learners to take a responsible approach to AI content creation based on industry standards and legal requirements.

In summary, the curriculum is sequenced to support learner progression from understanding narrative concepts (LU1), to implementing visual storytelling (LU2), creating video content (LU3), and finally to applying ethical guidelines (LU4). This step-by-step structure ensures coherence between theoretical knowledge and practical application, leading to well-rounded AI content creators who can produce compelling, effective, and responsible media."""
    
    # Update the data
    data["#Sequencing_rationale"] = new_template
    
    # Write the updated data back to the file
    write_json_file(data, 'CourseProposal/json_output/generated_mapping.json')
    
    print("Sequencing rationale updated successfully!")

if __name__ == "__main__":
    update_sequencing_rationale() 