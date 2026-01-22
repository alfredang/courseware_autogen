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
import copy

# Get API keys from the new API management system
from settings.api_manager import load_api_keys

def get_openrouter_key():
    """Get OpenRouter API key dynamically"""
    keys = load_api_keys()
    return keys.get("OPENROUTER_API_KEY", "")

def _build_model_config(model: str, family: str, function_calling: bool = False, vision: bool = False) -> Dict[str, Any]:
    """Build a model config with fresh API key"""
    return {
        "provider": "OpenAIChatCompletionClient",
        "config": {
            "model": model,
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": get_openrouter_key(),
            "temperature": 0.2,
            "model_info": {
                "family": family,
                "function_calling": function_calling,
                "json_output": True,
                "vision": vision
            }
        }
    }

def _get_deepseek_config():
    return _build_model_config("deepseek/deepseek-chat", "unknown", False, False)

def _get_gpt4o_mini_config():
    return _build_model_config("openai/gpt-4o-mini", "openai", True, False)

def _get_claude_sonnet_config():
    return _build_model_config("anthropic/claude-3.5-sonnet", "anthropic", True, True)

def _get_gemini_flash_config():
    return _build_model_config("google/gemini-2.0-flash-001", "google", False, True)

def _get_gemini_pro_config():
    return _build_model_config("google/gemini-pro-1.5", "google", False, True)

def get_model_config(choice: str) -> Dict[str, Any]:
    """
    Return the chosen model config dict, or default_config if unknown.

    Args:
        choice: The model choice string

    Returns:
        Model configuration dictionary with fresh API key
    """
    configs = {
        "DeepSeek-Chat": _get_deepseek_config,
        "GPT-4o-Mini": _get_gpt4o_mini_config,
        "Claude-Sonnet-3.5": _get_claude_sonnet_config,
        "Gemini-Flash": _get_gemini_flash_config,
        "Gemini-Pro": _get_gemini_pro_config
    }
    config_func = configs.get(choice, _get_deepseek_config)
    return config_func()

def get_all_model_choices() -> Dict[str, Dict[str, Any]]:
    """
    Get all available model choices with fresh API keys

    Returns:
        Dictionary of all available models
    """
    return {
        "DeepSeek-Chat": _get_deepseek_config(),
        "GPT-4o-Mini": _get_gpt4o_mini_config(),
        "Claude-Sonnet-3.5": _get_claude_sonnet_config(),
        "Gemini-Flash": _get_gemini_flash_config(),
        "Gemini-Pro": _get_gemini_pro_config()
    }

def get_assessment_default_config() -> Dict[str, Any]:
    """
    Get default model config for Assessment module (DeepSeek via OpenRouter).

    Returns:
        Model configuration optimized for content generation
    """
    return _get_deepseek_config()

def get_courseware_default_config() -> Dict[str, Any]:
    """
    Get default model config for Courseware module (DeepSeek via OpenRouter).

    Returns:
        Model configuration optimized for document generation
    """
    return _get_deepseek_config()

# Backward compatibility - these now call functions to get fresh configs
# WARNING: These are evaluated at import time, may have empty keys
# Use the get_* functions instead for guaranteed fresh keys
OPENROUTER_API_KEY = get_openrouter_key()
deepseek_config = _get_deepseek_config()
gpt4o_mini_config = _get_gpt4o_mini_config()
claude_sonnet_config = _get_claude_sonnet_config()
gemini_flash_config = _get_gemini_flash_config()
gemini_pro_config = _get_gemini_pro_config()
default_config = deepseek_config
MODEL_CHOICES = get_all_model_choices()
