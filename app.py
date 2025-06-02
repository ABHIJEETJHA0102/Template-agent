import os
import sys
import uuid
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv


from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agents import create_agent_graph
from agents.state import get_initial_state, AgentState

from agents.nodes import extract_template_preference, generate_template 

# Load environment variables
load_dotenv()

# Create FastAPI app first, so health endpoint works even if imports fail
app = FastAPI(
    title="Real Estate Poster Template Agent API",
    description="API for creating customized real estate poster templates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define template image placeholder URLs
TEMPLATE_PLACEHOLDER_IMAGES = {
    1: "https://example.com/templates/modern_home_preview.jpg",
    2: "https://example.com/templates/house_agent_preview.jpg",
    3: "https://example.com/templates/best_home_preview.jpg",
}

# Create the agent graph
agent = create_agent_graph()

# Session storage
sessions: Dict[str, AgentState] = {}

# Define request and response models
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_prompt: str
    template_version: Optional[int] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    status: str
    template_version: int

def get_templates() -> List[Dict]:
    """Get information about available templates"""
    templates = [
        {
            "id": 1,
            "name": "Modern Home",
            "description": "Classic real estate poster with modern design elements",
            "preview_url": TEMPLATE_PLACEHOLDER_IMAGES[1],
            "customizable_elements": [
                "image_url", "property_price", "modern_text", "home_text", 
                "for_sale_text", "start_from_text", "cta_text", "website_text",
                "modern_color", "home_color", "for_sale_color", "start_from_color", 
                "price_color", "cta_color", "website_color"
            ],
            "required_elements": ["image_url", "property_price"]
        },
        {
            "id": 2,
            "name": "House Agent",
            "description": "Professional real estate agent focused template",
            "preview_url": TEMPLATE_PLACEHOLDER_IMAGES[2],
            "customizable_elements": [
                "image_url", "house_agent_text", "tagline_text", "info_header_text", 
                "contact_info_text", "text_1_color", "text_1_copy_color",
                "text_1_copy_copy_color", "text_1_copy_copy_copy_color"
            ],
            "required_elements": ["image_url"]
        },
        {
            "id": 3,
            "name": "Best Home",
            "description": "Multi-image template with prominent call-to-action",
            "preview_url": TEMPLATE_PLACEHOLDER_IMAGES[3],
            "customizable_elements": [
                "image_url", "secondary_image_url1", "secondary_image_url2", "secondary_image_url3",
                "title_1_text", "title_2_text", "cta_button_text", "info_text", "template3_website_text",
                "title_1_color", "title_2_color", "info_color", "template3_website_color"
            ],
            "required_elements": ["image_url"]
        }
    ]
    return templates

def create_template_introduction() -> str:
    """Create a welcome message introducing available templates"""
    templates = get_templates()
    welcome_msg = "👋 Welcome! I can help you create real estate poster templates. Here are the templates I can work with:\n\n"
    
    for template in templates:
        welcome_msg += f"📌 Template {template['id']}: {template['name']}\n"
        welcome_msg += f"   {template['description']}\n"
        welcome_msg += f"   Preview: {template['preview_url']}\n\n"
    
    welcome_msg += "Please select a template number (1, 2, or 3) to get started, or tell me more about what you're looking for!"
    return welcome_msg

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process a chat message and return the agent's response"""
    # Get or create session
    if request.session_id in sessions:
        state = sessions[request.session_id]
        session_id = request.session_id
    else:
        session_id = request.session_id or str(uuid.uuid4())
        state = get_initial_state()
        
        # Add welcome message for new sessions
        welcome_message = create_template_introduction()
        state["messages"].append(SystemMessage(content=f"Start the conversation by introducing yourself and providing the following template information: {welcome_message}"))
        
        sessions[session_id] = state
    
    # Check if template is explicitly mentioned in the request query
    template_from_query = extract_template_preference(request.user_prompt)
    requested_template = request.template_version if request.template_version else template_from_query
    
    # Handle template switching if needed
    template_switched = False
    if requested_template and 1 <= requested_template <= 3 and state["template_version"] != requested_template:
        print(f"Switching from Template {state['template_version']} to Template {requested_template}")
        # Save image URL before clearing template params
        image_url = None
        if state["template_params"] and "image_url" in state["template_params"]:
            image_url = state["template_params"]["image_url"]
        
        # Update template version
        state["template_version"] = requested_template
        
        # Clear params but preserve image URL if available
        state["template_params"] = {}
        if image_url:
            state["template_params"]["image_url"] = image_url
            print(f"Preserved image URL during template switch: {image_url}")
            
        state["status"] = "COLLECTING_INFO"
        state["generation_result"] = None  # Clear previous generation
        state["force_generation"] = True   # Force regeneration with new template
        template_switched = True
        
        # Add a system message about the template change
        state["messages"].append(
            SystemMessage(content=f"User has switched to Template {requested_template}.")
        )
    
    # Add user message to state
    state["messages"].append(HumanMessage(content=request.user_prompt))
    
    try:
        # Check if this is a generation request
        generation_keywords = ["generate", "create", "make", "produce", "build", "design"]
        is_generation_request = any(keyword in request.user_prompt.lower() for keyword in generation_keywords)
        
        # Check if this is a URL request or asking for results
        url_keywords = ["url", "link", "generated", "show me", "view", "preview", "see", "poster", "provide"]
        is_url_request = any(keyword in request.user_prompt.lower() for keyword in url_keywords)
        
        # Force generation
        if ((is_generation_request or is_url_request) and state["status"] == "READY_TO_GENERATE") or template_switched:
            state["messages"].append(
                SystemMessage(content=f"The user has requested template generation using Template {state['template_version']}.")
            )
            # Run the generate template step explicitly
            try:
                state = generate_template(state)
                
                # Ensure state is correctly updated for template generation
                if state["generation_result"] and "url" in state["generation_result"]:
                    state["status"] = "TEMPLATE_GENERATED"
                    poster_url = state["generation_result"]["url"]
                    
                    # Check if this is a mock generation
                    is_mock = state["generation_result"].get("mock_generation", False)
                    mock_note = " (This is a preview since you're using development API keys)" if is_mock else ""
                    
                    # Add system message with URL for the agent to see
                    state["messages"].append(
                        SystemMessage(content=f"Template {state['template_version']} generated successfully. URL: {poster_url}{mock_note}")
                    )
                else:
                    # Add error message
                    state["messages"].append(
                        SystemMessage(content=f"Failed to generate template {state['template_version']}: No URL returned from generation service.")
                    )
            except Exception as e:
                # Add error details for the agent
                state["messages"].append(
                    SystemMessage(content=f"Error during template generation: {str(e)}")
                )
        
        # If the user is asking for a URL and we already have one, make sure they get it
        elif is_url_request and state["generation_result"] and "url" in state["generation_result"]:
            poster_url = state["generation_result"]["url"]
            is_mock = state["generation_result"].get("mock_generation", False)
            mock_note = " (This is a preview since you're using development API keys)" if is_mock else ""
            
            # Make sure the agent knows to include the URL
            state["messages"].append(
                SystemMessage(content=f"The user is asking for the poster URL for Template {state['template_version']}. Here it is: {poster_url}{mock_note}")
            )
        
        # Process the input through the agent workflow
        new_state = agent.invoke(state)
        sessions[session_id] = new_state
        
        # Get AI response
        ai_message = new_state["messages"][-1]
        
        return ChatResponse(
            session_id=session_id,
            response=ai_message.content,
            status=new_state["status"],
            template_version=new_state["template_version"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/templates")
async def templates_endpoint():
    """Get information about available templates"""
    return {"templates": get_templates()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)