from typing import Dict, List, Optional, TypedDict, Any
from langchain_core.messages import BaseMessage, ChatMessage, HumanMessage, SystemMessage


class AgentState(TypedDict):
    """State for the real estate poster template agent."""
    
    # Chat history
    messages: List[BaseMessage]
    
    # Current conversation status
    status: str
    
    # Template customization parameters
    template_params: Optional[Dict]
    
    # Generation result
    generation_result: Optional[Dict]
    
    # Selected template version (1, 2, or 3)
    template_version: int
    
    # Flag to force template generation
    force_generation: bool


def get_initial_state() -> AgentState:
    """Get the initial state for the real estate poster template agent."""
    return {
        "messages": [
            SystemMessage(content=(
                "You are a helpful real estate poster design assistant. "
                "You help users create customized real estate poster templates. "
                "You can create posters using three different templates. "
                "You will ask for details about their real estate listing and "
                "help them customize the poster design."
            )),
        ],
        "status": "WAITING_FOR_USER",
        "template_params": None,
        "generation_result": None,
        "template_version": 1,  # Default to template 1
        "force_generation": False,  # Don't force generation by default
    }