from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from CourseProposal.model_configs import get_model_config
from autogen_core.models import ChatCompletionClient

# planning team functions
# Planning team will create a retrieval plan on how to retrieve the information required to support the A and K factors. Perhaps limited to 5 key topics to be retrieved.


def planning_team_task(tsc_data):
    tsc_task = f"""
    1. Parse data from the following JSON file: {tsc_data}
    2. Evaluate and create a retrieval plan to support the Learning Outcome, A and K factors.
    3. Limit the retrieval plan to 5 key topics.
    4. Return a full JSON object with your suggestions according to the schema.
    """
    return tsc_task

def create_planning_team(tsc_data, model_choice: str) -> RoundRobinGroupChat:
    chosen_config = get_model_config(model_choice)
    model_client = ChatCompletionClient.load_component(chosen_config)

    planner_agent_message = f"""
        You are to create a retrieval plan to support the Learning Outcome, A and K factors from the following JSON file: {tsc_data}.
        This retrieval plan will be passed to the Retrieval team for selection of supporting information that will help address learning outcomes, and A and K factors.
        The requirements are as follows:
        1. Your retrieval plan must be concise, and summarises the Learning Outcome, A and K factors into no more than 5 different sentences. A search will be performed in the database based on those sentences.
        2. Ensure that the retrieval plan is clear and actionable, providing a roadmap for the Retrieval team to follow.
        3. Provide Keywords that will assist in the search.
        4. Return a full JSON object with your suggestions according to the schema.

        An example JSON schema looks like this:
        {{
        "Planning": {{
            "Retrieval Plan": [

            ],
            "Keywords": [

            ],
    }}
        }}
        """

    # planner_critic_message = f"""
    #     You are to evaluate the retrieval plan created by the Planning team from the following JSON file: {tsc_data}.
    #     Ensure that the retrieval plan is sound and actionable, providing a roadmap for the Retrieval team to follow.
    #     The requirements are as follows:
    #     1. 
    #     """

    planner_agent = AssistantAgent(
        name="planner_agent",
        model_client=model_client,
        system_message=planner_agent_message,
    )

    # tsc_prepper_agent = AssistantAgent(
    #     name="tsc_prepper_agent",
    #     model_client=model_client,
    #     system_message=tsc_parser_agent_message,
    # )

    planner_agent_response = RoundRobinGroupChat([planner_agent], max_turns=1)

    return planner_agent_response