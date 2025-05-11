# Contributing to AgentWeave

Thank you for considering contributing to AgentWeave! This document outlines the process for contributing to the project and helps you get started.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:

- Check the issue tracker to avoid duplicates
- Gather information about your environment (OS, Python version, etc.)
- Provide clear steps to reproduce the issue

For bug reports, please use the following template:

```
**Description:**
A clear description of the bug

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. ...

**Expected Behavior:**
What you expected to happen

**Actual Behavior:**
What actually happened

**Environment:**
- OS: [e.g., Windows 10, macOS 11.4]
- Python Version: [e.g., 3.9.5]
- AgentWeave Version: [e.g., 0.1.0]
```

### Suggesting Features

For feature requests, please:

- Clearly describe the feature
- Explain why it would be valuable
- Provide examples of how it might work

### Pull Requests

1. Fork the repository
2. Create a new branch from `main`
3. Make your changes
4. Add or update tests as needed
5. Ensure all tests pass
6. Submit a pull request against the `main` branch

#### Commit Messages

Please use clear, descriptive commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests after the first line

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip

### Installation for Development

```bash
# Clone your fork of the repository
git clone https://github.com/YOUR-USERNAME/agentweave.git
cd agentweave

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## Adding New Components

### Adding a New Tool

1. Create a new file in `agentweave/templates/tools`
2. Implement the tool interface
3. Add documentation
4. Add tests

### Adding a New Agent Template

1. Create a new template in `agentweave/templates/agents`
2. Implement the required methods
3. Update the template registry
4. Add tests

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a new GitHub release
4. CI will automatically publish to PyPI

## Questions?

If you have any questions, feel free to open an issue or reach out to the maintainers.

Thank you for contributing to AgentWeave!
