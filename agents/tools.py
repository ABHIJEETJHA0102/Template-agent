from langchain_core.tools import tool
from utils.template_renderer import TemplateRenderer
from typing import Dict, Any, Optional

# Initialize a default renderer
default_renderer = TemplateRenderer(template_version=1)

@tool
def generate_real_estate_poster(
    template_version: int,
    image_url: str,
    # Template 1 specific parameters
    property_price: Optional[str] = None,
    modern_text: Optional[str] = None,
    home_text: Optional[str] = None,
    for_sale_text: Optional[str] = None,
    start_from_text: Optional[str] = None,
    cta_text: Optional[str] = None,
    website_text: Optional[str] = None,
    modern_color: Optional[str] = None,
    home_color: Optional[str] = None,
    for_sale_color: Optional[str] = None,
    start_from_color: Optional[str] = None,
    price_color: Optional[str] = None,
    cta_color: Optional[str] = None,
    website_color: Optional[str] = None,
    # Template 2 specific parameters
    house_agent_text: Optional[str] = None,
    tagline_text: Optional[str] = None,
    info_header_text: Optional[str] = None,
    contact_info_text: Optional[str] = None,
    text_1_color: Optional[str] = None,
    text_1_copy_color: Optional[str] = None,
    text_1_copy_copy_color: Optional[str] = None,
    text_1_copy_copy_copy_color: Optional[str] = None,
    # Template 3 specific parameters
    secondary_image_url1: Optional[str] = None,
    secondary_image_url2: Optional[str] = None,
    secondary_image_url3: Optional[str] = None,
    title_1_text: Optional[str] = None,
    title_2_text: Optional[str] = None,
    cta_button_text: Optional[str] = None,
    info_text: Optional[str] = None,
    template3_website_text: Optional[str] = None,
    title_1_color: Optional[str] = None,
    title_2_color: Optional[str] = None,
    info_color: Optional[str] = None,
    template3_website_color: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a real estate poster template with customized content."""
    # Create a template renderer with the specified version
    renderer = TemplateRenderer(template_version=template_version)
    
    # Get the base template structure
    template_data = renderer.get_template_structure()
    
    try:
        print(f"Creating poster for template_version={template_version}")
        print(f"Using image_url={image_url}")
        
        # Update the template data based on the template version
        if template_version == 1:
            # Template 1 parameters
            template_data['image-1']['image_url'] = image_url
            
            if property_price:
                print(f"Setting property price: {property_price}")
                template_data['price']['text'] = property_price
            if modern_text:
                template_data['modern']['text'] = modern_text
            if home_text:
                template_data['home']['text'] = home_text
            if for_sale_text:
                template_data['for sale']['text'] = for_sale_text
            if start_from_text:
                template_data['start from']['text'] = start_from_text
            if cta_text:
                template_data['button-cta']['text'] = cta_text
            if website_text:
                template_data['website']['text'] = website_text
            if modern_color:
                template_data['modern']['color'] = modern_color
            if home_color:
                template_data['home']['color'] = home_color
            if for_sale_color:
                template_data['for sale']['color'] = for_sale_color
            if start_from_color:
                template_data['start from']['color'] = start_from_color
            if price_color:
                template_data['price']['color'] = price_color
            if cta_color:
                print(f"Setting CTA color: {cta_color}")
                template_data['button-cta']['color'] = cta_color
            if website_color:
                template_data['website']['color'] = website_color
        
        elif template_version == 2:
            # Template 2 parameters
            template_data['image-1']['image_url'] = image_url
            
            if house_agent_text:
                template_data['text-1']['text'] = house_agent_text
            if tagline_text:
                template_data['text-1-copy']['text'] = tagline_text
            if info_header_text:
                template_data['text-1-copy-copy']['text'] = info_header_text
            if contact_info_text:
                template_data['text-1-copy-copy-copy']['text'] = contact_info_text
            if text_1_color:
                template_data['text-1']['color'] = text_1_color
            if text_1_copy_color:
                template_data['text-1-copy']['color'] = text_1_copy_color
            if text_1_copy_copy_color:
                template_data['text-1-copy-copy']['color'] = text_1_copy_copy_color
            if text_1_copy_copy_copy_color:
                template_data['text-1-copy-copy-copy']['color'] = text_1_copy_copy_copy_color
        
        elif template_version == 3:
            # Template 3 parameters
            template_data['image-top']['image_url'] = image_url
            
            # Set secondary images if provided, otherwise use the main image
            template_data['photo-1']['image_url'] = secondary_image_url1 or image_url
            template_data['photo-2']['image_url'] = secondary_image_url2 or image_url
            template_data['photo-3']['image_url'] = secondary_image_url3 or image_url
            
            if title_1_text:
                template_data['title-1']['text'] = title_1_text
            if title_2_text:
                template_data['title-2']['text'] = title_2_text
            if cta_button_text:
                template_data['button-cta']['text'] = cta_button_text
            if info_text:
                template_data['info']['text'] = info_text
            if template3_website_text:
                template_data['website']['text'] = template3_website_text
            if title_1_color:
                template_data['title-1']['color'] = title_1_color
            if title_2_color:
                template_data['title-2']['color'] = title_2_color
            if info_color:
                template_data['info']['color'] = info_color
            if template3_website_color:
                template_data['website']['color'] = template3_website_color
        
        # Render the template and return the result
        print("Rendering template...")
        result = renderer.render_template(template_data)
        print(f"Template rendering complete: {result.get('url', 'No URL returned')}")
        return result
        
    except Exception as e:
        import traceback
        print(f"Error in generate_real_estate_poster: {str(e)}")
        print(traceback.format_exc())
        # Re-raise to ensure the error is properly handled
        raise