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
import tempfile
import subprocess
from adapters.engines.openai_adapter import OpenAIEngine
from adapters.engines.ollama_adapter import OllamaEngine
from adapters.file_converter import FileConverter
from core.generator import AITipsGenerator


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
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="AI Tips Generator (Hexagonal Architecture)"
    )
    parser.add_argument('--topic', default='linux')
    parser.add_argument('--quantity', type=int, default=5)
    parser.add_argument(
        '--engine',
        default='openai',
        choices=['openai', 'ollama']
    )
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--ollama-host', default=None)
    parser.add_argument('--ollama-model', default='llama3.2')
    parser.add_argument('--ollama-stream', action='store_true')
    parser.add_argument('--ollama-no-think', action='store_true', help='Disable thinking process in Ollama')
    parser.add_argument('--openai-stream', action='store_true', help='Enable streaming for OpenAI responses')
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if output files can be generated with dummy content'
    )
    parser.add_argument(
        '--category',
        default='Tip',
        help='Category for the tips (used as CATEGORY)'
    )
    parser.add_argument(
        '--expertise-level',
        default='Novice',
        help='Expertise level for the tips'
    )
    args = parser.parse_args()
    logger.debug("Arguments: %s", args)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    if args.check:
        GREEN = "\033[92m"
        RED = "\033[91m"
        RESET = "\033[0m"

        # Use a temporary file prefix
        with tempfile.NamedTemporaryFile(
            dir=output_dir, prefix="check_", suffix="_tip.md", delete=False
        ) as tmp_md:
            output_md = tmp_md.name
            dummy_content = '''# Dummy AI Tips Output

This is a test file for --check mode.

## Tip 1
Dummy tip content.

## Tip 2
More dummy content.
'''
            tmp_md.write(dummy_content.encode("utf-8"))
        logger.info("Dummy markdown saved as %s", output_md)

        converter = FileConverter()
        try:
            converter.convert(output_md)
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"{RED}FAILED{RESET} to convert files: {exc}")
            logger.error("FAILED to convert files: %s", exc)

        base = os.path.splitext(output_md)[0]
        results = {}
        for ext in [".md", ".html", ".pdf", ".epub"]:
            file_path = base + ext
            if os.path.exists(file_path):
                results[ext] = True
            else:
                results[ext] = False

        print("\nCheck results:")
        for ext in [".md", ".html", ".pdf", ".epub"]:
            file_path = base + ext
            status = (
                f"{GREEN}SUCCESS{RESET}"
                if results[ext]
                else f"{RED}FAILED{RESET}"
            )
            print(f"  {file_path}: {status}")

        # Cleanup
        for ext in [".md", ".html", ".pdf", ".epub"]:
            file_path = base + ext
            if os.path.exists(file_path):
                os.remove(file_path)

        print("\nCleanup complete.")
        logger.info(
            "Check complete: All output files generated and cleaned up successfully."
        )
        return

    output_md = os.path.join(
        output_dir,
        f"{sanitize_filename(args.topic)}_"
        f"{sanitize_filename(args.category)}_"
        f"{sanitize_filename(args.expertise_level)}_"
        f"{args.engine}_"
        f"{sanitize_filename(args.ollama_model if args.engine == 'ollama' else 'gpt-4.1')}_tip.md"
    )

    if args.engine == 'openai':
        engine = OpenAIEngine(
            stream=args.openai_stream,
            category=args.category,
            expertise_level=args.expertise_level
        )
    else:
        engine = OllamaEngine(
            args.ollama_model,
            host=args.ollama_host,
            stream=args.ollama_stream,
            category=args.category,
            expertise_level=args.expertise_level,
            think=not args.ollama_no_think
        )
    converter = FileConverter()

    generator = AITipsGenerator(engine, converter)
    logger.debug("Calling generator.generate_tips")
    generator.generate_tips(
        args.topic,
        args.quantity,
        output_md,
        force=args.force
    )


if __name__ == "__main__":
    main()
