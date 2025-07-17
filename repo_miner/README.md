# GitHub Repository Miner

This project is a Python-based tool designed to mine GitHub repositories based on specific criteria. It automatically handles API rate limits, pagination, and processes data in batches to find repositories that match a defined profile (e.g., language, minimum stars, issue resolution time).

## Features

- **Criteria-Based Searching**: Finds repositories using a combination of language, minimum stars, and other metrics.
- **Adaptive Search**: Bypasses the GitHub API's 1000-result limit by adaptively adjusting search queries.
- **Batch Processing**: Mines and saves data in manageable batches, allowing the process to be stopped and resumed.
- **Progress Management**: Automatically saves and loads progress, so you can continue where you left off.
- **Data Consolidation**: Merges all batch results into final JSON and CSV files.
- **Post-Processing**: Applies quality filters to the consolidated data to create a categorized dataset.
- **Cross-Platform**: Includes execution scripts for both Windows and Linux/macOS.

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python**: Version 3.8 or higher.
2.  **uv**: A fast Python package installer and resolver. If you don't have it, you can install it by following the official instructions:
    - **[uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)**

## Setup

Follow these steps to get your development environment set up:

1.  **Clone the repository:**
    ```sh
    git clone <your-repository-url>
    cd pr-repo-minner
    ```

2.  **Configure your environment:**
    - This project uses a `.env` file for configuration. A template is provided in `.env.example`.
    - Create your own `.env` file by copying the example:
      ```sh
      # On Windows (Command Prompt)
      copy .env.example .env

      # On Linux/macOS
      cp .env.example .env
      ```
    - **Crucial:** Open the newly created `.env` file and add your **GitHub Personal Access Token** to the `GITHUB_TOKEN` variable. This is required to interact with the GitHub API.

3.  **Install dependencies:**
    - The `uv run` command used in the execution scripts will automatically detect your `requirements.txt` or `pyproject.toml` and install the necessary dependencies in a virtual environment. No manual installation step is needed.

## How to Run

Execution scripts are provided for convenience. They handle the process of running the main application using `uv`.

-   **On Windows:**
    Open a terminal and run the batch script:
    ```sh
    run.bat
    ```
    Alternatively, you can double-click the `run.bat` file in the File Explorer.

-   **On Linux or macOS:**
    First, make the script executable, then run it:
    ```sh
    chmod +x run.sh
    ./run.sh
    ```

The script will start the mining process, showing progress in the terminal. If stopped, you can simply run the script again to resume.

## Configuration

All major settings can be adjusted in the `.env` file:

-   `GITHUB_TOKEN`: Your personal GitHub API token.
-   `SEARCH_LANGUAGE`: The programming language to search for (e.g., `java`, `python`).
-   `MIN_STARS`: The minimum number of stars a repository must have.
-   `MAX_ISSUE_CLOSE_DAYS`: The maximum average time (in days) for issues to be closed.
-   `TOTAL_TARGET_REPOS`: The total number of unique, accepted repositories to mine before stopping.
-   `BATCH_SIZE`: The number of repositories to process in each batch.

## Project Structure

```
.
├── .data/                # Internal data for progress tracking
├── exporters/            # Modules for exporting data (JSON, CSV)
├── miners/               # The core GitHub mining logic
├── results/              # Output directory for all generated files
│   ├── batches/          # Intermediate batch files
│   ├── final/            # Consolidated results
│   └── final_categorized_dataset/ # Final dataset after quality filtering
├── scripts/              # Manual scripts for specific tasks (e.g., analysis)
├── .env.example          # Environment variable template
├── config.py             # Loads configuration from .env
├── main.py               # Main entry point of the application
├── post_processing.py    # Handles consolidation and filtering
├── run.bat               # Execution script for Windows
└── run.sh                # Execution script for Linux/macOS
```