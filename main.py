import argparse
from adapters.engines.openai import OpenAIEngine
from adapters.engines.ollama import OllamaEngine
from adapters.file_converter import FileConverter
from core.generator import AITipsGenerator

def sanitize_filename(s):
    import re
    s = s.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s

def main():
    import os
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)

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

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_md = os.path.join(
        output_dir,
        f"{sanitize_filename(args.topic)}_{args.engine}_{sanitize_filename(args.ollama_model if args.engine == 'ollama' else 'gpt-4.1')}_tip.md"
    )

    if args.engine == 'openai':
        engine = OpenAIEngine()
    else:
        engine = OllamaEngine(args.ollama_model, host=args.ollama_host, stream=args.ollama_stream)
    converter = FileConverter()

    generator = AITipsGenerator(engine, converter)
    logger.debug("Calling generator.generate_tips")
    generator.generate_tips(args.topic, args.quantity, output_md, force=args.force)

if __name__ == "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("Starting main execution")
    main()