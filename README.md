# 🚀 AI Keyword Strategy Generator

An intelligent keyword research and content strategy tool powered by AI that helps you discover quick-win opportunities and generate comprehensive content briefs.

## ✨ Features

### 🎯 Smart Keyword Discovery
- **Personalized Input System**: Describe your business, industry, and target audience
- **Quick-Win Scoring**: AI-powered scoring to identify rankable opportunities
- **SERP Analysis**: Real-time search engine results analysis
- **Competitor Intelligence**: Automated competitor content gap analysis

### 🧠 AI-Powered Content Strategy
- **Dynamic Content Briefs**: AI-generated content briefs tailored to your keyword
- **Strategic Suggestions**: Personalized quick wins, content ideas, and technical SEO recommendations
- **SERP-Based Insights**: Content opportunities based on competitor analysis

### 💾 Advanced Session Management
- **Persistent Storage**: SQLite database for session and content persistence
- **Session Tracking**: Every analysis is saved and can be revisited
- **Data Relationships**: Links between sessions, briefs, suggestions, and SERP data
- **Export Ready**: Structured data ready for report generation

## 🏗️ Architecture

### Database Schema
```sql
-- Core session management
sessions (id, created_at, topic)
briefs (id, session_id, content, created_at)

-- Enhanced AI features  
suggestions (id, session_id, variant, content, created_at)
serps (id, session_id, data, created_at)
```

### Tech Stack
- **Frontend**: Streamlit for interactive web interface
- **Backend**: Python with OpenAI API integration
- **Database**: SQLite for local data persistence
- **AI Integration**: OpenAI GPT models for content generation
- **SERP Data**: Real-time search engine results fetching

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-keyword-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r ai-keyword-tool/requirements.txt
   ```

3. **Set up environment**
   ```bash
   # Create .env file and add your OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

4. **Initialize database**
   ```bash
   python db_init.py
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 📊 Usage Workflow

### Step 1: Business Input
- Describe your business/product
- Specify industry and target audience
- Select country and language preferences

### Step 2: Keyword Discovery
- AI generates relevant keywords with quick-win scores
- Filter by score, include/exclude terms
- Select target keyword for content strategy

### Step 3: AI Content Brief
- Generates comprehensive content brief
- Includes structure, key points, and optimization tips
- Automatically saved to session

### Step 4: SERP Analysis
- Real-time competitor analysis
- Identifies content gaps and opportunities
- Saved for future reference

### Step 5: Strategy Suggestions
- AI-generated content ideas
- Technical SEO recommendations
- Actionable next steps
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
