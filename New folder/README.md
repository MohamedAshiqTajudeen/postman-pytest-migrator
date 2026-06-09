# Postman Collection → Pytest Migrator (Phase 1)

Transform Postman API collections into executable pytest automation suites using Gemini AI.

## Project Architecture & Tech Stack

- **Backend:** Python 3.11, Flask
- **Database:** SQLite
- **AI Engine:** Google Gemini API (Free Tier)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (No React, Node, or TypeScript)

## Phase 1 Deliverables (Created)

1. **`requirements.txt`**: Manages all required Python dependencies (`Flask`, `google-genai`, `pytest`, `requests`, `python-dotenv`).
2. **`.env.example`**: Outlines environmental configurations (`GEMINI_API_KEY`, `FLASK_APP`, `FLASK_ENV`, `SECRET_KEY`, `DATABASE_PATH`).
3. **`database/db_manager.py`**: Custom SQLite Manager containing five core transactional tables according to the precise database schema:
   - `uploaded_collections`
   - `api_details`
   - `generated_testcases`
   - `generated_scripts`
   - `ai_recommendations`

## Project Folder Shell (Ready for Phase 2)

- `/database` - Database controllers and managers
- `/parser` - Postman Collection JSON validators and parser scripts
- `/ai_engine` - Gemini conversion integration
- `/validators` - Python and Pytest script syntax validators
- `/uploads` - Location for temporary file upload caching
- `/generated_scripts` - Converted `.py` pytest automation suites
- `/generated_reports` - Conversion metrics and feedback logs
- `/sample_data` - Mock Postman collections for sandbox validations
- `/tests` - Local system unit and integration tests
- `/templates` - Jinja2 HTML server-side interfaces
- `/static` - CSS stylings and vanilla JS client side bundles
