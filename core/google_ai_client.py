import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import json_repair
from threading import Lock
import google.generativeai as genai
from core.config_utils import load_key
from core.api_key_pool import api_key_pool
import time
from random import uniform

LOCK = Lock()
MIN_REQUEST_INTERVAL = 0.2  # 最小请求间隔500ms
MAX_RETRIES = 3  # 最大重试次数
BASE_WAIT_TIME = 2  # 基础等待时间（秒）
MAX_WAIT_TIME = 10  # 最大等待时间（秒）
_last_request_time = 0

def _wait_for_next_request():
    """确保请求间隔不小于MIN_REQUEST_INTERVAL"""
    global _last_request_time
    current_time = time.time()
    time_since_last_request = current_time - _last_request_time
    if time_since_last_request < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - time_since_last_request)
    _last_request_time = time.time()

def _exponential_backoff(attempt):
    """计算指数退避等待时间"""
    wait_time = min(BASE_WAIT_TIME * (2 ** attempt) + uniform(0, 1), MAX_WAIT_TIME)
    return wait_time

def initialize_google_ai():
    """Initialize Google AI API with configuration from config.yaml"""
    api_config = load_key("api")["google_ai"]
    if not api_config["enabled"]:
        return None
        
    if not all([api_config["model"], api_config["api_keys"]]):
        raise ValueError("⚠️ Google AI API configuration is incomplete")
    
    try:
        # 从密钥池获取下一个可用的API密钥
        api_key = api_key_pool.get_next_api_key()
        genai.configure(api_key=api_key)
        api_config["api_key"] = api_key
        return api_config
    except ValueError as e:
        raise ValueError(f"⚠️ Failed to get API key from pool: {str(e)}")

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
        for attempt in range(MAX_RETRIES):
            try:
                _wait_for_next_request()
                model = genai.GenerativeModel(api_config["model"])
                
                if response_json:
                    prompt = f"Please respond in JSON format only. {prompt}"
                    
                response = model.generate_content(prompt)
                
                if response_json:
                    try:
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
                error_msg = str(e)
                if "429" in error_msg or "Resource has been exhausted" in error_msg:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = _exponential_backoff(attempt)
                        print(f"⚠️ Rate limit exceeded. Retrying in {wait_time:.2f} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(wait_time)
                        continue
                raise Exception(f"❎ Google AI API error: {error_msg}")
if __name__ == "__main__":
    # 测试Google AI API
    try:
        # 测试初始化
        print("测试初始化 Google AI...")
        config = initialize_google_ai()
        print("初始化成功:", config)
        
        # 测试简单问答
        print("\n测试普通文本问答...")
        response = ask_google_ai("What is Python?", response_json=False)
        print("回答:", response)
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
