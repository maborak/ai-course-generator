import os
import re
import argparse
import subprocess
from pathlib import Path
from openai import OpenAI
import ollama
from pprint import pprint as pp

# ==============================
#        Configuration
# ==============================
PROMPT_FILE = "adapters/engines/openai/prompt.txt"
DEFAULT_TOPIC = "linux"
DEFAULT_QUANTITY = 5
MODEL = "gpt-4.1"  # Use a model with a larger context window
MAX_TOKENS = 4096
TEMPERATURE = 0.7
MAX_ITERATIONS = 50  # Maximum number of iterations to avoid infinite loops

# Define per-token costs for the selected model
INPUT_COST_PER_1K = 0.002
OUTPUT_COST_PER_1K = 0.008

# ==============================
#         Utilities
# ==============================

def sanitize_filename(s):
    """Sanitize string for safe filename."""
    s = s.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)      # Remove special characters
    s = re.sub(r'[\s-]+', '_', s)       # Replace spaces/hyphens with underscores
    return s

def parse_args():
    parser = argparse.ArgumentParser(description="AI Tips Generator")
    parser.add_argument('--topic', default=DEFAULT_TOPIC, help=f'Topic for the tips (default: {DEFAULT_TOPIC})')
    parser.add_argument('--quantity', type=int, default=DEFAULT_QUANTITY, help=f'Number of tips to generate (default: {DEFAULT_QUANTITY})')
    parser.add_argument('--force', action='store_true', help='Overwrite output file if it exists')
    parser.add_argument('--engine', default='openai', choices=['openai', 'ollama'], help="Which AI engine to use: openai (default) or ollama")
    parser.add_argument('--ollama-host', default=None, help='Ollama server URL (default: http://localhost:11434)')
    parser.add_argument('--ollama-model', default='llama3.2', help='Ollama model name to use (default: llama3.2)')
    parser.add_argument('--ollama-stream', action='store_true', help='Enable streaming progress for Ollama engine (default: disabled)')
    return parser.parse_args()

def read_and_replace_prompt(file_path, topic, quantity):
    try:
        content = Path(file_path).read_text(encoding='utf-8')
        content = content.replace("{{TOPIC}}", topic)
        content = content.replace("{{NUMBER_OF_TIPS}}", str(quantity))
        return content
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        exit(1)

def run_subprocess(command, success_message):
    """Run a shell command, report errors if any, and print a success message."""
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
        print(success_message)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command '{' '.join(command)}' failed with exit code {e.returncode}.")
        print(f"Details: {e}")
        print("Please check that all required tools (pandoc, weasyprint) are installed and your input files are valid.")
        exit(1)

def convert_files(md_file, css_file="style.css"):
    base_name = os.path.splitext(md_file)[0]
    html_file = base_name + ".html"
    epub_file = base_name + ".epub"
    pdf_file = base_name + ".pdf"

    # 1. Convert Markdown to HTML using Pandoc
    pandoc_html_cmd = [
        "pandoc",
        md_file,
        "-o", html_file,
        "--standalone",
        "--embed-resources",
        f"--css={css_file}",
        "--highlight-style=kate"
    ]
    run_subprocess(pandoc_html_cmd, f"HTML file generated: {html_file}")

    # 2. Convert Markdown to EPUB using Pandoc
    pandoc_epub_cmd = [
        "pandoc",
        md_file,
        "-o", epub_file,
        "--standalone",
        "--embed-resources",
        f"--css={css_file}",
        "--highlight-style=kate"
    ]
    run_subprocess(pandoc_epub_cmd, f"EPUB file generated: {epub_file}")

    # 3. Convert HTML to PDF using WeasyPrint
    weasyprint_cmd = [
        "weasyprint",
        html_file,
        pdf_file
    ]
    run_subprocess(weasyprint_cmd, f"PDF file generated: {pdf_file}")

# ==============================
#     OpenAI Completion Logic
# ==============================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_full_completion(prompt, quantity, engine="openai", ollama_model="llama3.2", ollama_host=None, ollama_stream=False):
    messages = [{"role": "user", "content": prompt}]
    full_response = ""
    iteration = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0

    while True:
        iteration += 1
        print(f"\n--- Requesting chunk {iteration} ---")
        if engine == "openai":
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
            pp(response)
            chunk = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            print(f"Finish reason: {finish_reason}")
            print(f"Chunk length: {len(chunk)} characters")

            usage = response.usage
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
        elif engine == "ollama":
            ollama_kwargs = {}
            if ollama_host is not None and bool(ollama_host):
                ollama_kwargs['host'] = ollama_host
            if ollama_stream:
                stream_response = ollama.chat(model=ollama_model, messages=messages, stream=True, **ollama_kwargs)
                chunk = ""
                print(f"\n[Ollama Streaming Output]: ", end="", flush=True)
                for msg in stream_response:
                    content_piece = msg['message']['content']
                    print(content_piece, end="", flush=True)
                    chunk += content_piece
                print("\n[End of Ollama Output]")
                finish_reason = 'stop'
            else:
                response = ollama.chat(model=ollama_model, messages=messages, **ollama_kwargs)
                chunk = response['message']['content']
                finish_reason = response['message'].get('finish_reason', 'stop')
                print(f"Finish reason: {finish_reason}")
                print(f"Chunk length: {len(chunk)} characters")
                # Ollama API may not provide token usage, so skip cost calculation
        else:
            raise ValueError(f"Unknown engine: {engine}")

        full_response += chunk

        if finish_reason == "stop":
            if (f"Tip #{quantity}" in chunk or f"Tip {quantity}" in chunk) or iteration > MAX_ITERATIONS:
                print("Completed successfully.")
                break
            else:
                print(f"Detected incomplete Tip #{quantity}, requesting continuation...")
                messages.append({"role": "assistant", "content": chunk})
                messages.append({"role": "user", "content": "Please continue from where you left off."})
                continue
        elif finish_reason == "length":
            print("Output truncated, requesting continuation...")
            messages.append({"role": "assistant", "content": chunk})
            messages.append({"role": "user", "content": "Please continue from where you left off."})
        else:
            print(f"Unexpected finish_reason: {finish_reason}")
            break

    if engine == "openai":
        input_cost = (total_prompt_tokens / 1000) * INPUT_COST_PER_1K
        output_cost = (total_completion_tokens / 1000) * OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost

        print(f"\nTotal prompt tokens used: {total_prompt_tokens}")
        print(f"Total completion tokens used: {total_completion_tokens}")
        print(f"Input cost: ${input_cost:.4f}")
        print(f"Output cost: ${output_cost:.4f}")
        print(f"Total cost: ${total_cost:.4f}")

    return full_response

# ==============================
#           Main
# ==============================
def main():
    args = parse_args()
    topic = args.topic
    quantity = args.quantity

    model_name = args.ollama_model if args.engine == 'ollama' else MODEL

    print("Reading prompt from file...")
    prompt = read_and_replace_prompt(PROMPT_FILE, topic, quantity)

    # Generate sanitized filename for the output with engine and model name
    output_md = f"{sanitize_filename(topic)}_{args.engine}_{sanitize_filename(model_name)}_tip.md"

    if os.path.exists(output_md) and not args.force:
        print(f"Completed: output file '{output_md}' already exists. Use --force to overwrite.")
        return

    print(f"Generating expert-level {topic} tips with {args.engine} API...")
    full_text = get_full_completion(
        prompt,
        quantity,
        engine=getattr(args, 'engine', 'openai'),
        ollama_model=args.ollama_model,
        ollama_host=args.ollama_host,
        ollama_stream=args.ollama_stream
    )
    print(f"\nTotal response length: {len(full_text)} characters")

    # Save as markdown
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"Markdown saved as {output_md}")

    # Convert to HTML, EPUB, PDF
    convert_files(output_md)

if __name__ == "__main__":
    main()