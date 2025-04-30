from typing import Annotated, TypedDict, Dict
from langgraph.graph import StateGraph, START, END
from agents.state import AgentState, get_initial_state
from agents.nodes import user_turn, check_requirements, generate_template, ai_turn

def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph workflow for the real estate poster template agent.
    
    The workflow:
    1. Process user input
    2. Check if all requirements are met for template generation
    3. Generate template if requirements are met
    4. Generate AI response
    5. Wait for next user input or end
    """
    # Create a new graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("user_turn", user_turn)
    workflow.add_node("check_requirements", check_requirements)
    workflow.add_node("generate_template", generate_template)
    workflow.add_node("ai_turn", ai_turn)
    
    # Define the flow
    workflow.add_edge(START, "user_turn")
    workflow.add_edge("user_turn", "check_requirements")
    
    # Improved conditional routing to ensure generation happens
    workflow.add_conditional_edges(
        "check_requirements",
        # Fixed conditional logic to properly route based on force_generation flag
        lambda state: (
            "generate_template" 
            if state["status"] == "READY_TO_GENERATE" or state.get("force_generation", False)
            else "ai_turn"
        ),
        {
            "generate_template": "generate_template",
            "ai_turn": "ai_turn"
        }
    )
    
    workflow.add_edge("generate_template", "ai_turn")
    workflow.add_edge("ai_turn", END)
    
    return workflow.compile()