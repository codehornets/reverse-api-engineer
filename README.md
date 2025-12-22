# Reverse API

`reverse-api` is a Python package designed to simplify the process of reverse-engineering APIs by capturing network traffic using Playwright and HAR files, and automatically generating client scripts using AI.

## Features

- **Browser Automation**: Use Playwright to interact with web applications.
- **HAR Recording**: Capture all network traffic in HTTP Archive (HAR) format.
- **AI-Powered Generation**: Automatically generate Python scripts for reverse-engineered APIs using Claude.
- **CLI & TUI**: Easy-to-use command-line and terminal user interfaces.
- **Integrated Scripts**: Organizes generated scripts with clear documentation and requirements.

## Installation

This project uses `uv` for dependency management.

```bash
# Clone the repository
git clone https://github.com/kalil0321/reverse-api.git
cd reverse-api

# Install dependencies
uv sync
```

## Usage

### Browser Recording

To start a recording session:

```bash
uv run reverse-api
```

### Script Generation

After recording, generate a script from the captured HAR file:

```bash
uv run reverse-api engineer path/to/recording.har
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
