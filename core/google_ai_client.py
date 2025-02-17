import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import json_repair
from threading import Lock
import google.generativeai as genai
from core.config_utils import load_key

LOCK = Lock()

def initialize_google_ai():
    """Initialize Google AI API with configuration from config.yaml"""
    api_config = load_key("api")["google_ai"]
    if not api_config["enabled"]:
        return None
        
    if not all([api_config["api_key"], api_config["project_id"], api_config["location"]]):
        raise ValueError("⚠️ Google AI API configuration is incomplete")
        
    genai.configure(api_key=api_config["api_key"])
    return api_config

def ask_google_ai(prompt, response_json=True, valid_def=None):
    """Send request to Google AI API
    
    Args:
        prompt (str): The prompt to send to the API
        response_json (bool): Whether to expect a JSON response
        valid_def (callable): Function to validate the response
        
    Returns:
        dict or str: The API response
    """
    api_config = initialize_google_ai()
    if not api_config:
        raise ValueError("⚠️ Google AI API is not enabled")
        
    with LOCK:
        try:
            model = genai.GenerativeModel(api_config["model"])
            
            if response_json:
                prompt = f"Please respond in JSON format only. {prompt}"
                
            response = model.generate_content(prompt)
            
            if response_json:
                try:
                    # 使用 json_repair 来处理可能的 JSON 格式问题
                    response_data = json_repair.loads(response.text)
                    if valid_def:
                        valid_response = valid_def(response_data)
                        if valid_response['status'] != 'success':
                            raise ValueError(f"❎ API response error: {valid_response['message']}")
                    return response_data
                except Exception as e:
                    raise ValueError(f"❎ Failed to parse JSON response: {str(e)}\nResponse text: {response.text}")
            
            return response.text
            
        except Exception as e:
            raise Exception(f"❎ Google AI API error: {str(e)}")