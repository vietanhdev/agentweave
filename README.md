# AgentWeave 🧵

AgentWeave is a powerful CLI tool for initializing and managing AI agent projects based on LangGraph, making it easier to build, customize, and deploy sophisticated AI agents.

Think of AgentWeave as a "create-react-app" but for AI agents - it helps you bootstrap a complete project with all the necessary components, configurations, and integrations.

## Features ✨

- **Quick Project Setup**: Initialize complete AI agent projects with a single command
- **Component Management**: Easily add, remove, and update agent components
- **Tool Integration**: Add and configure agent tools from a growing library of predefined tools
- **LangGraph Integration**: Built on top of LangGraph for powerful agent orchestration
- **Monitoring & Visualization**: Built-in components for monitoring, debugging, and visualizing agent behavior
- **Memory Management**: Easy integration of different memory solutions
- **Service Integrations**: Connect to various external services and APIs
- **Extensible Architecture**: Design focused on extensibility and customization
- **FastAPI Backend**: Well-structured FastAPI backend for serving your agents

## Installation 🚀

```bash
pip install agentweave
```

## Quick Start 🏁

```bash
# Initialize a new agent project
agentweave init {{project_name}}

# Change to the project directory
cd {{project_name}}

# Edit .env to add OpenAI key

# Install the environment (sets up dependencies)
agentweave install_env

# Run your agent in development mode
agentweave run
```

![Screenshot of Example project](https://raw.githubusercontent.com/vietanhdev/agentweave/refs/heads/main/screenshots/example-project.png)

## Environment Setup 🔐

After initializing your project, make sure to:

1. Find the `.env.example` file in your project
2. Copy it to `.env`
3. Update the values in `.env` with your API keys and configuration

This step is essential for your agent to function properly with external services.

## Project Commands 📝

### Core Commands

```bash
# Initialize a new agent project
agentweave init [project-name]

# Run your agent in development mode
agentweave run

# Run the agent in development mode with hot reloading
agentweave dev

# Install environment dependencies
agentweave install_env
```

### Utility Commands

```bash
# Display version information
agentweave version

# Display general information about AgentWeave
agentweave info
```

## Project Structure 📂

```
{{project_name}}/
├── agents/              # Agent definitions
├── tools/               # Custom tools
├── templates/           # Templates for agents and tools
├── memory/              # Memory configurations
├── monitoring/          # Monitoring and visualization
├── frontend/            # UI for interacting with agents
├── config/              # Configuration files
├── README.md            # Project documentation
└── agentweave.yaml      # AgentWeave configuration
```

## Extensibility 🔌

AgentWeave is designed to be highly extensible:

- Create custom templates for new project types
- Develop and share custom tools
- Create plugins for new functionalities
- Integrate with various AI services and platforms

## Dependencies

AgentWeave is built using:

- LangGraph v0.0.30+ for agent orchestration
- FastAPI for the backend API
- Typer and Click for the CLI interface
- Rich for beautiful terminal output
- Jinja2 for template rendering
- And more!

## Contributing 🤝

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License 📄

AgentWeave is open source software [licensed as MIT](LICENSE).
