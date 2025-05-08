import json
import os
from CourseProposal.utils.excel_conversion_pipeline import write_json_file

def update_sequencing_rationale():
    # Load the current data
    with open('CourseProposal/json_output/generated_mapping.json', 'r') as f:
        data = json.load(f)
    
    # New template for sequencing rationale that doesn't mention Learning Outcomes
    new_template = """For this course, the step-by-step sequencing is designed to align with the progressive development of an AI content creator's competencies, from understanding storytelling fundamentals to applying ethical guidelines. The structure supports learners in gradually building both conceptual and applied knowledge, starting from narrative basics and ending with ethical considerations. This logical flow ensures learners can contextualize AI storytelling techniques, implement visual storyboarding, create video content, and address ethical concerns in AI-generated media.

LU1: Storytelling with Generative AI
This foundational unit introduces learners to the essential narrative aspects of AI content creation. Topics such as fundamentals of storytelling, basic AI models for script generation, and generating stories with generative AI equip learners with the baseline knowledge necessary to create compelling narrative content. The inclusion of practical exercises reinforces real-world application, anchoring theory in practice before learners move on to visual storytelling processes.

LU2: Storyboarding with Generative AI
Building on narrative knowledge, LU2 focuses on visual storytelling through AI. Learners explore how to create effective storyboards, identify key prompt terms, and apply iterative approaches to image generation. This unit emphasizes the storyboard as a key mechanism for translating narrative concepts into visual content. By understanding AI tool limitations and solutions, learners learn to elevate their visual storytelling from basic concepts to polished visual narratives.

LU3: Creating AI Generated Video
LU3 provides learners with a comprehensive view of AI video creation tools and techniques. It introduces AI video tools for generating text, voiceover and video and methods for creating AI video from storyboards. Practical techniques for refining video scripts build on storytelling foundations laid in LU1 and LU2. This sequence ensures that learners are not only creating videos but doing so with attention to clarity, tone, and narrative consistency.

LU4: Generative AI Ethics and Best Practices
Culminating the course, this final unit shifts focus from creation to responsible practice. Learners synthesize knowledge from previous units to apply ethical considerations, minimize plagiarism risk, analyze AI output for bias, and avoid copyright infringement. By addressing these critical ethical issues, this unit prepares learners to take a responsible approach to AI content creation based on industry standards and legal requirements.

In summary, the curriculum is sequenced to support learner progression from understanding narrative concepts (LU1), to implementing visual storytelling (LU2), creating video content (LU3), and finally to applying ethical guidelines (LU4). This step-by-step structure ensures coherence between theoretical knowledge and practical application, leading to well-rounded AI content creators who can produce compelling, effective, and responsible media."""
    
    # Update the sequencing data to fix issues in Excel output
    data["#Sequencing_rationale"] = new_template
    
    # Also update #Sequencing to match the format above, as it might be used as a source
    data["#Sequencing"] = """For this course, the step-by-step sequencing is employed to scaffold the learners' comprehension and application of storytelling and storyboarding using generative AI. The methodology is crucial as it systematically breaks down the intricate facets of AI-driven storytelling, storyboarding, video creation, and ethical considerations into digestible units. This aids in gradually building the learners' knowledge and skills from fundamental to more complex concepts, ensuring a solid foundation before advancing to the next topic. The progression is designed to foster a deeper understanding and the ability to effectively apply the learned concepts in real-world media scenarios.

LU1: Storytelling with Generative AI
LU1 lays the foundational knowledge by introducing learners to the core elements of storytelling and how generative AI can enhance script development. The facilitator will guide learners through the integration of creative principles into AI-generated text prompts, setting the stage for developing compelling narratives. This unit addresses the performance gap of using AI techniques to enrich script elements with narrative structure and creative storytelling, equipping learners with the ability to create engaging story ideas using AI tools.

LU2: Storyboarding with Generative AI
Building on the foundational knowledge, LU2 focuses on the practical aspects of storyboarding and the use of AI to generate visual content. Learners will be led through exercises to identify effective prompt terms and narrative components, enhancing their ability to create impactful AI-generated storyboards. This unit addresses the performance gap of identifying prompt terms and narrative components, providing learners with the proficiency to improve visual storytelling through AI-generated content.

LU3: Creating AI Generated Video
LU3 escalates to a higher level of complexity where learners delve into video script refinement using AI tools. Under the guidance of the facilitator, learners will engage in utilizing AI for generating text, voiceovers, and videos, thereby aligning theoretical knowledge with practical skills in video production. This unit addresses the performance gap of refining video scripts for clarity, tone, and narrative consistency, equipping learners with the skill to enhance video narratives using AI.

LU4: Generative AI Ethics and Best Practices
LU4 focuses on the ethical considerations and best practices in using generative AI. Learners will explore the ethical implications of AI-generated content, including bias, copyright risks, and plagiarism. This unit addresses the performance gap of analyzing AI outputs for ethical issues, providing learners with the competence to apply corrective actions and ensure ethical compliance in AI-generated media.

In summary, the curriculum is sequenced to support learner progression from understanding fundamental concepts to practical application, advanced techniques, and finally to ethical guidelines and best practices. This step-by-step approach ensures coherence between theoretical knowledge and practical application."""
    
    # Write the updated data back to the file
    write_json_file(data, 'CourseProposal/json_output/generated_mapping.json')
    
    print("Sequencing rationale updated successfully!")

if __name__ == "__main__":
    update_sequencing_rationale() 