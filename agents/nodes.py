import re
import os
from typing import Dict, List, Tuple, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from agents.state import AgentState
from agents.tools import generate_real_estate_poster


def extract_template_preference(text: str) -> int:
    """
    Extract template preference from user message
    """
    # Check for explicit template selection with numbers
    template_match = re.search(r'(?:use|select|choose|prefer|want|generate|create|try)\s+(?:the\s+)?template\s+(\d)', text, re.IGNORECASE)
    if template_match:
        template_num = int(template_match.group(1))
        if 1 <= template_num <= 3:
            return template_num
    
    # Check for direct mention of template numbers
    template_number_match = re.search(r'template\s*(?:number|#)?\s*(\d)', text, re.IGNORECASE)
    if template_number_match:
        template_num = int(template_number_match.group(1))
        if 1 <= template_num <= 3:
            return template_num
    
    # Look for template descriptions
    if re.search(r'modern home|for sale|start from|buy now', text, re.IGNORECASE):
        return 1
    elif re.search(r'house agent|information|contact|technology|template 2', text, re.IGNORECASE):
        return 2
    elif re.search(r'best home|multiple photos|i want button|three images|template 3', text, re.IGNORECASE):
        return 3
    
    # Default to template 1 if no preference detected
    return 1


def extract_template_params(text: str, template_version: int = 1) -> Dict:
    """
    Extract template parameters from the user message based on the selected template.
    """
    params = {}
    
    # Look for image URL - improved to handle URLs starting with www.
    # First check for standard URLs with protocol
    image_url_match = re.search(r'(https?://\S+\.(jpg|jpeg|png|gif|webp))', text, re.IGNORECASE)
    
    # If no standard URL found, check for URLs starting with www.
    if not image_url_match:
        www_url_match = re.search(r'(www\.\S+\.(jpg|jpeg|png|gif|webp))', text, re.IGNORECASE)
        if www_url_match:
            params["image_url"] = "https://" + www_url_match.group(0)
    else:
        params["image_url"] = image_url_match.group(0)
    
    # If still no image URL with specific extensions, look for any URL with www
    if "image_url" not in params:
        general_url_match = re.search(r'(www\.\S+\.\w+)', text, re.IGNORECASE)
        if general_url_match:
            params["image_url"] = "https://" + general_url_match.group(0)
    
    # Extract parameters based on template version
    if template_version == 1:
        # Template 1 parameters
        # Improved price detection - check for explicit price modification patterns first
        price_modification_match = re.search(r'(?:modify|change|update|set|make)(?:\s+the)?\s+price\s+(?:to|as|be)\s+\$?([\d,.]+)', text, re.IGNORECASE)
        
        if price_modification_match:
            price = price_modification_match.group(1).replace(',', '')
            try:
                price_value = int(float(price))
                formatted_price = "${:,}".format(price_value)
                params["property_price"] = formatted_price
                print(f"Price modification detected: {formatted_price}")
            except ValueError:
                # If conversion fails, use the original matched text
                params["property_price"] = f"${price_modification_match.group(1)}"
        else:
            # Fall back to standard price detection if no modification pattern is found
            price_match = re.search(r'\$([\d,.]+)', text)
            if not price_match:
                # Try without the $ symbol
                price_match = re.search(r'(?:price|cost|value)[^\d]*(\d[\d,.]+)', text, re.IGNORECASE)
            
            if price_match:
                # Format the price with $ and commas
                price = price_match.group(1).replace(',', '')
                try:
                    price_value = int(float(price))
                    formatted_price = "${:,}".format(price_value)
                    params["property_price"] = formatted_price
                except ValueError:
                    # If conversion fails, use the original matched text
                    params["property_price"] = f"${price_match.group(1)}"
        
        # Look for text customizations
        text_matches = re.findall(r'([\w\s-]+) text should be "([^"]+)"', text)
        for element, content in text_matches:
            element_key = element.strip().lower()
            if element_key == "modern":
                params["modern_text"] = content
            elif element_key == "home":
                params["home_text"] = content
            elif element_key == "for sale":
                params["for_sale_text"] = content
            elif element_key == "start from":
                params["start_from_text"] = content
            elif element_key == "cta" or element_key == "buy now":
                params["cta_text"] = content
            elif element_key == "website":
                params["website_text"] = content
        
        # Look for color preferences
        color_matches = re.findall(r'([\w\s-]+) color should be ([#\w(),. ]+)', text)
        for element, color in color_matches:
            element_key = element.strip().lower()
            if element_key == "modern":
                params["modern_color"] = color.strip()
            elif element_key == "home":
                params["home_color"] = color.strip()
            elif element_key == "for sale":
                params["for_sale_color"] = color.strip()
            elif element_key == "start from":
                params["start_from_color"] = color.strip()
            elif element_key == "price":
                params["price_color"] = color.strip()
            elif element_key == "cta" or element_key == "buy now":
                params["cta_color"] = color.strip()
            elif element_key == "website":
                params["website_color"] = color.strip()
        
        # Also look for simplified color descriptions
        color_adjectives = {
            "yellow": "#FFD700",
            "red": "#FF0000",
            "blue": "#0000FF",
            "green": "#00FF00",
            "black": "#000000",
            "white": "#FFFFFF",
            "purple": "#800080",
            "orange": "#FFA500",
            "pink": "#FFC0CB",
            "brown": "#A52A2A",
            "gray": "#808080",
            "gold": "#FFD700"
        }
        
        for element, color in color_adjectives.items():
            if f"{element} buy now" in text.lower() or f"{element} button" in text.lower():
                params["cta_color"] = color
            if f"{element} modern" in text.lower():
                params["modern_color"] = color
            if f"{element} home" in text.lower():
                params["home_color"] = color
            if f"{element} for sale" in text.lower():
                params["for_sale_color"] = color
            if f"{element} price" in text.lower():
                params["price_color"] = color
            if f"{element} website" in text.lower():
                params["website_color"] = color
    
    elif template_version == 2:
        # Template 2 parameters
        # Look for text customizations
        if re.search(r'house agent\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["house_agent_text"] = re.search(r'house agent\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        if re.search(r'tagline\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["tagline_text"] = re.search(r'tagline\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        if re.search(r'info header\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["info_header_text"] = re.search(r'info header\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        if re.search(r'contact info\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["contact_info_text"] = re.search(r'contact info\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        # Look for color preferences
        if re.search(r'main text\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["text_1_color"] = re.search(r'main text\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
        
        if re.search(r'tagline\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["text_1_copy_color"] = re.search(r'tagline\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
        
        if re.search(r'info header\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["text_1_copy_copy_color"] = re.search(r'info header\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
        
        if re.search(r'contact info\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["text_1_copy_copy_copy_color"] = re.search(r'contact info\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
    
    elif template_version == 3:
        # Template 3 parameters
        # Look for secondary images
        secondary_images = re.findall(r'secondary image\s+(\d)\s+(https?://\S+\.\w+)', text, re.IGNORECASE)
        for img_num, img_url in secondary_images:
            if img_num == '1':
                params["secondary_image_url1"] = img_url
            elif img_num == '2':
                params["secondary_image_url2"] = img_url
            elif img_num == '3':
                params["secondary_image_url3"] = img_url
        
        # Look for text customizations
        if re.search(r'main title\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["title_1_text"] = re.search(r'main title\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        if re.search(r'second title\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["title_2_text"] = re.search(r'second title\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        if re.search(r'button\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["cta_button_text"] = re.search(r'button\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        if re.search(r'info\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["info_text"] = re.search(r'info\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        if re.search(r'website\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE):
            params["template3_website_text"] = re.search(r'website\s+text\s+["\']([^"\']+)["\']', text, re.IGNORECASE).group(1)
        
        # Look for color preferences
        if re.search(r'main title\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["title_1_color"] = re.search(r'main title\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
        
        if re.search(r'second title\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["title_2_color"] = re.search(r'second title\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
        
        if re.search(r'button\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["cta_color"] = re.search(r'button\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
        
        if re.search(r'info\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["info_color"] = re.search(r'info\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
        
        if re.search(r'website\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE):
            params["template3_website_color"] = re.search(r'website\s+color\s+([#\w(),. ]+)', text, re.IGNORECASE).group(1).strip()
    
    return params


def user_turn(state: AgentState) -> AgentState:
    """Process user input and update state accordingly."""
    # Get the last human message
    human_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    if not human_messages:
        return state
    
    last_message = human_messages[-1]
    
    # Check if user is selecting a template
    template_preference = extract_template_preference(last_message.content)
    if template_preference != state["template_version"]:
        # User changed template preference
        state["template_version"] = template_preference
        # Clear template params when template changes to avoid incompatibility
        state["template_params"] = {}
        state["status"] = "COLLECTING_INFO"
    
    # Track previous parameters to detect changes
    previous_params = state["template_params"].copy() if state["template_params"] else {}
    
    # Extract template parameters for the current template version
    extracted_params = extract_template_params(
        last_message.content,
        template_version=state["template_version"]
    )
    
    # Check for any direct price modifications in the message
    price_modification = False
    if state["template_version"] == 1:  # Only for template 1
        price_modification_pattern = re.search(r'(?:modify|change|update|set|make)(?:\s+the)?\s+price\s+(?:to|as|be)?\s+\$?([\d,.]+)', 
                                            last_message.content, re.IGNORECASE)
        if price_modification_pattern:
            price_modification = True
            price = price_modification_pattern.group(1).replace(',', '')
            try:
                price_value = int(float(price))
                formatted_price = "${:,}".format(price_value)
                extracted_params["property_price"] = formatted_price
                print(f"Direct price modification detected: {formatted_price}")
            except ValueError:
                pass
    
    # Update template parameters in state
    if state["template_params"] is None:
        state["template_params"] = extracted_params
    else:
        state["template_params"].update(extracted_params)
    
    # Check for parameter updates that require regeneration
    params_changed = False
    if extracted_params:
        for key, value in extracted_params.items():
            if key in previous_params and previous_params[key] != value:
                print(f"Parameter '{key}' changed from '{previous_params[key]}' to '{value}'")
                params_changed = True
                break
    
    # Check if this is a regeneration or update request
    regeneration_keywords = ["regenerate", "generate", "create", "update", "change", "modify", 
                           "make", "yes", "proceed", "go ahead", "do it", "new"]
    url_keywords = ["url", "link", "generated", "show me", "view", "preview", "see", "poster", "provide"]
    
    is_regeneration_request = any(keyword in last_message.content.lower() for keyword in regeneration_keywords)
    is_url_request = any(keyword in last_message.content.lower() for keyword in url_keywords)
    
    # Force regeneration if:
    # 1. User explicitly asked for regeneration/update OR
    # 2. Parameters changed and status is already READY_TO_GENERATE or TEMPLATE_GENERATED OR
    # 3. User is asking for a URL after updating parameters OR
    # 4. Direct price modification was detected
    if (((is_regeneration_request or is_url_request) and params_changed) or 
        (params_changed and state["status"] in ["READY_TO_GENERATE", "TEMPLATE_GENERATED"]) or
        price_modification):
        print(f"Forcing template regeneration due to parameter changes: {extracted_params}")
        state["force_generation"] = True
        # Clear previous generation result to ensure new one is created
        state["generation_result"] = None
    
    # Update status based on template version and user intent
    if state["template_version"] == 1:
        if "image_url" in state["template_params"] and "property_price" in state["template_params"]:
            state["status"] = "READY_TO_GENERATE"
            # Force generation for explicit requests or price modifications
            if is_regeneration_request or price_modification:
                state["force_generation"] = True
    elif state["template_version"] == 2:
        if "image_url" in state["template_params"]:
            state["status"] = "READY_TO_GENERATE"
            # Force generation for explicit requests
            if is_regeneration_request:
                state["force_generation"] = True
    elif state["template_version"] == 3:
        if "image_url" in state["template_params"]:
            state["status"] = "READY_TO_GENERATE"
            # Force generation for explicit requests
            if is_regeneration_request:
                state["force_generation"] = True
    else:
        # Default handling
        if "image_url" in state["template_params"]:
            state["status"] = "READY_TO_GENERATE"
    
    return state


def check_requirements(state: AgentState) -> AgentState:
    """Check if all necessary template parameters are available."""
    if state["template_params"] is None:
        state["status"] = "COLLECTING_INFO"
        return state
    
    # If force_generation is set, go directly to generate template
    if state.get("force_generation", False):
        state["status"] = "READY_TO_GENERATE"
        return state
    
    # Check for required parameters based on template version
    if state["template_version"] == 1:
        required_params = ["image_url", "property_price"]
    elif state["template_version"] == 2:
        required_params = ["image_url"]
    elif state["template_version"] == 3:
        required_params = ["image_url"]
    else:
        required_params = ["image_url"]
    
    missing_params = [param for param in required_params if param not in state["template_params"]]
    
    if missing_params:
        state["status"] = "COLLECTING_INFO"
    else:
        state["status"] = "READY_TO_GENERATE"
    
    return state


def ai_turn(state: AgentState) -> AgentState:
    """Generate AI response based on the current state."""
    # Initialize OpenAI chat model
    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create the prompt template
    system_template = """You are a helpful real estate poster design assistant.
You help users create customized real estate poster templates using three different templates:

Template 1: Modern Home - Includes labels like MODERN, HOME, FOR SALE, START FROM, price, and a BUY NOW button
Template 2: House Agent - Has sections for HOUSE AGENT, tagline, information header, and contact info
Template 3: Best Home - Features multiple images, title sections, and an "I WANT" button

Current template: Template {template_version}
Current status: {status}

{status_message}

Respond to the user in a friendly and helpful manner. Avoid technical jargon.
"""

    # Define status-specific instructions for each template
    status_messages = {
        # Template 1 status messages
        "1_COLLECTING_INFO": """You need to collect the following information for Template 1:
1. A URL to an image of the property (required)
2. The property price (required)
3. Any customizations for text and colors (optional)

Template 1 has these customizable elements:
- MODERN text and color
- HOME text and color
- FOR SALE text and color
- START FROM text and color
- Price text and color
- BUY NOW button text and color
- Website text and color

Ask the user about any missing information politely.""",

        "2_COLLECTING_INFO": """You need to collect the following information for Template 2:
1. A URL to an image of the property (required)
2. Any customizations for text and colors (optional)

Template 2 has these customizable elements:
- HOUSE AGENT text and color
- Tagline text and color (default: "modern | beautiful | technology")
- Information header text and color (default: "FOR MORE INFORMATION")
- Contact info text and color (default: "+123 456 7890 | www.lovehouse.com")

Ask the user about any missing information politely.""",

        "3_COLLECTING_INFO": """You need to collect the following information for Template 3:
1. A URL to the main image of the property (required)
2. URLs for up to three additional property images (optional)
3. Any customizations for text and colors (optional)

Template 3 has these customizable elements:
- Main title text and color (default: "THE BEST HOME")
- Second title text and color (default: "FOR SALE")
- Button text and color (default: "I WANT")
- Info text and color (default: "For more info, contact us")
- Website text and color (default: "www.housesforyou.com")

Ask the user about any missing information politely.""",

        "READY_TO_GENERATE": """You have all the necessary information to generate a poster template using Template {template_version}.
You can offer to generate the poster or ask if they want to make any other customizations.

Remember to mention that the user can switch to a different template by saying "Use Template 1/2/3" if they prefer.""",

        "TEMPLATE_GENERATED": """A poster template has been generated using Template {template_version}. The URL to view it is:
{template_url}

Ask if the user would like to make any changes or if they are satisfied with the result.
They can also try a different template by saying "Use Template 1/2/3"."""
    }

    status = state["status"]
    template_version = state["template_version"]
    
    # Get the appropriate status message based on template version and status
    status_message = ""
    if status == "COLLECTING_INFO":
        status_message = status_messages.get(f"{template_version}_COLLECTING_INFO", status_messages.get("1_COLLECTING_INFO"))
    elif status == "READY_TO_GENERATE":
        status_message = status_messages.get("READY_TO_GENERATE").format(template_version=template_version)
    elif status == "TEMPLATE_GENERATED":
        template_url = ""
        if state["generation_result"] and "url" in state["generation_result"]:
            template_url = state["generation_result"]["url"]
        status_message = status_messages.get("TEMPLATE_GENERATED").format(
            template_version=template_version,
            template_url=template_url
        )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template.format(
            template_version=template_version,
            status=status,
            status_message=status_message
        )),
        MessagesPlaceholder(variable_name="messages")
    ])

    # Generate AI response
    chain = prompt | model | StrOutputParser()
    ai_response = chain.invoke({"messages": state["messages"]})
    
    # Update message history
    state["messages"].append(AIMessage(content=ai_response))
    
    return state


def generate_template(state: AgentState) -> AgentState:
    """
    Generate a real estate template with the provided parameters
    """
    template_version = state["template_version"]
    template_params = state["template_params"].copy()  # Make a copy to avoid modifying original
    
    # Make sure we have the image_url parameter
    if "image_url" not in template_params or not template_params["image_url"]:
        # Show a more descriptive error message
        error_msg = "Cannot generate template: missing required image_url parameter."
        print(error_msg)
        
        # Update state to inform the user about the missing parameter
        state["messages"].append(
            SystemMessage(content="Error: Missing image URL. Please provide a URL to an image before generating the template.")
        )
        
        # Set status appropriately but preserve any parameters that were already collected
        state["status"] = "COLLECTING_INFO"
        return state
    
    # Always include template_version in parameters
    template_params["template_version"] = template_version
    
    print(f"Generating template with parameters:")
    for key, value in template_params.items():
        print(f"  {key}: {value}")
    
    try:
        # Generate the poster
        result = generate_real_estate_poster.invoke(template_params)
        state["generation_result"] = result
        state["status"] = "TEMPLATE_GENERATED"
        
        # If we get here, generation was successful
        print(f"Template generated successfully. URL: {result.get('url')}")
        return state
        
    except Exception as e:
        error_message = str(e)
        print(f"Error generating template: {error_message}")
        
        # If this is a validation error for image_url, provide more helpful information
        if "validation error" in error_message and "image_url" in error_message:
            # Add clearer message to the state
            state["messages"].append(
                SystemMessage(content="Error: An image URL is required. Please provide a URL to an image of the property.")
            )
        else:
            # General error
            state["messages"].append(
                SystemMessage(content=f"Error generating template: {error_message}")
            )
        
        # Don't lose any parameters already collected
        state["status"] = "COLLECTING_INFO"
        return state