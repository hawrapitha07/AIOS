# AIOS - AI Application Development Operating Environment

AIOS is a Python-based AI application development environment/platform that provides a standardized way to configure and run AI applications.

## Features

- **Workflow-based Architecture**: Build AI applications as reusable workflows
- **Model Provider Abstraction**: Switch between different LLM providers (mock, OpenAI, Ollama)
- **Interactive CLI**: Easy-to-use command line interface
- **Project Scaffolding**: Quickly create new AIOS projects
- **Extensible Design**: Add new workflows, models, knowledge sources, and tools
- **Type Hints & Documentation**: Well-typed and documented codebase

## Architecture

```
                    AIOS
                      |
              Workflow Manager
                      |
                Agent Runtime
                      |
       +--------------+--------------+
       |              |              |
     Model         Knowledge        Tools
    Manager         Manager        Manager
       |              |              |
       +--------------+--------------+
                      |
                 AI Workflow
```

## Installation

```bash
# Clone the repository
git clone https://github.com/example/aios.git
cd aios

# Install in development mode
pip install -e .

# Verify installation
aios --help
```

## Quick Start

### Create a new project

```bash
aios create myproject
cd myproject
pip install -e .
```

### Run the chatbot workflow

```bash
aios workflow run chatbot
```

Example interaction with mock provider:
```
AIOS Chatbot
Provider: mock | Model: default
Type 'exit' to quit.

You: Hello
AIOS: Mock response #1 to: 'Hello'

You: What is AI?
AIOS: Mock response #2 to: 'What is AI?'

You: exit
Goodbye!
```

### Using Ollama provider

1. Install and run Ollama locally (https://ollama.com)
2. Pull a model: `ollama pull llama3.2:3b`
3. Configure your project to use Ollama:
   ```bash
   aios create my-ollama-project
   cd my-ollama-project
   ```
4. Edit `aios.yaml`:
   ```yaml
   model:
     provider: ollama
     name: llama3.2:3b
   workflow:
     name: chatbot
   ```
5. Run the chatbot: `aios workflow run chatbot`

### Check status

```bash
aios status
```

## Configuration

AIOS uses YAML configuration files. By default, it looks for `aios.yaml` in the current directory.

Example `aios.yaml`:
```yaml
name: my-aios-app

model:
  provider: mock
  name: default

workflow:
  name: chatbot
```

For OpenAI provider:
```yaml
name: my-aios-app

model:
  provider: openai
  name: gpt-4o-mini

workflow:
  name: chatbot
```

For Ollama provider:
```yaml
name: my-aios-app

model:
  provider: ollama
  name: llama3.2:3b

workflow:
  name: chatbot
```

Environment variables should be used for secrets:
```bash
OPENAI_API_KEY=your_api_key_here
OLLAMA_BASE_URL=http://localhost:11434  # Optional, defaults to localhost:11434
```

## Available Commands

```bash
# Project management
aios create <project_name> [--dir <directory>]

# Workflow management
aios workflow list
aios workflow run <workflow_name>

# Model management
aios model list

# System information
aios status
```

## Workflows

### Chatbot Workflow

The chatbot workflow provides an interactive terminal conversation with:
- Conversation history
- Configurable system prompt
- Exit commands (exit, quit, bye)
- Model provider abstraction (mock, OpenAI, Ollama)

## Extending AIOS

### Adding a New Workflow

1. Create a new directory in `aios/workflows/` (e.g., `research/`)
2. Create `__init__.py` in the directory
3. Create `workflow.py` implementing the `BaseWorkflow` interface
4. Optionally create `config.py` for workflow-specific configuration
5. The workflow will be automatically discovered and registered

Example workflow structure:
```
aios/
â””â”€â”€ workflows/
    â””â”€â”€ research/
        â”œâ”€â”€ __init__.py
        â”œâ”€â”€ workflow.py
        â””â”€â”€ config.py
```

### Adding a New Model Provider

1. Create a new provider file in `aios/models/providers/` (e.g., `anthropic_provider.py`)
2. Implement the `BaseModel` abstract class
3. Add the provider to the `ModelManager` provider classes
4. Update documentation

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_cli.py
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
## Developer Agent

AIOS includes a Developer Agent that can understand natural-language commands to perform common development tasks.

### Example Usage

```bash
aios "change my model to llama3.2:3b"
aios "what model is my project using?"
aios "what workflows are available?"
aios "create a workflow called research"
```

### How It Works

The Developer Agent uses the configured AIOS model (e.g., Ollama with llama3.2:3b) to interpret natural language requests. It returns a structured intent that is validated and executed through AIOS's existing operation layer (e.g., ModelManager, WorkflowManager). The LLM does not directly modify files; AIOS validates and executes the requested operation.

### Supported Commands

- Change model: `aios "change my model to <provider>:<name>"`
- Change model provider: `aios "use <provider> for my model"`
- Show current status: `aios "what model is my project using?"`
- List workflows: `aios "what workflows are available?"`
- Create workflow: `aios "create a workflow called <name>"`
- Remove workflow: `aios "remove the workflow called <name>"` (requires confirmation)
- List models: `aios "what models are available?"`

### Architecture

```
Natural Language
        |
AIOS CLI
        |
Developer Agent
        |
LLM (via ModelManager)
        |
Structured Intent
        |
Validation
        |
AIOS Operation Layer
        |
Managers (ModelManager, WorkflowManager, etc.)
        |
AIOS Project (aios.yaml)
```
