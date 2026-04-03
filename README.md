# I_can_help

Local Linux screenshot tool with hotkey trigger, OpenAI image analysis, logs, and saved text responses.

## Features

- Captures the screen into a chosen folder
- Sends the screenshot to OpenAI
- Saves model responses as `.txt` and `.json`
- Writes application logs to `logs/`
- Can be connected to global hotkeys through `sxhkd`

## Project structure

- `images/` — screenshots
- `responces/` — model outputs
- `logs/` — logs
- `prompts/` — prompt templates
- `scripts/` — Python source code

## Setup

### 1. Clone the project

```bash
git clone <your_repo_url>
cd I_can_help