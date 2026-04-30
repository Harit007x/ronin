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

### 2. Run Global Setup

To start assisting on codebases in separate workspace environments without redundant installations, use our 1-shot global installers.

**Note:** Ensure you exit any internal virtual environments (run `deactivate`) before running the installer.

**For Windows:**
Open Windows Command Prompt in the cloned folder and run:
```cmd
install.bat
```
The standalone installer verifies dependencies, embeds scripts natively on your Windows PATH variables, and builds profile states securely.

**For macOS / Linux:**
Open your terminal in the cloned folder and run:
```bash
chmod +x install.sh
./install.sh
```
This script detects your environment, installs dependencies, configures your PATH, and sets up your credentials.

### 3. Global API Routing Configuration

The setup scripts will prompt you for your API key. If you prefer to configure it manually, edit the following file:

- **Windows:** `%USERPROFILE%\.ronin\.env`
- **macOS / Linux:** `~/.ronin/.env`

```env
MODEL=gemini
MODEL_NAME=gemini-3-flash
GEMINI_API_KEY=<your_api_key_here>
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
