#!/usr/bin/env python3
# pylint: disable=invalid-name,too-many-arguments,too-many-locals
# pylint: disable=too-many-branches,too-many-statements,line-too-long
"""
AI Tips Generator - Main Module

This module provides the main entry point for the AI Tips Generator application.
It handles command-line arguments, initializes the appropriate AI engine,
and coordinates the generation of tips in various formats.

Example:
    python main.py --topic linux --quantity 5 --engine openai
"""

import argparse
import logging
import os
import re
import sys
from adapters.engines.openai_adapter import OpenAIEngine
from adapters.engines.ollama_adapter import OllamaEngine
from adapters.file_converter import FileConverter
from core.generator import AIKnowledgeGenerator
from core.verifier import FileConversionVerifier


def sanitize_filename(s):
    """
    Sanitize a string to be used as a filename.
    
    Args:
        s (str): The string to sanitize
        
    Returns:
        str: A sanitized string safe for use as a filename
    """
    s = s.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s


def str2bool(v):
    """Convert string to boolean value.
    
    Args:
        v: String value to convert
        
    Returns:
        bool: True for 'true', '1', 'yes', 'y', 't', 'on'
              False for 'false', '0', 'no', 'n', 'f', 'off'
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    if v.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')


def get_available_themes():
    """Get list of available themes from the themes directory.
    
    Returns:
        list: List of theme names (without .css extension)
    """
    themes_dir = os.path.join(os.path.dirname(__file__), 'themes')
    if not os.path.exists(themes_dir):
        return ['normal']
    
    themes = []
    for file in os.listdir(themes_dir):
        if file.endswith('.css'):
            themes.append(file[:-4])  # Remove .css extension
    return sorted(themes) if themes else ['normal']


def main():
    """
    Main entry point for the AI Tips Generator application.
    
    This function:
    1. Sets up logging
    2. Parses command line arguments
    3. Initializes the appropriate AI engine
    4. Generates tips in the requested format
    5. Handles the --check mode for testing output generation
    """
    parser = argparse.ArgumentParser(
        description="AI Tips Generator (Hexagonal Architecture)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 5 Linux tips using OpenAI GPT-4
  python main.py --topic linux --engine openai --openai-model gpt-4

  # Generate 3 Python tips using OpenAI GPT-3.5 with streaming
  python main.py --topic python --quantity 3 --engine openai --openai-model gpt-3.5-turbo --openai-stream

  # Generate 4 Docker tips using Ollama with custom host
  python main.py --topic docker --quantity 4 --engine ollama --ollama-model llama2 --ollama-host http://localhost:11434

  # Generate 2 Git tips using Ollama with streaming and no thinking process
  python main.py --topic git --quantity 2 --engine ollama --ollama-model mistral --ollama-stream --ollama-no-think

  # Check if all output formats can be generated (monitoring)
  python main.py --check

  # Generate tips with a specific theme
  python main.py --topic python --theme dracula

Monitoring:
  The --check flag helps verify that all output formats (markdown, HTML, PDF, EPUB)
  can be generated correctly. It creates a test file with dummy content and attempts
  to convert it to all supported formats. This is useful for:
  - Verifying installation of required dependencies
  - Testing file conversion capabilities
  - Checking write permissions in the output directory
"""
    )
    # Common arguments
    common_group = parser.add_argument_group('Common Arguments')
    common_group.add_argument('--topic', default='linux', help='Topic to generate tips for')
    common_group.add_argument('--quantity', type=int, default=5, help='Number of tips to generate')
    common_group.add_argument('--engine', default='openai', choices=['openai', 'ollama'], help='AI engine to use')
    common_group.add_argument('--force', action='store_true', help='Force overwrite existing files')
    common_group.add_argument('--category', default='Tip', help='Category for the tips')
    common_group.add_argument('--expertise-level', default='Novice', help='Expertise level for the tips')
    common_group.add_argument('--debug', action='store_true', help='Enable debug logging')
    common_group.add_argument(
        '--check',
        action='store_true',
        help='Check if output files can be generated with dummy content'
    )
    common_group.add_argument(
        '--progress-bar',
        type=str2bool,
        default=False,
        help='Show progress bar during generation (true/false, yes/no, 1/0)'
    )
    common_group.add_argument(
        '--theme',
        default='normal',
        choices=get_available_themes(),
        help='Theme to use for HTML/PDF output'
    )

    # OpenAI specific arguments
    openai_group = parser.add_argument_group('OpenAI Arguments')
    openai_group.add_argument('--openai-model', default='gpt-4', help='OpenAI model to use (e.g., gpt-4, gpt-3.5-turbo)')
    openai_group.add_argument('--openai-stream', type=str2bool, default=True, help='Enable streaming for OpenAI responses (true/false, yes/no, 1/0)')

    # Ollama specific arguments
    ollama_group = parser.add_argument_group('Ollama Arguments')
    ollama_group.add_argument('--ollama-host', default=None, help='Ollama host address')
    ollama_group.add_argument('--ollama-model', default='llama3.2', help='Ollama model to use')
    ollama_group.add_argument('--ollama-stream', type=str2bool, default=True, help='Enable streaming for Ollama responses')
    ollama_group.add_argument('--ollama-no-think', action='store_true', help='Disable thinking process in Ollama')

    args = parser.parse_args()
    
    # Configure logging based on debug flag
    logger = logging.getLogger(__name__)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.debug("Arguments: %s", args)

    # Validate engine-specific arguments
    if args.engine == 'openai':
        # Check if any Ollama-specific arguments are being used
        ollama_args = [arg for arg in sys.argv if arg.startswith('--ollama-')]
        if ollama_args:
            parser.error(
                f"Ollama-specific arguments cannot be used with OpenAI engine: {', '.join(ollama_args)}"
            )
    elif args.engine == 'ollama':
        # Check if any OpenAI-specific arguments are being used
        openai_args = [arg for arg in sys.argv if arg.startswith('--openai-')]
        if openai_args:
            parser.error(
                f"OpenAI-specific arguments cannot be used with Ollama engine: {', '.join(openai_args)}"
            )

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    if args.check:
        verifier = FileConversionVerifier()
        results = verifier.verify()
        verifier.display_results(results)
        return

    output_md = os.path.join(
        output_dir,
        f"{sanitize_filename(args.topic)}_"
        f"{sanitize_filename(args.category)}_"
        f"{sanitize_filename(args.expertise_level)}_"
        f"{args.engine}_"
        f"{sanitize_filename(args.ollama_model if args.engine == 'ollama' else args.openai_model)}.md"
    )

    # Check if output file exists and handle force flag
    if os.path.exists(output_md) and not args.force:
        logger.error("Output file already exists: %s", output_md)
        logger.error("Use --force to overwrite existing file")
        sys.exit(1)

    # Initialize the appropriate engine
    if args.engine == "openai":
        engine = OpenAIEngine(
            model=args.openai_model,
            stream=args.openai_stream,
            category=args.category,
            expertise_level=args.expertise_level,
            debug=args.debug,
            progress_bar=args.progress_bar
        )
    else:  # ollama
        engine = OllamaEngine(
            model=args.ollama_model,
            host=args.ollama_host,
            stream=args.ollama_stream,
            category=args.category,
            expertise_level=args.expertise_level,
            debug=args.debug,
            progress_bar=args.progress_bar
        )
    converter = FileConverter(theme=args.theme)

    generator = AIKnowledgeGenerator(engine, converter)
    logger.debug("Calling generator.run")

    # Set up progress bar if enabled
    if args.progress_bar:
        generator.run(
            args.topic,
            args.quantity,
            output_md,
            force=args.force
        )
    else:
        generator.run(
            args.topic,
            args.quantity,
            output_md,
            force=args.force
        )


if __name__ == "__main__":
    main()
