# Scout-Edge: AI Trend Tracking System

Scout-Edge is a Python-based toolkit designed to collect the latest trends in the Artificial Intelligence (AI) field from various sources like ArXiv papers, GitHub repositories, and web news. It utilizes Large Language Models (LLMs) like OpenAI's GPT to analyze this collected data.

## Features

*   **Multi-Source Data Collection:** Gathers trend data from ArXiv, GitHub, and the web (via Serper API).
*   **LLM-Powered Analysis:** Uses LLMs (e.g., OpenAI) to summarize collected data and identify key themes.
*   **Flexible CLI Interface:** Offers easy interaction through the command line (`collect`, `analyze`, `interactive` modes).
*   **Configurable:** Manages API keys and other settings via a `.env` file.

## Requirements

*   Python 3.9 or higher
*   Pip (Python package installer)
*   API Keys (see Configuration)

## Installation

There are two main ways to set up and run Scout-Edge:

**Method 1: Using a Virtual Environment (Recommended for Development)**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/egeyavuzcan/scout-edge # Replace with your repo URL
    cd scout-edge
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies from `requirements.txt`:**
    *   *(Note: Ensure `requirements.txt` is up-to-date. If you primarily use `pyproject.toml`, you might generate `requirements.txt` using tools like `pip-tools` or manually list essential runtime dependencies).* 
    *   If `requirements.txt` exists and is maintained:
        ```bash
        pip install -r requirements.txt 
        ```
    *   Alternatively, install directly from `pyproject.toml` within the environment:
        ```bash
        pip install . 
        ```

4.  **Configure API Keys:** (See Configuration section below)

5.  **Run the CLI:**
    ```bash
    python -m src.ui.cli --help 
    python -m src.ui.cli collect --sources arxiv github news
    python -m src.ui.cli analyze --file data/collected_trends_YYYY-MM-DD_HHMMSS.json
    ```

**Method 2: Installing as a Package (System-wide or User-level)**

This method installs Scout-Edge like any other Python package, making the `scout-edge` command available directly in your terminal (if the installation location is in your system's PATH).

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/egeyavuzcan/scout-edge # Replace with your repo URL
    cd scout-edge
    ```

2.  **Install the package:**
    ```bash
    pip install . 
    ```
    *   *(Optional: Use `pip install -e .` for an editable install if you plan to modify the code directly after installation).* 

3.  **Configure API Keys:** 
    *   Create a `.env` file in the directory where you will *run* the `scout-edge` command, or ensure the environment variables are set globally. The application will look for a `.env` file in the current working directory when executed.

4.  **Run the CLI:**
    *   *(Note: This assumes the installation script correctly sets up the entry point in `pyproject.toml`. We need to add this entry point.)*
    *   Assuming the entry point is configured (see **Adding CLI Entry Point** below):
        ```bash
        scout-edge --help
        scout-edge collect --sources arxiv github news
        scout-edge analyze --file data/collected_trends_YYYY-MM-DD_HHMMSS.json 
        ```

### Adding CLI Entry Point (Required for Method 2)

To make the `scout-edge` command work after installation (Method 2), you need to define a script entry point in your `pyproject.toml` file. Add the following section under `[project]`: 

```toml
[project.scripts]
scout-edge = "src.ui.cli:main"
```

Make sure your `src/ui/cli.py` file has a `main()` function that parses arguments and runs the appropriate commands.

## Configuration

Scout-Edge requires API keys for its various services. These keys must be stored in a file named `.env` in the project's root directory.

1.  **Copy `.env.example`:** Copy or rename the `.env.example` file (located in the project directory) to `.env`.

2.  **Edit `.env`:** Open the `.env` file and paste your API keys into the corresponding fields:

    ```dotenv
    # OpenAI API Key (Required for analysis)
    OPENAI_API_KEY=sk-...

    # GitHub API Key (Recommended for GitHub trends, increases rate limits)
    GITHUB_API_KEY=github_pat_...

    # Serper API Key (Required for Google search and news)
    SERPER_API_KEY=...

    # HuggingFace API Key (Optional, for future features)
    # HUGGINGFACE_API_KEY=hf_...

    # --- Other Settings --- 
    # LLM model to use (e.g., gpt-3.5-turbo, gpt-4)
    LLM_MODEL=gpt-3.5-turbo
    LLM_TEMPERATURE=0.7

    # Vectorstore path (Optional, for future features)
    VECTORSTORE_PATH=./data/vectorstore

    # Max results for ArXiv and GitHub
    ARXIV_MAX_RESULTS=10
    GITHUB_MAX_RESULTS=10

    # Verbose logging mode (true/false)
    VERBOSE_MODE=true

    # Directory to store data files
    DATA_DIR=./data
    ```

    **Where to Get API Keys:**
    *   **OpenAI:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
    *   **GitHub:** [https://github.com/settings/tokens](https://github.com/settings/tokens) (Create a Personal Access Token - Classic, `public_repo` scope is sufficient)
    *   **Serper:** [https://serper.dev/](https://serper.dev/) (For Google search results)

## Usage

Scout-Edge is primarily used via the `scout-edge` command. The main commands are `collect` and `analyze`. The easiest way to use it is through the interactive mode.

**Interactive Mode:**

Launch the interactive mode for the most comprehensive usage:

```bash
scout-edge interactive
```

In this mode, you can use the following commands:

*   `collect`: Starts the data collection process.
*   `analyze`: Analyzes previously collected data.
*   `exit` / `quit`: Exits the interactive mode.
*   Other input: Sent directly as a query to the LLM Agent (this feature might not be fully developed yet).

**1. Data Collection (`collect`)**

This command gathers current trend data from ArXiv, GitHub, and the web based on the queries you provide.

*   **Interactive Mode Example:**
    ```
    > collect
    ArXiv query [artificial intelligence]: LLM agents
    GitHub query [machine learning]: large language model applications
    News query [AI trends]: AI impact on software development
    Max results per source [10]: 5 
    Collecting trend data, please wait...
    # ... (collection logs) ...
    Save results to file? (y/n): y
    Filename [trends.json]: my_llm_trends.json 
    ```
    *   The command prompts you for search queries for each source and the maximum number of results per source.
    *   You can press Enter to use the default values.
    *   The collected data is saved in JSON format to the specified file (default: `trends.json`).

**2. Data Analysis (`analyze`)**

This command reads a JSON file previously saved by the `collect` command and analyzes its content using the configured LLM.

*   **Interactive Mode Example:**
    ```
    > analyze
    Input file with trend data: my_llm_trends.json 
    Analysis type (brief, comprehensive, technical, business) [comprehensive]: 
    Analyzing trends, please wait...
    # ... (analysis logs and result) ...
    Save results to file? (y/n): y
    Filename [analysis.json]: my_llm_analysis.json
    ```
    *   The command asks for the name of the data file to analyze.
    *   It prompts for an analysis type (currently more for informational purposes).
    *   The analysis summary generated by the LLM is printed to the console.
    *   You can save the results to the specified file (default: `analysis.json`).

**(Direct Commands - Non-Interactive)**

Future development could enable direct `collect` and `analyze` operations with arguments from the command line.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (if available).
