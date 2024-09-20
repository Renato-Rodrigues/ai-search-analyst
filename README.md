# AI-Powered Search and Analysis Tool

This project is an AI-powered tool that combines web search capabilities with AI analysis to provide insightful results on custom topics.

## Table of Contents

1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Setup](#setup)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Contributing](#contributing)
7. [License](#license)

## Features

- Multi-service AI integration: GPT, Azure (WIP), Gemini (WIP), AWS (WIP), Anthropic (WIP)
- Web search capabilities: Google Search, Bing Search (WIP)
- Google Sheets integration for input and output
- Caching system for improved performance
- Customizable query processing and result formatting

## Project Structure
```
project_folder/
│
├── ai_utils/
│   ├── ai_services.py      # Orchestrates AI service selection and query execution
│   ├── anthropic.py        # Handles interactions with Anthropic Claude API
│   ├── aws.py              # Manages AWS AI service integration
│   ├── azure.py            # Implements Azure OpenAI API functionality
│   ├── gemini.py           # Interfaces with Google Gemini API
│   └── gpt.py              # Handles OpenAI GPT API interactions
│
├── io_utils/
│   ├── google_auth.py      # Manages Google API authentication
│   └── google_sheets_io.py # Handles reading from and writing to Google Sheets
│
├── search_utils/
│   ├── bing_search.py      # Implements Bing Search API functionality
│   ├── google_search.py    # Handles Google Custom Search API operations
│   └── search_engine.py    # Orchestrates search engine selection and execution
│
├── .env                    # Stores environment variables (not tracked in git)
├── .gitignore              # Specifies intentionally untracked files to ignore
├── api_cache.json          # Caches API responses to reduce API calls (not tracked in git)
├── credentials.json        # Stores Google API credentials (not tracked in git)
├── FEATURES.md             # This file, describing features and project structure
├── README.md               # Provides an overview and instructions for the project
├── config.py               # Stores configuration options for the application
├── main.py                 # Main entry point of the application
├── requirements.txt        # Lists all Python package dependencies
└── token.pickle            # Stores Google API access tokens for authentication (not tracked in git)
```

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <project-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Copy `.env.example` to `.env`:
     ```
     cp .env.example .env
     ```
   - Open `.env` and fill in your API keys and other configuration values.

## Usage

Run the main script:
   ```
   python main.py
   ```
The script will process queries defined in your Google Sheet, perform web searches and AI analysis, and output the results back to the specified Google Sheet.

## Configuration

### Environment Variables

Set the following environment variables in your `.env` file:

- `GPT_API_KEY`: Your OpenAI GPT API key
- `AZURE_API_KEY`: Your Azure API key
- `AZURE_API_URL`: Your Azure API URL
- `GEMINI_API_KEY`: Your Gemini API key
- `GEMINI_API_URL`: Your Gemini API URL
- `AWS_API_KEY`: Your AWS API key
- `AWS_API_URL`: Your AWS API URL
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `ANTHROPIC_API_URL`: Your Anthropic API URL
- `GOOGLE_SEARCH_API_KEY`: Your Google Search API key
- `GOOGLE_SEARCH_CX`: Your Google Search CX
- `BING_SEARCH_API_KEY`: Your Bing Search API key
- `GOOGLE_SHEETS_ID`: Your Google Sheets ID

### Google Sheets

The project uses Google Sheets for input and output. Ensure you have the necessary permissions and have set up the Google Sheets API credentials.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

Copyright (c) 2024 Renato Rodrigues

