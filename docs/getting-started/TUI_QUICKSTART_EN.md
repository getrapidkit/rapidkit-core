# 🚀 RapidKit TUI – Quick Start

The RapidKit text user interface gives you a guided workflow for generating projects, installing
modules, and running common tasks—perfect when you’d rather browse than memorize every CLI flag.

## Launch the TUI

```bash
rapidkit --tui

# Inside Poetry or a venv
poetry run rapidkit --tui
```

Use the on-screen hints or press `?` to view available shortcuts. `q` exits from any screen.

## Core Panels

| Panel               | What you can do                                                                  |
| ------------------- | -------------------------------------------------------------------------------- |
| **Create Project**  | Choose the FastAPI standard kit, name your project, and scaffold it in one flow. |
| **Install Modules** | Browse community modules, read summaries, and install into the active project.   |
| **Project Tasks**   | Run curated commands such as tests, lint, format, or database migrations.        |
| **Settings**        | Toggle telemetry prompts, pick default paths, and review CLI configuration.      |

## Keyboard Shortcuts

- `<Tab>` / `<Shift+Tab>` — Move between interactive elements
- `<Enter>` — Confirm selections or run highlighted actions
- `Esc` — Close dialogs and go back
- `q` — Quit the TUI

Context-sensitive hints appear in the footer, so you always know which keys are active.

## Helpful CLI Commands

```bash
# Discover kits and modules outside the TUI
rapidkit list
rapidkit modules

# Scaffold without the TUI
rapidkit create project fastapi.standard MyProject

# Install modules directly
rapidkit add module logging

# Explore documentation links
rapidkit docs
```

Consult `rapidkit --help` for the full command surface. The TUI simply streamlines the most common
flows in a single interface.

______________________________________________________________________

**Tip:** Keep the TUI open alongside your editor to experiment with module combinations while you
build your application.
