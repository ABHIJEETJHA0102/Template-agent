import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

class TemplateRenderer:
    """Utility class to interact with the Templated.io API for poster generation"""
    
    def __init__(self, template_version: int = 1):
        """
        Initialize the template renderer
        
        Args:
            template_version (int): Which template version to use (1, 2, or 3)
        """
        self.api_key = os.getenv('TEMPLATED_API_KEY')
        self.template_id1 = os.getenv('TEMPLATED_TEMPLATE_ID1')
        self.template_id2 = os.getenv('TEMPLATED_TEMPLATE_ID2')
        self.template_id3 = os.getenv('TEMPLATED_TEMPLATE_ID3')
        self.url = 'https://api.templated.io/v1/render'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        self.template_version = template_version
    
    def get_template_id(self) -> str:
        """Get the template ID for the current template version"""
        if self.template_version == 1:
            return self.template_id1
        elif self.template_version == 2:
            return self.template_id2
        elif self.template_version == 3:
            return self.template_id3
        else:
            # Default to template 1
            return self.template_id1
    
    def get_template_structure(self) -> Dict[str, Any]:
        """Get the template structure for the current template version"""
        if self.template_version == 1:
            return {
                'image-1': {'image_url': ''},
                'bg-website': {},
                'website': {'text': 'www.house4you.com', 'color': '#FFFFFF'},
                'shape-bg': {},
                'modern': {'text': 'MODERN', 'color': 'rgb(171, 102, 49)'},
                'home': {'text': 'HOME', 'color': 'rgb(59, 59, 59)'},
                'for sale': {'text': 'FOR SALE', 'color': 'rgb(59, 59, 59)'},
                'start from': {'text': 'START FROM', 'color': 'rgb(59, 59, 59)'},
                'price': {'text': '$0', 'color': 'rgb(59, 59, 59)'},
                'button-cta': {'text': 'BUY NOW', 'color': 'rgb(228, 228, 222)'}
            }
        elif self.template_version == 2:
            return {
                'image-1': {'image_url': ''},
                'shape-1': {},
                'shape-2': {},
                'text-1': {'text': 'HOUSE AGENT', 'color': '#FFFFFF'},
                'text-1-copy': {'text': 'modern | beautiful | technology', 'color': '#FFFFFF'},
                'text-1-copy-copy': {'text': 'FOR MORE INFORMATION', 'color': 'rgb(105, 99, 65)'},
                'shape-3': {},
                'text-1-copy-copy-copy': {'text': '+123 456 7890 | www.lovehouse.com', 'color': 'rgb(105, 99, 65)'}
            }
        elif self.template_version == 3:
            return {
                'image-top': {'image_url': ''},
                'photo-1': {'image_url': ''},
                'photo-2': {'image_url': ''},
                'photo-3': {'image_url': ''},
                'shape-1': {},
                'title-1': {'text': 'THE BEST HOME', 'color': 'rgb(239, 233, 226)'},
                'title-2': {'text': 'FOR SALE', 'color': 'rgb(239, 233, 226)'},
                'button-cta': {'text': 'I WANT', 'color': 'rgb(255, 255, 255)'},
                'info': {'text': 'For more info, contact us', 'color': 'rgb(126, 103, 76)'},
                'website': {'text': 'www.housesforyou.com', 'color': 'rgb(0, 0, 0)'}
            }
        else:
            # Default to template 1
            return self.get_template_structure(template_version=1)
    
    def set_template_version(self, version: int) -> None:
        """
        Change the template version
        
        Args:
            version (int): Template version (1, 2, or 3)
        """
        if version in [1, 2, 3]:
            self.template_version = version
        else:
            self.template_version = 1 
    
    def render_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render a template with customized data
        
        Args:
            template_data (dict): Dictionary containing layer customizations for the template
            
        Returns:
            dict: Response from the Templated.io API with the render details
        """
        if not self.api_key or not self.get_template_id():
            raise ValueError("Missing API key or template ID. Please check your .env file.")
        
        # Debug output to help diagnose API issues
        print(f"Rendering template version {self.template_version}")
        print(f"Template ID: {self.get_template_id()}")
        
        # Check image URL which is often a source of issues
        image_key = 'image-1' if self.template_version in [1, 2] else 'image-top'
        image_url = template_data.get(image_key, {}).get('image_url', 'Missing image URL')
        print(f"Image URL: {image_url}")
        
        # Check for placeholder API keys - for development/testing environment
        if self.api_key == "your_templated_api_key_here" or self.get_template_id() == "your_template_id_here":
            print("WARNING: Using development/testing mode with placeholder API keys")
            # Return a mock response during development
            mock_image_url = template_data.get('image-1', {}).get('image_url', '')
            if not mock_image_url and self.template_version == 3:
                mock_image_url = template_data.get('image-top', {}).get('image_url', '')
            
            # Return a demo URL for testing purposes
            return {
                "url": "https://example.com/poster-preview.jpg",
                "status": "success",
                "template_id": self.get_template_id(),
                "template_version": self.template_version,
                "original_image": mock_image_url,
                "mock_generation": True  # Flag to indicate this is a mock response
            }
        
        # Prepare the request data
        data = {
            'template': self.get_template_id(),
            'layers': template_data
        }
        
        print("Sending API request to templated.io...")
        try:
            response = requests.post(self.url, json=data, headers=self.headers)
            print(f"API response status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Template generated successfully. URL: {result.get('url', 'No URL in response')}")
                return result
            else:
                error_message = f"Render request failed. Response code: {response.status_code}"
                try:
                    error_details = response.text
                    error_message += f"\nDetails: {error_details}"
                except:
                    pass
                
                print(error_message)
                raise Exception(error_message)
        except Exception as e:
            print(f"Exception during API call: {str(e)}")
            raise