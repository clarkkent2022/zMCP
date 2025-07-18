# MCP Chatbot with Research Server

A chatbot that interfaces with MCP (Model Context Protocol) servers to provide research paper search and management capabilities.

## Features

- Interactive chat interface with command history and tab completion
- Integration with MCP servers for paper search and management
- Support for custom prompts and commands
- Built with Python and Anthropic's Claude API

## Prerequisites

- Python 3.8+
- `uv` package manager (recommended)
- Anthropic API key

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Or using `uv` (recommended):
   ```bash
   uv pip install -r requirements.txt
   ```

4. Create a `.env` file with your API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

1. Start the research server in one terminal:
   ```bash
   uv run research_server.py
   ```

2. In another terminal, start the chatbot:
   ```bash
   uv run mcp_chatbot.py
   ```

## Available Commands

- `@folders` - List available paper topics
- `@<topic>` - Search papers in a specific topic
- `/prompts` - List available prompts
- `/prompt <name> <args>` - Execute a specific prompt
- `quit` - Exit the chatbot

## Project Structure

- `mcp_chatbot.py` - Main chatbot application
- `research_server.py` - MCP server for paper research
- `server_config.json` - Configuration for MCP servers
- `main.py` - Simple entry point
- `papers/` - Directory for storing paper data

## License

MIT
