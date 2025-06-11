"""
Test suite for OllamaEngine chapter generation.

This module tests the chapter generation functionality for all supported Ollama models.
"""

import logging
import pytest
#from ollama import Client  # Uncomment if needed
from adapters.engines.ollama_adapter import OllamaEngine

logging.basicConfig(level=logging.DEBUG)

# Manually specify models for testing
def get_ollama_models():
    """Return a list of available Ollama models for testing."""
    #return [m['model'] for m in Client().list()['models']]
    return ["llama3.2", "llama4", "mistral", "phi4", "devstral:24b", "qwen3:32b", "deepseek-r1:70b"]

@pytest.mark.parametrize("model", get_ollama_models())
def test_generate_chapters_all_models(model):
    """Test chapter generation with all supported models."""
    print(f"Testing model: {model}", flush=True)
    engine = OllamaEngine(model=model)
    engine.category = "Tip"
    engine.expertise_level = "Expert"
    engine.context_note = ""
    chapters, overview = engine.generate_chapters("Python", 2)
    print(f"TIPS: {chapters}", flush=True)
    print(f"OVERVIEW: {overview}", flush=True)
    assert len(chapters) >= 1, f"Model {model} did not return any tips!"
    assert isinstance(overview, str), f"Model {model} did not return a string overview!"
    assert overview.strip() != "", f"Model {model} returned an empty overview!"
