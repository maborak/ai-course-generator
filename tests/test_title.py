import logging
import pytest
from ollama import Client  # Commented out for now
from adapters.engines.ollama import OllamaEngine

logging.basicConfig(level=logging.DEBUG)

# Manually specify models for testing
def get_ollama_models():
    return [m['model'] for m in Client().list()['models']]
    #return ["llama3.2", "llama4","mistral","phi4","devstral:24b","qwen3:32b","deepseek-r1:70b"]
    #return ["llama3.2", "llama4"]

@pytest.mark.parametrize("model", get_ollama_models())
def test_generate_tip_titles_all_models(model):
    print(f"Testing model: {model}", flush=True)
    engine = OllamaEngine(model=model)
    engine.category = "Tip"
    engine.expertise_level = "Expert"
    engine.context_note = ""
    tips, overview = engine.generate_tip_titles("Python", 2)
    print(f"TIPS: {tips}", flush=True)
    print(f"OVERVIEW: {overview}", flush=True)
    assert len(tips) >= 1, f"Model {model} did not return any tips!"
    assert isinstance(overview, str), f"Model {model} did not return a string overview!"
    assert overview.strip() != "", f"Model {model} returned an empty overview!"