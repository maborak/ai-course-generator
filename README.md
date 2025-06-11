# AI Knowledge Generator

Generate comprehensive educational content on any technical topic using OpenAI's GPT API or Ollama. Create professional ebooks, guides, and tutorials with **Markdown, HTML, EPUB, and PDF** formats—complete with custom styling and syntax highlighting. Perfect for creating educational materials, technical documentation, and learning resources.

---

## Features

- **Versatile Content Generation:** Create various types of educational content:
  - Tips and Tricks
  - How-to Guides
  - Best Practices
  - Tutorials
  - Technical Documentation
  - Learning Resources
- **Flexible Topic Selection:** Choose your topic, category, expertise level, and content quantity from the command line.
- **Multi-Engine Support:** Use OpenAI GPT-4/3.5 or Ollama for content generation.
- **OpenAI Integration:** 
  - Support for multiple models (GPT-4, GPT-3.5-turbo)
  - Streaming responses with `--openai-stream`
  - Automatic token counting and cost estimation
- **Ollama Integration:** 
  - Supports local or remote Ollama servers
  - Customizable models (llama2, mistral, etc.)
  - Streaming support with `--ollama-stream`
  - Optional thinking process with `--ollama-no-think`
- **Professional Output Formats:** 
  - Markdown (`.md`) for easy editing and version control
  - HTML (`.html`) with custom CSS for web viewing
  - EPUB (`.epub`) with embedded metadata for e-readers
  - PDF (`.pdf`) for professional printing and sharing
- **Idempotent Output:** Will not overwrite existing files unless you specify `--force`.
- **Configurable Output Filename:** All output files are named using your topic, category, expertise level, engine, and model.
- **Embedded Metadata:** EPUB and other formats include metadata such as title, author, category, expertise level, model, and more.
- **Overview Section:** Each generated document includes an AI-written overview/introduction tailored to the topic and expertise level.
- **Monitoring Tools:** Use `--check` to verify all output formats can be generated correctly.

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

You may also need system packages for WeasyPrint, such as `libpango`, `cairo`, and `gdk-pixbuf` (see WeasyPrint's docs).

---

## Usage

### Basic Usage

Generate a comprehensive Python programming guide using OpenAI GPT-4:
```sh
python main.py --topic "Python Programming" --category "Guide" --expertise-level "Intermediate" --engine openai --openai-model gpt-4
```

Create a Docker best practices tutorial with streaming:
```sh
python main.py --topic "Docker Best Practices" --category "Tutorial" --quantity 3 --engine openai --openai-model gpt-3.5-turbo --openai-stream
```

Generate a Kubernetes deployment guide using Ollama:
```sh
python main.py --topic "Kubernetes Deployment" --category "How-to" --quantity 4 --engine ollama --ollama-model llama2 --ollama-host http://localhost:11434
```

Create a Git workflow tutorial with Ollama:
```sh
python main.py --topic "Git Workflows" --category "Tutorial" --quantity 2 --engine ollama --ollama-model mistral --ollama-stream --ollama-no-think
```

Generate a Linux system administration guide:
```sh
python main.py --topic "Linux Administration" --category "Guide" --expertise-level "Advanced" --engine openai --openai-model gpt-4
```

Check if all output formats can be generated (monitoring):
```sh
python main.py --check
```

### Command Line Options

#### Common Arguments
| Option              | Description                                                             | Default   |
|---------------------|-------------------------------------------------------------------------|-----------|
| `--topic`           | Topic for tips                                                          | `linux`   |
| `--quantity`        | Number of tips to generate                                              | `5`       |
| `--category`        | Category for the tips                                                   | `Tip`     |
| `--expertise-level` | Expertise level for the tips                                            | `Novice`  |
| `--force`           | Overwrite existing output files                                         | *off*     |
| `--engine`          | AI engine to use (`openai` or `ollama`)                                 | `openai`  |
| `--check`           | Verify all output formats can be generated                              | *off*     |

#### OpenAI Arguments
| Option              | Description                                                             | Default   |
|---------------------|-------------------------------------------------------------------------|-----------|
| `--openai-model`    | OpenAI model to use (e.g., gpt-4, gpt-3.5-turbo)                        | `gpt-4`   |
| `--openai-stream`   | Enable streaming for OpenAI responses                                   | *off*     |

#### Ollama Arguments
| Option              | Description                                                             | Default   |
|---------------------|-------------------------------------------------------------------------|-----------|
| `--ollama-host`     | Host URL for Ollama server                                              | `None`    |
| `--ollama-model`    | Ollama model name to use                                                | `llama3.2`|
| `--ollama-stream`   | Enable streaming for Ollama responses                                   | *off*     |
| `--ollama-no-think` | Disable thinking process in Ollama                                      | *off*     |

---

## Prompt Structure

The generator uses two types of prompts, stored in the `adapters/engines/openai_adapter/prompts/` directory:

### Titles Prompt
Located in `prompts/titles/`, this prompt generates the chapter titles and overview. It includes:
- Topic context
- Expertise level requirements
- Category specifications
- Quantity of tips needed
- Format requirements

### Content Prompt
Located in `prompts/content/`, this prompt generates the detailed content for each tip. It includes:
- Topic context
- Chapter title
- Chapter index
- Total chapters
- Expertise level requirements
- Category specifications
- Format requirements

You can customize these prompts by editing the corresponding files in the prompts directory.

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
   If streaming is enabled, the response is printed live as the model generates text.
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
- **Connection errors:**  
  If you encounter streaming connection errors, try:
  - Running without streaming (`--openai-stream` or `--ollama-stream`)
  - Checking your network stability
  - Using a different model
  - Reducing the quantity of tips

---

## Customizing Output

- **Style:**  
  Edit or replace `style.css` to change the appearance of the HTML/EPUB/PDF output.
- **Prompts:**  
  Customize the generation by editing the prompt templates in `adapters/engines/openai_adapter/prompts/`.

---

## License

MIT

---

## Contributions

Pull requests and suggestions welcome!