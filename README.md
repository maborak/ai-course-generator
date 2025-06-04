# ai-tips-generator
Using OpenAI generate PDF or Markdown files with tips and tricks

# AI Tips Generator

Generate expert-level tips on any technical topic using OpenAI’s GPT API or Ollama, and automatically export the output in **Markdown, HTML, EPUB, and PDF** formats—with custom styling and syntax highlighting. Supports multi-engine selection for flexible AI backend usage.

---

## Features

- **Flexible Topic Selection:** Choose your topic, category, expertise level, and number of tips from the command line.
- **Multi-Engine Support:** Use OpenAI GPT-4.1 or Ollama for tip generation.
- **OpenAI GPT-4.1 Integration:** Automatically generates concise, high-quality tips.
- **Ollama Integration:** Supports local or remote Ollama servers with customizable models.
- **Automatic File Conversion:** 
  - Markdown (`.md`)
  - HTML (`.html`) with custom CSS
  - EPUB (`.epub`) with embedded metadata
  - PDF (`.pdf`) via [Pandoc](https://pandoc.org/) and [WeasyPrint](https://weasyprint.org/)
- **Idempotent Output:** Will not overwrite existing files unless you specify `--force`.
- **Configurable Output Filename:** All output files are named using your topic, category, expertise level, engine, and model.
- **Ollama Streaming Output:** Enable live streaming of Ollama LLM responses for real-time progress with `--ollama-stream`.
- **Embedded Metadata:** EPUB and other formats include metadata such as title, author, category, expertise level, model, and more.
- **Overview Section:** Each generated document includes an AI-written overview/introduction tailored to the topic and expertise level.

---

## Requirements

- **Python 3.8+**
- **OpenAI API key** (set as `OPENAI_API_KEY` in your environment) for OpenAI engine
- **Pandoc** ([installation guide](https://pandoc.org/installing.html))
- **WeasyPrint** (see Python packages and system dependencies below)
- **style.css** in your working directory (for custom HTML/EPUB/PDF styling)
- **requirements.txt** in your working directory (contains all Python dependencies)
- **Ollama Python package and an Ollama server** if using the Ollama engine

### Python packages

To install Python dependencies, simply run:
```sh
pip install -r requirements.txt
```

You may also need system packages for WeasyPrint, such as `libpango`, `cairo`, and `gdk-pixbuf` (see WeasyPrint’s docs).

---

## Usage

Basic usage (default topic: `linux`, default quantity: `5`, default engine: `openai`):

```sh
python tool.py
```

#### Command Line Options

| Option              | Description                                                             | Default   |
|---------------------|-------------------------------------------------------------------------|-----------|
| `--topic`           | Topic for tips                                                          | `linux`   |
| `--quantity`        | Number of tips to generate                                              | `5`       |
| `--category`        | Category for the tips                                                   | `Tip`     |
| `--expertise-level` | Expertise level for the tips                                            | `Novice`  |
| `--force`           | Overwrite existing output files                                         | *off*     |
| `--engine`          | AI engine to use (`openai` or `ollama`)                                 | `openai`  |
| `--ollama-host`     | Host URL for Ollama server (used if engine is `ollama`)                 | `http://localhost:11434` |
| `--ollama-model`    | Ollama model name to use (used if engine is `ollama`)                   | `llama3.2`|
| `--ollama-stream`   | Enable streaming progress for Ollama engine (default: off)              | *off*     |

#### Examples

Generate 10 Bash scripting tips, overwriting files if they exist, using OpenAI:

```sh
python tool.py --topic="Bash scripting" --quantity=10 --force
```

Generate 7 tips on Docker using the Ollama engine with the default local host:

```sh
python tool.py --topic="Docker" --quantity=7 --engine=ollama
```

Generate 5 Kubernetes tips using a remote Ollama server and a custom model:

```sh
python tool.py --topic="Kubernetes" --quantity=5 --engine=ollama --ollama-host="http://remote-ollama-server:11434" --ollama-model="custom-k8s-model"
```

Generate 10 tips on Python with live streaming from Ollama:
```sh
python tool.py --topic="Python" --quantity=10 --engine=ollama --ollama-stream
```

---

## Output Files

After generation, **four files** will be produced, all with your topic, category, expertise level, engine, and model in the filename. For example, with `--topic="Bash scripting" --category="Tip" --expertise-level="Novice" --engine="ollama" --ollama-model="llama3.2"`:

- `output/bash_scripting_tip_novice_ollama_llama3.2_tip.md`    (Markdown)
- `output/bash_scripting_tip_novice_ollama_llama3.2_tip.html`  (HTML, with CSS and highlighting)
- `output/bash_scripting_tip_novice_ollama_llama3.2_tip.epub`  (EPUB, with embedded metadata and styling)
- `output/bash_scripting_tip_novice_ollama_llama3.2_tip.pdf`   (PDF, rendered via WeasyPrint)

---

## How It Works

1. **Prompt Preparation:**  
   Prompts are prepared internally using your topic, category, expertise level, and quantity.
2. **Generation:**  
   Sends the prompt to the selected AI engine (`openai` or `ollama`).  
   For Ollama, the model and host can be specified to customize the request.  
   If streaming is enabled with Ollama, the response is printed live as the model generates text.
3. **Markdown Output:**  
   Saves the generated content as a Markdown file, including a metadata section and an AI-generated overview.
4. **Conversion:**  
   - Runs Pandoc to generate both HTML and EPUB (`.html`, `.epub`), embedding metadata.
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
- **Ollama errors:**  
  Ensure the Ollama server is running and accessible at the specified host URL.  
  Verify the Ollama Python package is installed.

---

## Customizing Output

- **Style:**  
  Edit or replace `style.css` to change the appearance of the HTML/EPUB/PDF output.

---

## License

MIT

---

## Contributions

Pull requests and suggestions welcome!