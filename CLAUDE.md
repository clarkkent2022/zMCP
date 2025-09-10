# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is an MCP Chatbot with Research Server project that provides academic paper search and management capabilities via the Model Context Protocol (MCP). The project consists of three main Python components:

1. **Research Server** (`research_server.py`) - MCP server providing arXiv paper search, storage, and management
2. **MCP Chatbot** (`mcp_chatbot.py`) - Interactive command-line interface that connects to multiple MCP servers
3. **Main Entry** (`main.py`) - Simple entry point that prints "Hello from zMCP"

The architecture uses FastMCP for the server implementation and integrates with multiple MCP servers including filesystem, research, and fetch capabilities.

## Common Development Commands

### Environment Setup
```bash
pip install -r requirements.txt
```

Recommended using `uv`:
```bash
uv pip install -r requirements.txt
```

### Running the Application
```bash
# Start research server (in one terminal)
uv run research_server.py

# Start chatbot interface (in another terminal)  
uv run mcp_chatbot.py

# Simple entry point
python main.py
```

### Required Environment Variables
```bash
export ANTHROPIC_API_KEY="your_anthropic_key"
```

## Key Implementation Details

### MCP Server Pattern (research_server.py)
Uses FastMCP framework with decorators:
- `@mcp.tool()` for tool registration (search_papers, extract_info)
- `@mcp.resource()` for resource endpoints (papers://folders, papers://{topic})
- `@mcp.prompt()` for prompt templates (generate_search_prompt)
- `@log_call` decorator for comprehensive function call logging

### Data Storage Structure
- Papers stored in `papers/` directory organized by topic
- Each topic gets a subfolder with `papers_info.json` containing paper metadata
- Topics are normalized (lowercase, spaces to underscores)

### Tool Functionality
- `search_papers(topic, max_results)`: Searches arXiv and stores results locally
- `extract_info(paper_id)`: Retrieves stored information for specific paper
- `generate_search_prompt(topic, num_papers)`: Creates structured prompts for paper analysis

### Chatbot Integration
The chatbot connects to multiple MCP servers via `server_config.json`:
- **research**: Local research server for arXiv paper management
- **filesystem**: NPM-based filesystem server for file operations  
- **fetch**: Web content fetching capabilities
- Uses Anthropic Claude 3.5 Sonnet for natural language processing
- Supports special syntax: `@folders`, `@topic`, `/prompts`, `/prompt <name>`

### Resource URI Patterns
- `papers://folders` - Lists all available paper topics
- `papers://{topic}` - Shows detailed paper information for specific topic

## External Dependencies

### arXiv API
- Uses `arxiv` Python library for paper search and metadata retrieval
- Searches by relevance, stores title, authors, summary, PDF URL, and publication date
- No authentication required

### Anthropic API
- Powers the conversational interface with Claude 3.5 Sonnet
- Maintains conversation history and handles tool execution workflow

## Logging and Debugging
- Comprehensive colored logging with timestamps for all function calls
- Execution time tracking for performance monitoring
- Error handling with detailed logging for debugging