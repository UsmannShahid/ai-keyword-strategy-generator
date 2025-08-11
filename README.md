# AI Keyword Tool

A Streamlit web application that generates SEO keyword suggestions using OpenAI's GPT model.

## Features

- Generate comprehensive SEO keyword lists
- Primary, long-tail, local, and semantic keyword suggestions
- Clean, user-friendly web interface
- Powered by OpenAI's GPT model

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
cd ai-keyword-tool
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
1. Copy `.env.example` to `.env` (if available) or create a `.env` file
2. Add your OpenAI API key:
```
OPENAI_API_KEY=your_actual_api_key_here
```

### 6. Run the Application
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### 7. Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Or use the test runner script
python run_tests.py

# Run with coverage
python run_tests.py --coverage
```

## Project Structure
```
ai-keyword-tool/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in git)
├── .gitignore         # Git ignore file
├── pytest.ini         # Pytest configuration
├── run_tests.py        # Test runner script
├── tests/              # Test suite
│   ├── __init__.py     # Package initialization
│   ├── test_app.py     # Main test file
│   └── README.md       # Testing documentation
├── venv/              # Virtual environment (not in git)
└── README.md          # This file
```

## Usage

1. Enter a description of your website or business in the text input
2. Click "Generate Keywords" to get AI-powered keyword suggestions
3. Use the generated keywords for your SEO strategy

## Requirements

- Python 3.7+
- OpenAI API key
- Internet connection

## Dependencies

- streamlit: Web app framework
- openai: OpenAI API client
- python-dotenv: Environment variable management
- pandas: Data manipulation and analysis
- pytest: Testing framework
- pytest-mock: Mocking utilities for tests

## Testing

The project includes a comprehensive test suite covering:
- Utility functions
- Data processing
- API integration (mocked)
- Error handling
- File operations

See `tests/README.md` for detailed testing documentation.

## Security Notes

- Never commit your `.env` file to version control
- Keep your OpenAI API key secure
- Regenerate API keys if accidentally exposed

## Troubleshooting

### "streamlit: command not found"
Make sure your virtual environment is activated and streamlit is installed.

### "Import 'streamlit' could not be resolved"
This is a common IDE warning. As long as streamlit is installed in your virtual environment, the app will run fine.

### API Key Issues
- Ensure your OpenAI API key is correctly set in the `.env` file
- Check that you have sufficient credits in your OpenAI account
- Verify the API key format is correct (starts with 'sk-')
