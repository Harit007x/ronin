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

### 2. Run Global Setup (Windows)

To start assisting on codebases in separate workspace environments without redundant installations:

1. Exit internal virtual sandboxes (`deactivate`).
2. Open Windows Command Prompt in the cloned folder and run:
   ```cmd
   install.bat
   ```

The standalone installer verifies dependencies, embeds scripts natively on your Windows PATH variables, and builds profile states securely.

### 3. Global API Routing fallback
Configure underlying platform routes under:
`C:\Users\ADMIN\.ronin\.env`

```env
MODEL=gemini
MODEL_NAME=gemini-3-flash
GEMINI_API_KEY=<key>
```

## Usage

Run task actions anywhere in separate codebase directories:

```bash
ronin "Create integration tests for core logic"
```

Modify underlying back-end connections:
```bash
ronin current-model
```




## Project Structure

- `ronin_cli/agent.py`: Main execution workflows
- `ronin_cli/cli.py`: Typer parameters mapping
- `ronin_cli/tools.py`: Automated local helper routines
- `ronin_cli/prompts.py`: Context payloads
- `ronin_cli/router.py`: Network integrations


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]
