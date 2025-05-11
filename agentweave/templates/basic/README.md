# {{ project_name }}

An AI agent built with AgentWeave

This project was created with [AgentWeave](https://github.com/yourusername/agentweave), a powerful CLI tool for initializing and managing AI agent projects based on LangGraph.

## Project Structure

```
{{ project_name }}/
├── agents/              # Agent definitions
├── tools/               # Custom tools
├── memory/              # Memory configurations
├── backend/             # FastAPI backend
│   ├── main.py          # Main application entry point
│   ├── routers/         # API routers
│   └── utils/           # Utility functions
├── frontend/            # UI (if applicable)
├── config/              # Configuration files
└── agentweave.yaml      # AgentWeave configuration
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher (if using frontend)

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

### Example Tools

This project includes example tools to get you started. You can find them in the `tools/` directory.

## Running the Project

To run the project in development mode:

```bash
agentweave run
```

This will start both the backend and frontend servers.

To run only the backend:

```bash
agentweave run --backend-only
```
