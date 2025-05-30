# ai-tips-generator
Using OpenAI generate PDF or Markdown files with tips and tricks

# AI Tips Generator

Generate expert-level tips on any technical topic using OpenAI’s GPT API, and automatically export the output in **Markdown, HTML, EPUB, and PDF** formats—with custom styling and syntax highlighting.

---

## Features

- **Flexible Topic Selection:** Choose your topic and number of tips from the command line.
- **OpenAI GPT-4.1 Integration:** Automatically generates concise, high-quality tips.
- **Templated Prompting:** Uses `prompt.txt` with placeholders for easy customization.
- **Automatic File Conversion:** 
  - Markdown (`.md`)
  - HTML (`.html`) with custom CSS
  - EPUB (`.epub`)
  - PDF (`.pdf`) via [Pandoc](https://pandoc.org/) and [WeasyPrint](https://weasyprint.org/)
- **Idempotent Output:** Will not overwrite existing files unless you specify `--force`.
- **Configurable Output Filename:** All output files are named using your topic, sanitized, and suffixed with `_tip`.

---

## Requirements

- **Python 3.8+**
- **OpenAI API key** (set as `OPENAI_API_KEY` in your environment)
- **Pandoc** ([installation guide](https://pandoc.org/installing.html))
- **WeasyPrint** (see Python packages and system dependencies below)
- **style.css** in your working directory (for custom HTML/EPUB/PDF styling)
- **requirements.txt** in your working directory (contains all Python dependencies)

### Python packages

To install Python dependencies, simply run:
```sh
pip install -r requirements.txt
```

You may also need system packages for WeasyPrint, such as `libpango`, `cairo`, and `gdk-pixbuf` (see WeasyPrint’s docs).

---

## Usage

### 1. Prepare Your Prompt Template

Edit `prompt.txt` and use the following placeholders:
- `{{TOPIC}}` — will be replaced with the selected topic
- `{{NUMBER_OF_TIPS}}` — will be replaced with the quantity

### 2. Run the Script

Basic usage (default topic: `linux`, default quantity: `5`):

```sh
python tool.py
```

#### Command Line Options

| Option          | Description                                                             | Default   |
|-----------------|-------------------------------------------------------------------------|-----------|
| `--topic`       | Topic for tips (will replace `{{TOPIC}}` in `prompt.txt`)               | `linux`   |
| `--quantity`    | Number of tips to generate (replaces `{{NUMBER_OF_TIPS}}` in prompt)    | `5`       |
| `--force`       | Overwrite existing output files (otherwise, script exits if present)     | *off*     |

#### Examples

Generate 10 Bash scripting tips, overwriting files if they exist:

```sh
python tool.py --topic="Bash scripting" --quantity=10 --force
```

---

## Output Files

After generation, **four files** will be produced, all with your topic name (sanitized for filenames), plus the `_tip` suffix. For example, with `--topic="Bash scripting"`:

- `bash_scripting_tip.md`    (Markdown)
- `bash_scripting_tip.html`  (HTML, with CSS and highlighting)
- `bash_scripting_tip.epub`  (EPUB, with embedded resources and styling)
- `bash_scripting_tip.pdf`   (PDF, rendered via WeasyPrint)

---

## How It Works

1. **Prompt Preparation:**  
   Reads `prompt.txt`, replaces `{{TOPIC}}` and `{{NUMBER_OF_TIPS}}` with your chosen values.
2. **Generation:**  
   Sends the prompt to OpenAI (using GPT-4.1), automatically continuing until the requested number of tips is reached.
3. **Markdown Output:**  
   Saves the generated content as `<topic>_tip.md`.
4. **Conversion:**  
   - Runs Pandoc to generate both HTML and EPUB (`.html`, `.epub`).
   - Runs WeasyPrint to generate PDF from the HTML.
5. **Safety:**  
   If any output file already exists, the script exits and prints a message (unless you use `--force`).

---

## Troubleshooting

- **Pandoc or WeasyPrint not found:**  
  Ensure both are installed and in your PATH.
- **WeasyPrint errors:**  
  Missing system dependencies (fonts, Cairo, Pango, GDK-PixBuf) can cause failures.  
  See [WeasyPrint's install docs](https://weasyprint.readthedocs.io/en/stable/install.html).
- **OpenAI errors:**  
  Make sure your API key is set as the `OPENAI_API_KEY` environment variable.

---

## Customizing Output

- **Style:**  
  Edit or replace `style.css` to change the appearance of the HTML/EPUB/PDF output.
- **Prompt Logic:**  
  Tweak `prompt.txt` to guide the AI’s writing style, length, or structure.

---

## Example Prompt Template

Here’s a simple `prompt.txt` template:

```
Generate {{NUMBER_OF_TIPS}} expert-level tips about {{TOPIC}}.
Each tip should be practical, concise, and suitable for advanced users.
Format the output as a numbered Markdown list, with explanations for each tip.
```

---

## License

MIT

---

## Contributions

Pull requests and suggestions welcome!