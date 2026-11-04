# v2/src/core/llm.py
import os
import requests
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class ModelManager:
    def __init__(self):
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.current_model = os.getenv('DEFAULT_MODEL', 'llama3.1:8b')
        self.available_models = {}
        self.model_temperatures = {
            'creative': 0.8,
            'balanced': 0.5,
            'precise': 0.2
        }
        self.setup_model(self.current_model)
        
    def setup_model(self, model_name: str) -> bool:
        """Setup and verify a specific model"""
        try:
            # Check if model is available
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                available_model_names = [model['name'] for model in models_data.get('models', [])]
                
                if model_name in available_model_names:
                    self.current_model = model_name
                    self._load_available_models()
                    print(f"✅ Model switched to: {model_name}")
                    return True
                else:
                    print(f"❌ Model '{model_name}' not found. Available models: {available_model_names}")
                    return False
            else:
                print(f"❌ Cannot connect to Ollama at {self.ollama_base_url}")
                return False
                
        except Exception as e:
            print(f"❌ Model setup error: {e}")
            return False
    
    def _load_available_models(self):
        """Load available models with their descriptions"""
        self.available_models = {
            'llama3.1:8b': 'Meta Llama 3.1 8B - Fast, efficient general-purpose model',
            'llama3.1:70b': 'Meta Llama 3.1 70B - Powerful large model for complex tasks',
            'llama3.2:1b': 'Meta Llama 3.2 1B - Ultra-fast for simple tasks',
            'llama3.2:3b': 'Meta Llama 3.2 3B - Balanced speed and capability',
            'mistral:7b': 'Mistral 7B - Strong reasoning and coding',
            'codellama:7b': 'CodeLlama 7B - Specialized for programming',
            'phi3:mini': 'Phi-3 Mini - Compact but capable model',
            'gemma2:2b': 'Gemma 2 2B - Google\'s efficient model',
            'qwen2.5:0.5b': 'Qwen2.5 0.5B - Very fast, basic tasks'
        }
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of available models with descriptions"""
        if not self.available_models:
            self._load_available_models()
        return self.available_models
    
    def invoke_model(self, prompt: str, temperature: float = None, max_tokens: int = 2048) -> str:
        """Invoke the current model with a prompt"""
        if temperature is None:
            temperature = self.model_temperatures['balanced']
        
        try:
            payload = {
                "model": self.current_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"❌ Model error: {response.status_code} - {response.text}"
                
        except requests.exceptions.Timeout:
            return "⏰ Model request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return f"🔌 Cannot connect to Ollama at {self.ollama_base_url}. Please ensure Ollama is running."
        except Exception as e:
            return f"❌ Model invocation error: {e}"
