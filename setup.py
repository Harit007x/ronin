from setuptools import setup, find_packages

setup(
    name="ronin-cli",
    version="0.1.0",
    py_modules=["agent", "cli", "prompts", "router", "tools"],
    install_requires=[
        "typer>=0.12.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "langchain-core>=0.1.0",
        "langchain-google-genai>=1.0.0",
        "duckduckgo-search>=5.0.0"
    ],
    entry_points={
        "console_scripts": [
            "ronin=cli:main",
        ],
    },
)
