#!/bin/bash

echo "========================================"
echo "  RONIN GLOBAL INSTALLER (macOS/Linux)"
echo "========================================"

# 1. Check for Virtual Environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo ""
    echo "[!] WARNING: You are running inside a virtual environment: $VIRTUAL_ENV"
    echo "To make 'ronin' accessible globally everywhere across your computer,"
    echo "please type 'deactivate' and re-run this installer."
    echo ""
    read -p "Press [Enter] to exit..."
    exit 1
fi

# Detect python command
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[!] Python is not installed or not in PATH."
    exit 1
fi

echo ""
echo "[1/4] Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

echo ""
echo "[2/4] Installing dependencies & standalone package..."
$PYTHON_CMD -m pip install -e .

echo ""
echo "[3/4] Ensuring command is on your system PATH..."
# Find Python's bin directory
PYTHON_BIN_DIR=$($PYTHON_CMD -c "import sys, os; print(os.path.join(sys.prefix, 'bin'))")

echo "Python bin directory: $PYTHON_BIN_DIR"

if [[ ":$PATH:" != *":$PYTHON_BIN_DIR:"* ]]; then
    echo "Adding directory to User PATH..."
    
    # Try to determine the shell profile file
    SHELL_PROFILE=""
    if [[ "$SHELL" == *"zsh"* ]] || [ -n "$ZSH_VERSION" ]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]] || [ -n "$BASH_VERSION" ]; then
        if [ -f "$HOME/.bash_profile" ]; then
            SHELL_PROFILE="$HOME/.bash_profile"
        else
            SHELL_PROFILE="$HOME/.bashrc"
        fi
    else
        # Default to .profile
        SHELL_PROFILE="$HOME/.profile"
    fi

    echo "" >> "$SHELL_PROFILE"
    echo "# Added by Ronin Installer" >> "$SHELL_PROFILE"
    echo "export PATH=\"\$PATH:$PYTHON_BIN_DIR\"" >> "$SHELL_PROFILE"
    
    echo ""
    echo "[*] Added to PATH persistently in $SHELL_PROFILE."
    echo "    NOTE: You MUST restart your terminal or run 'source $SHELL_PROFILE' for this to take effect."
else
    echo "[*] Directory is already present on system PATH."
fi

echo ""
echo "[4/4] Configuring Global credentials..."
read -p "Paste your GEMINI_API_KEY (leave blank to skip): " API_KEY

CONFIG_DIR="$HOME/.ronin"
CONFIG_FILE="$CONFIG_DIR/.env"

if [ -n "$API_KEY" ]; then
    mkdir -p "$CONFIG_DIR"
    echo "MODEL=gemini" > "$CONFIG_FILE"
    echo "MODEL_NAME=gemini-3-flash" >> "$CONFIG_FILE"
    echo "GEMINI_API_KEY=$API_KEY" >> "$CONFIG_FILE"
    echo "Global credentials saved successfully to $CONFIG_FILE"
else
    echo "Skipping key configuration."
fi

echo ""
echo "========================================"
echo "  SUCCESS! Setup Complete."
echo "  Close this window, open a NEW terminal, and run:"
echo "  ronin \"your prompt\""
echo "========================================"
