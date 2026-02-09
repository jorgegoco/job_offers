# My DOE - AI-Powered Workflow Automation

A multi-workflow automation system using a 3-layer architecture to separate instructions, decision-making, and deterministic execution.

## Architecture

This project follows a 3-layer architecture that separates concerns for maximum reliability:

### Layer 1: Directives (What to do)
- SOPs written in Markdown, live in `directives/`
- Define goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions

### Layer 2: Orchestration (Decision making)
- AI agent reads directives and makes intelligent routing decisions
- Calls execution tools in the right order
- Handles errors and asks for clarification

### Layer 3: Execution (Doing the work)
- Deterministic Python scripts in `execution/`
- Handle API calls, data processing, file operations
- Reliable, testable, fast

**Why this works:** Pushes complexity into deterministic code. AI focuses on decision-making, not execution.

For detailed architecture documentation, see: `CLAUDE.md`

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
ANTHROPIC_API_KEY=your_actual_key_here
```

Get your API key from: https://console.anthropic.com/

### 3. Choose a workflow

Navigate to the workflow you want to use. Each workflow has its own resources folder with specific instructions.

## Available Workflows

### Job Application Generator
**Location:** `resources/job_applications/`
**Purpose:** Generate tailored CVs and cover letters for specific job offers

**Features:**
- Auto-detects job language (Spanish/English/etc.)
- Intelligent CV caching (saves time and API costs)
- Iterative refinement workflow
- Custom cover letter lengths
- Emoji-enhanced headers

**Quick Start:** See `resources/job_applications/README.md`
**Detailed Guide:** See `directives/job_application_generator.md`

---

*More workflows coming soon...*

## Project Structure

```
.
├── directives/              # Workflow instructions (SOPs)
│   └── *.md                # Detailed workflow documentation
├── execution/               # Python scripts (deterministic tools)
│   ├── utils/              # Shared utility modules
│   └── *.py                # Workflow-specific scripts
├── resources/               # Resources organized by workflow
│   └── [workflow_name]/    # Each workflow has its own subdirectory
│       ├── README.md       # Workflow-specific quick start
│       └── ...             # Workflow resources
├── output/                  # Final outputs organized by workflow
│   └── [workflow_name]/    # Generated deliverables
├── .tmp/                    # Intermediate files organized by workflow
│   └── [workflow_name]/    # Temporary processing files
├── .env                     # API keys (create from .env.example)
├── CLAUDE.md               # Architecture documentation
└── README.md               # This file
```

## Usage

### With AI Agent

Simply tell the AI agent which workflow you want to run. The agent will:
1. Read the directive for that workflow
2. Ask for necessary inputs
3. Run the appropriate scripts
4. Show you previews and wait for approval
5. Generate final outputs

### Manual Execution

Each workflow can also be run manually via Python scripts. See individual workflow READMEs for specific commands.

## Adding New Workflows

To add a new workflow:

1. Create directive: `directives/your_workflow.md`
2. Create execution scripts: `execution/your_workflow_*.py`
3. Create resource directory: `resources/your_workflow/`
4. Add README: `resources/your_workflow/README.md`
5. Outputs will automatically go to: `output/your_workflow/`

The directory structure automatically organizes everything by workflow.

## Key Principles

1. **Check for tools first** - Before writing code, check `execution/` for existing scripts
2. **Self-anneal when things break** - Fix errors, update tools, improve directives
3. **Update directives as you learn** - Directives are living documents
4. **Deliverables in cloud, intermediates local** - Final outputs should be accessible (PDFs, Sheets, etc.)
5. **Deterministic execution** - Complex logic goes in Python scripts, not AI decisions

## Benefits

- **Scalable**: Easy to add new workflows without affecting existing ones
- **Reliable**: Deterministic execution reduces errors
- **Cost-effective**: Caching and optimization reduce API costs
- **Organized**: Clear separation between workflows
- **Maintainable**: Updates to one workflow don't break others

## Contributing

When adding features:
- Update the relevant directive in `directives/`
- Modify or create scripts in `execution/`
- Update the workflow-specific README
- Test thoroughly before committing
- Document learnings in the directive

## License

Private project for personal use.
