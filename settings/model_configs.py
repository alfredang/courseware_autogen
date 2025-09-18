"""
Centralized Model Configuration Module

This module manages all AI model configurations for the Courseware AutoGen system.
It provides a unified interface for accessing different model configurations across
all modules (CourseProposal, Assessment, Courseware, etc.).

Author: Derrick Lim
Date: 3 March 2025
"""

import streamlit as st
from typing import Dict, Any

# Get API keys from the new API management system
from settings.api_manager import load_api_keys

api_keys = load_api_keys()
OPENAI_API_KEY = api_keys.get("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = api_keys.get("DEEPSEEK_API_KEY", "")
GEMINI_API_KEY = api_keys.get("ALFRED_GEMINI_API_KEY", api_keys.get("GEMINI_API_KEY", ""))
OPENROUTER_API_KEY = api_keys.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY = api_keys.get("GROQ_API_KEY", "")
GROK_API_KEY = api_keys.get("GROK_API_KEY", "")

# Gemini 2.5 Pro (Default for all modules - superior content generation)
default_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "gemini-2.5-pro",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": GEMINI_API_KEY,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        },
        "llama_name": "gemini-2.0-flash-001",
        "text_embedding_model": "model/text-embedding-005"
    }
}

# GPT-4o
gpt_4o_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "gpt-4o",
        "api_key": OPENAI_API_KEY,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "model_info": {
            "family": "openai",
            "function_calling": True,
            "json_output": True,
            "vision": True
        }
    }
}


# GPT-5
gpt_5_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "gpt-5",
        "api_key": OPENAI_API_KEY,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "model_info": {
            "family": "openai",
            "function_calling": True,
            "json_output": True,
            "vision": True
        }
    }
}

# GPT-4o-Mini
gpt_4o_mini_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "gpt-4o-mini",
        "api_key": OPENAI_API_KEY,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "model_info": {
            "family": "openai",
            "function_calling": True,
            "json_output": True,
            "vision": False
        }
    }
}

# GPT o3-mini
gpt_o3_mini_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "o3-mini",
        "api_key": OPENAI_API_KEY,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "model_info": {
            "family": "openai",
            "function_calling": True,
            "json_output": True,
            "vision": False
        }
    }
}

# DeepSeek-V3.1
deepseek_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "api_key": DEEPSEEK_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": False,
            "vision": False
        }
    }
}

# Gemini 2.5 Flash
gemini_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "gemini-2.5-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": GEMINI_API_KEY,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# Gemini 2.5 Pro (Default for Assessment/Courseware - superior content generation)
gemini_pro_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "gemini-2.5-pro",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": GEMINI_API_KEY,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        },
        "llama_name": "gemini-2.0-flash-001",
        "text_embedding_model": "model/text-embedding-005"
    }
}

# OpenRouter DeepSeek
openrouter_deepseek_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "deepseek-chat",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# OpenRouter Llama4
openrouter_llama4_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "meta-llama/llama-3.2-90b-vision-instruct",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": True
        }
    }
}

# Groq DeepSeek
groq_deepseek_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "deepseek-r1-distill-llama-70b",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": GROQ_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# Groq Llama4
groq_llama4_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": GROQ_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# Grok-3
grok_3_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "grok-3",
        "base_url": "https://api.x.ai/v1",
        "api_key": GROK_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# Grok-3-Mini
grok_3_mini_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "grok-3-mini",
        "base_url": "https://api.x.ai/v1",
        "api_key": GROK_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# Grok-4
grok_4_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "grok-4",
        "base_url": "https://api.x.ai/v1",
        "api_key": GROK_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# Grok Code Fast-1
grok_code_fast_config = {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "grok-code-fast-1",
        "base_url": "https://api.x.ai/v1",
        "api_key": GROK_API_KEY,
        "temperature": 0.2,
        "model_info": {
            "family": "unknown",
            "function_calling": False,
            "json_output": True,
            "vision": False
        }
    }
}

# Comprehensive model choices mapping
MODEL_CHOICES = {
    # OpenAI Models
    "GPT-5": gpt_5_config,
    "GPT-4o": gpt_4o_config,
    "GPT-4o-Mini": gpt_4o_mini_config,
    "GPT-o3-Mini": gpt_o3_mini_config,
    
    # Google Models
    "Gemini-2.5-Pro": gemini_pro_config,
    "Gemini-2.5-Flash": gemini_config,
    
    # DeepSeek
    "DeepSeek-V3.1": deepseek_config,
    
    # OpenRouter Models
    "OpenRouter-DeepSeek": openrouter_deepseek_config,
    "OpenRouter-Llama4": openrouter_llama4_config,
    
    # Groq Models
    "Groq-DeepSeek": groq_deepseek_config,
    "Groq-Llama4": groq_llama4_config,
    
    # xAI Grok Models
    "Grok-3": grok_3_config,
    "Grok-3-Mini": grok_3_mini_config,
    "Grok-4": grok_4_config,
    "Grok-Code-Fast-1": grok_code_fast_config
}

def get_model_config(choice: str) -> Dict[str, Any]:
    """
    Return the chosen model config dict, or default_config if unknown.
    
    Args:
        choice: The model choice string
        
    Returns:
        Model configuration dictionary
    """
    # Use static model configurations only (bypassing UI API manager)
    return MODEL_CHOICES.get(choice, default_config)

def get_all_model_choices() -> Dict[str, Dict[str, Any]]:
    """
    Get all available model choices using static configurations only
    
    Returns:
        Dictionary of all available models
    """
    # Return static model configurations only (bypassing UI API manager)
    return MODEL_CHOICES

def get_assessment_default_config() -> Dict[str, Any]:
    """
    Get default model config for Assessment module (Gemini-2.5-Pro).
    
    Returns:
        Model configuration optimized for content generation
    """
    return gemini_pro_config

def get_courseware_default_config() -> Dict[str, Any]:
    """
    Get default model config for Courseware module (Gemini-2.5-Pro).
    
    Returns:
        Model configuration optimized for document generation
    """
    return gemini_pro_config