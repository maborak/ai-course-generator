import argparse
from adapters.engines.openai_engine import OpenAIEngine
from adapters.engines.ollama_engine import OllamaEngine
from adapters.file_converter import FileConverter
from core.generator import AITipsGenerator

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

PROMPT_FILE = "prompt.txt"
MODEL = "gpt-4.1"
MAX_TOKENS = 4096
TEMPERATURE = 0.7

def read_and_replace_prompt(file_path, topic, quantity):
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    content = content.replace("{{TOPIC}}", topic)
    content = content.replace("{{NUMBER_OF_TIPS}}", str(quantity))
    logger.debug(f"Prompt after replacements: {content}")
    return content

def sanitize_filename(s):
    import re
    s = s.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    logger.debug(f"Sanitized filename: {s}")
    return s

def main():
    parser = argparse.ArgumentParser(description="AI Tips Generator (Hexagonal Architecture)")
    parser.add_argument('--topic', default='linux')
    parser.add_argument('--quantity', type=int, default=5)
    parser.add_argument('--engine', default='openai', choices=['openai', 'ollama'])
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--ollama-host', default=None)
    parser.add_argument('--ollama-model', default='llama3.2')
    parser.add_argument('--ollama-stream', action='store_true')
    args = parser.parse_args()
    logger.debug(f"Arguments: {args}")

    prompt = read_and_replace_prompt(PROMPT_FILE, args.topic, args.quantity)
    output_md = f"{sanitize_filename(args.topic)}_{args.engine}_{sanitize_filename(args.ollama_model if args.engine == 'ollama' else MODEL)}_tip.md"

    if args.engine == 'openai':
        engine = OpenAIEngine(MODEL, TEMPERATURE, MAX_TOKENS)
    else:
        engine = OllamaEngine(args.ollama_model, host=args.ollama_host, stream=args.ollama_stream)
    converter = FileConverter()

    generator = AITipsGenerator(engine, converter)
    logger.debug(f"Calling generator with prompt: {prompt[:100]}...")
    generator.generate_tips(prompt, args.topic, args.quantity, output_md, force=args.force)

if __name__ == "__main__":
    logger.debug("Starting main execution")
    main()