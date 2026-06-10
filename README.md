# Postman Collection to Pytest Migrator

## Live Deployment

Render Deployment URL:

https://postman-pytest-migrator-2.onrender.com


## Project Overview

Postman Collection to Pytest Migrator is an AI-assisted automation platform that converts Postman Collection v2.1 files into executable Pytest test scripts. The system automatically extracts API requests, headers, payloads, variables, and Postman assertions, then generates Python-based test automation scripts along with recommendations and test case suggestions.

The platform combines a Rule-Based Conversion Engine with an AI-Assisted Conversion Engine to handle both simple and complex Postman test logic.

---

## Problem Statement

Many QA teams store API testing logic inside Postman collections. While Postman is useful for API validation, migrating test cases to Pytest requires significant manual effort.

### Challenges

* Test logic remains locked inside Postman
* Manual migration to Pytest is time-consuming
* High risk of human error
* Difficult maintenance of multiple testing frameworks
* Lack of automated recommendation generation

---

## Solution

The application automates the migration workflow:

1. Upload Postman Collection
2. Parse API definitions and assertions
3. Validate collection structure
4. Convert assertions into Pytest format
5. Generate recommendations and test cases
6. Download executable Python scripts

---

## Key Features

### Authentication Module

* User Registration
* User Login
* Session-Based Authentication
* Secure Password Hashing

### Collection Processing

* Postman Collection Upload
* Collection Validation
* API Extraction
* Assertion Extraction

### AI-Assisted Migration

* Rule-Based Conversion Engine
* AI-Assisted Conversion Engine
* Hybrid Conversion Workflow

### Reporting

* Conversion Reports
* Positive Test Recommendations
* Negative Test Recommendations
* Boundary Test Recommendations
* Security Recommendations

### Dashboard

* Collection History
* Conversion Statistics
* Generated Scripts
* User Analytics

### UI Features

* Landing Page
* Onboarding Wizard
* Light Theme
* Dark Theme
* Responsive Design

---

## System Architecture

User
↓
Authentication
↓
Dashboard
↓
Upload Collection
↓
Parser
↓
Validator
↓
Hybrid Conversion Engine
↓
Recommendation Engine
↓
Pytest Generator
↓
Reports
↓
Download Center

---

## Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask

### Database

* SQLite

### AI Integration

* Google Gemini API

### Testing Framework

* Pytest

### Deployment

* Render

---

## Project Structure

project/

├── app.py

├── requirements.txt

├── database/

├── parser/

├── validators/

├── ai_engine/

├── templates/

├── static/

├── uploads/

├── generated_scripts/

├── generated_reports/

├── sample_data/

└── tests/

---

## Installation Guide

### Clone Repository

git clone <repository-url>

cd postman-pytest-migrator

### Create Virtual Environment

python -m venv venv

### Activate Environment

Windows:

venv\Scripts\activate

Linux/Mac:

source venv/bin/activate

### Install Dependencies

pip install -r requirements.txt

### Configure Environment Variables

Create a .env file:

GEMINI_API_KEY=your_api_key

SECRET_KEY=your_secret_key

DATABASE_PATH=database/migrator.db

### Run Application

python app.py

Application URL:

http://localhost:3000

---

## Sample Workflow

1. Register a new account
2. Login to the platform
3. Complete onboarding wizard
4. Upload Postman Collection JSON
5. Generate Pytest Script
6. Review recommendations and reports
7. Download generated files

---

## Sample Input

Location:

sample_data/input/basic_collection.json

---

## Expected Output

Location:

sample_data/expected_output/expected_pytest.py

---

## Test Cases

Available under:

tests/

Includes:

* Authentication Tests
* Parser Tests
* Converter Tests
* Download Tests

---

## Assumptions

* Postman Collection follows v2.1 schema
* Uploaded JSON is valid
* Internet access is available for AI-assisted conversions
* User has Gemini API access

---

## Limitations

* Highly customized JavaScript may require manual review
* SQLite is intended for small-to-medium workloads
* Generated scripts should be validated before production use

---

## Future Enhancements

* PostgreSQL Integration
* Batch Collection Processing
* CI/CD Integration
* Test Coverage Analytics
* AI Optimization Suggestions



## Demo Video Walkthrough

The demo video demonstrates:

1. User Registration
2. User Login
3. Onboarding Flow
4. Collection Upload
5. Collection Parsing
6. Pytest Generation
7. Recommendation Generation
8. Report Analysis
9. Script Download
10. Multi-User Data Isolation



J.J. College of Engineering and Technology
