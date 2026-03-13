# Ronin

A powerful coding agent built with LangChain that can assist with various programming tasks using AI models like Gemini and Ollama.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ronin
```

### 2. Create a Virtual Environment

Create and activate a Python virtual environment to isolate project dependencies:

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Select Python Interpreter (VS Code)

If using VS Code:
1. Open the project folder in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) to open the command palette
3. Type "Python: Select Interpreter" and select it
4. Choose the interpreter from your virtual environment (should show something like `./venv/bin/python` or `./venv/Scripts/python.exe`)

### 4. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install all the necessary dependencies including:
- LangChain for AI orchestration
- Rich for console output
- Typer for CLI interface
- Various AI model integrations
- And other supporting libraries

### 5. Environment Configuration

Create a `.env` file in the project root and configure your AI model settings:

```bash
# For Gemini (default)
MODEL=gemini
MODEL_NAME=gemini-pro  # or your preferred Gemini model

# For Ollama
# MODEL=ollama
# OLLAMA_MODEL=deepseek-coder  # or your preferred Ollama model
```

## Usage

### Command Line Interface

Run the coding agent with a task:

```bash
python cli.py "Create a Python function to calculate fibonacci numbers"
```

### Available Options

- `--help`: Show help information
- `task`: The coding task you want the agent to perform

## Configuration

The agent supports multiple AI models:

- **Gemini**: Google's AI model (requires API key)
- **Ollama**: Local AI models via Ollama

Configure your preferred model in the `.env` file as shown in the setup section.

## Project Structure

- `agent.py`: Main agent implementation
- `cli.py`: Command-line interface
- `tools.py`: Available tools for the agent
- `prompts.py`: System prompts and templates
- `router.py`: Model routing logic
- `requirements.txt`: Python dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]
