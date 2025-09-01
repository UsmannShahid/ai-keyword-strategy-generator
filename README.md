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
- **API**: FastAPI for RESTful API endpoints
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

## 🔌 FastAPI Integration

The project now includes a FastAPI backend that provides RESTful API endpoints for programmatic access to the keyword and content generation features.

### API Endpoints

#### Core Endpoints
- `GET /` - API status and available endpoints
- `GET /ping` - Health check endpoint
- `GET /health` - Application health status
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

#### Content Generation Endpoints
- `POST /generate-brief/` - Generate content brief for a keyword
- `POST /suggest-keywords/` - Get keyword suggestions for a topic
- `POST /serp/` - Fetch SERP data for keyword analysis
- `POST /suggestions/` - Get AI-powered content suggestions

### Running the API Server

**Start the FastAPI server:**
```bash
python -m api.main
```

The API will be available at `http://127.0.0.1:8001`

**Access interactive documentation:**
- Swagger UI: `http://127.0.0.1:8001/docs`
- ReDoc: `http://127.0.0.1:8001/redoc`

### API Usage Examples

**Generate content brief:**
```bash
curl -X POST "http://127.0.0.1:8001/generate-brief/" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "digital marketing strategies", "user_plan": "free"}'
```

**Get keyword suggestions:**
```bash
curl -X POST "http://127.0.0.1:8001/suggest-keywords/" \
  -H "Content-Type: application/json" \
  -d '{"topic": "content marketing", "max_results": 10, "user_plan": "free"}'
```

### API Configuration

The API supports different user plans with varying capabilities:

**Free Plan:**
- GPT-3.5 Turbo model
- Serper.dev for SERP data
- Max 10 keyword results
- Basic features

**Paid Plan:**
- GPT-4 model
- SearchAPI.io for enhanced SERP data
- Max 25 keyword results  
- Advanced keyword analysis

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
├── api/               # FastAPI backend
│   ├── __init__.py     # API package initialization
│   ├── main.py         # FastAPI application entry point
│   ├── core/           # Core API functionality
│   │   ├── __init__.py
│   │   ├── config.py   # Configuration and user plans
│   │   ├── env.py      # Environment variable handling
│   │   ├── gpt.py      # OpenAI integration
│   │   ├── keywords.py # Keyword processing
│   │   └── serp.py     # SERP data fetching
│   ├── models/         # Pydantic data models
│   │   ├── __init__.py
│   │   └── schemas.py  # Request/response schemas
│   └── routes/         # API route handlers
│       ├── __init__.py
│       ├── brief.py    # Content brief generation
│       ├── keywords.py # Keyword suggestions
│       ├── serp.py     # SERP data endpoints
│       └── suggestions.py # Content suggestions
├── src/               # Core application modules
│   ├── core/          # Core business logic
│   ├── ui/            # Streamlit UI components
│   ├── utils/         # Utility functions
│   └── services/      # Application services
├── tests/              # Test suite
│   ├── __init__.py     # Package initialization
│   ├── test_app.py     # Main test file
│   └── README.md       # Testing documentation
├── data/              # Data files and GKP keywords
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

### Core Dependencies
- streamlit: Web app framework
- openai: OpenAI API client
- python-dotenv: Environment variable management
- pandas: Data manipulation and analysis
- requests: HTTP client for SERP data fetching

### API Dependencies
- fastapi: Modern, fast web framework for APIs
- uvicorn: ASGI server for FastAPI
- pydantic: Data validation and serialization

### Development Dependencies
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
