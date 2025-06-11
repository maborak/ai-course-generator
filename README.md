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

### OpenAI Examples

Generate a comprehensive Python programming guide using GPT-4:
```sh
python main.py --topic "Python Programming" --category "Guide" --expertise-level "Intermediate" --engine openai --openai-model gpt-4
```

Create a Docker best practices tutorial with streaming:
```sh
python main.py --topic "Docker Best Practices" --category "Tutorial" --quantity 3 --engine openai --openai-model gpt-3.5-turbo --openai-stream
```

Generate a Linux system administration guide:
```sh
python main.py --topic "Linux Administration" --category "Guide" --expertise-level "Advanced" --engine openai --openai-model gpt-4
```

### Ollama Examples

Generate a Kubernetes deployment guide using Llama2:
```sh
python main.py --topic "Kubernetes Deployment" --category "How-to" --quantity 4 --engine ollama --ollama-model llama2 --ollama-host http://localhost:11434
```

Create a Git workflow tutorial with Mistral:
```sh
python main.py --topic "Git Workflows" --category "Tutorial" --quantity 2 --engine ollama --ollama-model mistral --ollama-stream --ollama-no-think
```

### Monitoring

Check if all output formats can be generated:
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

The generator uses a modular prompt system stored in the `adapters/engines/` directory. Here's the structure:

```
adapters/engines/
├── openai_adapter/
│   └── prompts/
│       ├── titles/                    # Prompts for generating chapter titles
│       │   ├── openai.txt            # Default OpenAI titles prompt
│       │   ├── gpt-4.txt             # GPT-4 specific titles prompt
│       │   └── gpt-3.5-turbo.txt     # GPT-3.5 specific titles prompt
│       │
│       └── content/                   # Prompts for generating chapter content
│           ├── openai.txt            # Default OpenAI content prompt
│           ├── gpt-4.txt             # GPT-4 specific content prompt
│           └── gpt-3.5-turbo.txt     # GPT-3.5 specific content prompt
│
└── ollama_adapter/
    └── prompts/
        ├── titles/                    # Prompts for generating chapter titles
        │   ├── llama.txt             # Default Ollama titles prompt
        │   ├── llama2.txt            # Llama2 specific titles prompt
        │   └── mistral.txt           # Mistral specific titles prompt
        │
        └── content/                   # Prompts for generating chapter content
            ├── llama.txt             # Default Ollama content prompt
            ├── llama2.txt            # Llama2 specific content prompt
            └── mistral.txt           # Mistral specific content prompt
```

### Prompt Types

#### 1. Titles Prompt
Located in `prompts/titles/`, this prompt generates the chapter titles and overview. It includes:
- Topic context
- Expertise level requirements
- Category specifications
- Quantity of tips needed
- Format requirements

Example template variables:
```
{{TOPIC}}          # The main topic
{{QUANTITY}}       # Number of chapters to generate
{{CATEGORY}}       # Content category (Guide, Tutorial, etc.)
{{EXPERTISE_LEVEL}} # Target expertise level
{{CONTEXT_NOTE}}   # Context based on expertise level
```

#### 2. Content Prompt
Located in `prompts/content/`, this prompt generates the detailed content for each tip. It includes:
- Topic context
- Chapter title
- Chapter index
- Total chapters
- Expertise level requirements
- Category specifications
- Format requirements

Example template variables:
```
{{TOPIC}}          # The main topic
{{CHAPTER_TITLE}}  # Title of the current chapter
{{CHAPTER_INDEX}}  # Current chapter number
{{TOTAL_CHAPTERS}} # Total number of chapters
{{CATEGORY}}       # Content category
{{EXPERTISE_LEVEL}} # Target expertise level
{{CONTEXT_NOTE}}   # Context based on expertise level
```

### Customizing Prompts

1. **System Template Variables:**
   The following variables are automatically injected by the system and should NOT be modified:
   ```
   {{TOPIC}}          # The main topic
   {{QUANTITY}}       # Number of chapters to generate
   {{CATEGORY}}       # Content category (Guide, Tutorial, etc.)
   {{EXPERTISE_LEVEL}} # Target expertise level
   {{CONTEXT_NOTE}}   # Context based on expertise level
   {{CHAPTER_TITLE}}  # Title of the current chapter
   {{CHAPTER_INDEX}}  # Current chapter number
   {{TOTAL_CHAPTERS}} # Total number of chapters
   ```
   These variables will be automatically replaced with actual values during generation.

2. **Model-Specific Prompts:**
   - For OpenAI:
     - Create a new prompt file named after your model (e.g., `gpt-4.txt`)
     - The generator will automatically use the model-specific prompt if available
     - Falls back to `openai.txt` if no model-specific prompt exists
   - For Ollama:
     - Create a new prompt file named after your model (e.g., `llama2.txt`)
     - The generator will automatically use the model-specific prompt if available
     - Falls back to `llama.txt` if no model-specific prompt exists

3. **Prompt Optimization Tips:**
   - Use clear, specific instructions
   - Include examples of desired output format
   - Specify the tone and style
   - Define any constraints or requirements
   - Add context about the target audience
   - You can move the template variables around in your prompt, but don't modify their names

4. **Example Prompt Structure:**
```markdown
You are an expert in {{TOPIC}} writing for {{EXPERTISE_LEVEL}} level readers.
Generate {{QUANTITY}} {{CATEGORY}} sections about {{TOPIC}}.

Context: {{CONTEXT_NOTE}}

Requirements:
- Each section should be self-contained
- Include practical examples
- Use clear, concise language
- Follow markdown formatting

Format each section as:
## Section Title
[Content with examples and explanations]
```

5. **Testing Prompts:**
   - Use the `--check` flag to test prompt changes
   - Start with a small quantity to verify output
   - Adjust based on the generated content quality
   - Verify that all template variables are being properly replaced

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

## For Developers

### Project Structure

```
ai-knowledge-generator/
├── adapters/                    # Engine and format adapters
│   ├── engines/                # AI engine implementations
│   │   ├── openai_adapter/     # OpenAI implementation
│   │   │   ├── prompts/       # Prompt templates
│   │   │   └── __init__.py    # OpenAI adapter implementation
│   │   └── ollama_adapter/     # Ollama implementation
│   │       ├── prompts/       # Prompt templates
│   │       └── __init__.py    # Ollama adapter implementation
│   └── file_converter.py       # File format conversion
├── core/                       # Core business logic
│   ├── generator.py           # Main generation logic
│   └── ports.py              # Interface definitions
├── tests/                     # Test suite
├── output/                    # Generated content
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── style.css                  # Output styling
```

### Architecture

The project follows a hexagonal architecture (ports and adapters) pattern:

1. **Core Layer**
   - Contains business logic and interfaces
   - Defines ports (interfaces) that adapters must implement
   - Independent of external frameworks and libraries

2. **Adapter Layer**
   - Implements the ports defined in the core
   - Handles external services (AI engines, file conversion)
   - Isolated from core business logic

3. **CLI Layer**
   - Handles user interaction
   - Coordinates between core and adapters
   - Manages configuration and output

### Adding a New Engine

To add a new AI engine, follow these steps:

1. **Create Engine Adapter**
   ```python
   # adapters/engines/new_engine_adapter/__init__.py
   from core.ports import CompletionEnginePort
   
   class NewEngineAdapter(CompletionEnginePort):
       def __init__(self, model: str, **kwargs):
           # Initialize your engine
           pass
           
       def generate(self, topic: str, quantity: int) -> Tuple[List[Tuple[int, Dict[str, str], str]], str]:
           # Implement generation logic
           pass
   ```

2. **Create Prompt Structure**
   ```
   adapters/engines/new_engine_adapter/
   ├── prompts/
   │   ├── titles/
   │   │   ├── default.txt     # Default titles prompt
   │   │   └── model.txt       # Model-specific prompt
   │   └── content/
   │       ├── default.txt     # Default content prompt
   │       └── model.txt       # Model-specific prompt
   ```

3. **Implement Required Methods**
   - `generate()`: Main generation method
   - `build_titles_prompt()`: Build titles prompt
   - `build_detail_prompt()`: Build content prompt
   - `count_tokens()`: Token counting (if applicable)

4. **Add CLI Support**
   ```python
   # In main.py
   parser.add_argument('--new-engine-option', help='New engine specific option')
   ```

### Engine Requirements

To be compatible with the system, an engine must:

1. **Implement the Interface**
   - Must implement `CompletionEnginePort`
   - Must handle all required template variables
   - Must support streaming (optional but recommended)

2. **Prompt Structure**
   - Must support the standard prompt template variables
   - Must have both titles and content prompts
   - Should support model-specific prompts

3. **Error Handling**
   - Must implement proper error handling
   - Must raise appropriate exceptions
   - Should include retry logic for network issues

4. **Configuration**
   - Must support model selection
   - Should support streaming configuration
   - Should support custom parameters

### Development Guidelines

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Document all public methods
   - Include docstrings

2. **Testing**
   - Write unit tests for all new code
   - Include integration tests
   - Test error conditions
   - Test prompt variations

3. **Error Handling**
   - Use custom exceptions
   - Include meaningful error messages
   - Implement proper logging
   - Handle edge cases

4. **Documentation**
   - Update README with new features
   - Document new configuration options
   - Include usage examples
   - Document prompt structure

### Adding New Features

1. **Core Features**
   - Add to core layer first
   - Define interfaces in ports.py
   - Implement in adapters
   - Update CLI interface

2. **Output Formats**
   - Add to file_converter.py
   - Update style.css if needed
   - Add format-specific metadata
   - Update documentation

3. **Prompt Templates**
   - Add new template variables to core
   - Update all engine adapters
   - Update documentation
   - Add examples

### Best Practices

1. **Engine Development**
   - Keep engine-specific code isolated
   - Use dependency injection
   - Implement proper error handling
   - Support configuration via environment variables

2. **Prompt Engineering**
   - Keep prompts modular
   - Use clear instructions
   - Include examples
   - Document template variables

3. **Testing**
   - Test with different models
   - Test with different prompts
   - Test error conditions
   - Test performance

4. **Documentation**
   - Keep README up to date
   - Document all options
   - Include examples
   - Document prompt structure