import os
from pathlib import Path
from openai import OpenAI
from pprint import pprint as pp
import markdown2
from fpdf import FPDF
import re

# Configuration
PROMPT_FILE = "prompt.txt"
OUTPUT_MD = "output.md"
OUTPUT_PDF = "output.pdf"
MODEL = "gpt-4.1"  # Use a model with a larger context window
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# Define per-token costs for the selected model
# For GPT-4.1, as of May 2025:
# Input: $0.002 per 1K tokens
# Output: $0.008 per 1K tokens
INPUT_COST_PER_1K = 0.002
OUTPUT_COST_PER_1K = 0.008

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def read_prompt(file_path):
    """
    Reads the prompt content from the specified text file.
    """
    try:
        return Path(file_path).read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        exit(1)

def get_full_completion(prompt):
    messages = [{"role": "user", "content": prompt}]
    full_response = ""
    iteration = 0

    # Initialize token counters
    total_prompt_tokens = 0
    total_completion_tokens = 0

    while True:
        iteration += 1
        print(f"\n--- Requesting chunk {iteration} ---")
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

        # Update token counters
        usage = response.usage
        total_prompt_tokens += usage.prompt_tokens
        total_completion_tokens += usage.completion_tokens

        full_response += chunk

        # Check if the response seems incomplete
        if finish_reason == "stop":
            # Heuristic: check if the last tip is incomplete
            if "Tip 20" not in chunk:
                print("Detected incomplete Tip #20, requesting continuation...")
                messages.append({"role": "assistant", "content": chunk})
                messages.append({"role": "user", "content": "Please continue from where you left off."})
                continue
            else:
                print("Completed successfully.")
                break
        elif finish_reason == "length":
            print("Output truncated, requesting continuation...")
            messages.append({"role": "assistant", "content": chunk})
            messages.append({"role": "user", "content": "Please continue from where you left off."})
        else:
            print(f"Unexpected finish_reason: {finish_reason}")
            break

    # Calculate costs
    input_cost = (total_prompt_tokens / 1000) * INPUT_COST_PER_1K
    output_cost = (total_completion_tokens / 1000) * OUTPUT_COST_PER_1K
    total_cost = input_cost + output_cost

    # Display token usage and costs
    print(f"\nTotal prompt tokens used: {total_prompt_tokens}")
    print(f"Total completion tokens used: {total_completion_tokens}")
    print(f"Input cost: ${input_cost:.4f}")
    print(f"Output cost: ${output_cost:.4f}")
    print(f"Total cost: ${total_cost:.4f}")

    return full_response

def convert_md_to_pdf(md_file, pdf_file):
    """
    Converts a markdown file to PDF format.
    """
    try:
        # Read markdown content
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown2.markdown(md_content)
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Set font
        pdf.set_font("Arial", size=12)
        
        # Process HTML content
        # Remove HTML tags and split into lines
        text_content = re.sub('<[^<]+?>', '', html_content)
        lines = text_content.split('\n')
        
        # Add content to PDF
        for line in lines:
            if line.strip():
                pdf.multi_cell(0, 10, txt=line.strip())
        
        # Save PDF
        pdf.output(pdf_file)
        print(f"PDF saved as {pdf_file}")
        
    except Exception as e:
        print(f"Error converting markdown to PDF: {str(e)}")
        exit(1)

def main():
    print("Reading prompt from file...")
    prompt = read_prompt(PROMPT_FILE)

    print("Generating expert-level Bash scripting tips with OpenAI API...")
    full_text = get_full_completion(prompt)
    print(f"\nTotal response length: {len(full_text)} characters")

    # Save as markdown
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"Markdown saved as {OUTPUT_MD}")
    
    # Convert to PDF
    print("Converting markdown to PDF...")
    convert_md_to_pdf(OUTPUT_MD, OUTPUT_PDF)

if __name__ == "__main__":
    main()