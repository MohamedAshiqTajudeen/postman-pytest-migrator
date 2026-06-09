# Postman Collection to Pytest Migrator

## Overview

Postman Collection to Pytest Migrator is an AI-assisted automation platform that converts Postman Collection v2.1 files into executable Pytest test scripts.

The application automatically extracts API requests, headers, payloads, variables, and Postman assertions, then generates Python-based test automation scripts with recommendations and test case suggestions.

The system combines a rule-based conversion engine with AI-assisted conversion capabilities to handle both standard and complex Postman test logic.

---

## Problem Statement

Many QA teams maintain API tests inside Postman collections.

Challenges:

- Test logic remains locked inside Postman
- Manual conversion to Pytest is time-consuming
- Human errors occur during migration
- Maintaining both Postman and Pytest versions increases effort

---

## Solution

The platform automates migration by:

1. Uploading a Postman Collection
2. Parsing API requests and assertions
3. Validating collection structure
4. Converting assertions into Pytest format
5. Generating recommendations and test cases
6. Producing downloadable Python scripts

---

## Features

### User Management

- User Registration
- User Login
- Session Authentication
- Secure Password Hashing

### Collection Processing

- Postman Collection Upload
- Collection Validation
- API Extraction
- Assertion Extraction

### AI-Assisted Migration

- Rule-Based Conversion Engine
- AI-Assisted Conversion Engine
- Hybrid Conversion Workflow

### Reporting

- Conversion Reports
- Test Case Suggestions
- Positive Test Recommendations
- Negative Test Recommendations
- Boundary Test Recommendations
- Security Recommendations

### Dashboard

- Analytics Dashboard
- Collection History
- Generated Scripts
- User Statistics

### UI Features

- Landing Page
- Onboarding Wizard
- Dark Theme
- Light Theme
- Responsive Design

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

- HTML5
- CSS3
- JavaScript

### Backend

- Python 3
- Flask

### Database

- SQLite

### AI Layer

- Google Gemini API

### Testing

- Pytest

### Deployment

- Render

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

└── tests/

---

## Installation

### Clone Repository

git clone <repository-url>

cd postman-pytest-migrator

### Create Virtual Environment

python -m venv venv

### Activate Environment

Windows

venv\Scripts\activate

Linux/Mac

source venv/bin/activate

### Install Dependencies

pip install -r requirements.txt

---

## Environment Variables

Create .env file

GEMINI_API_KEY=your_api_key

SECRET_KEY=your_secret_key

DATABASE_PATH=database/migrator.db

---

## Run Application

python app.py

Application runs on:

http://localhost:3000

---

## Usage

1. Register Account
2. Login
3. Complete Onboarding
4. Upload Postman Collection
5. Generate Pytest Script
6. Review Reports
7. Download Generated Files

---

## Assumptions

- Postman Collection follows v2.1 schema
- Collection JSON is valid
- Internet access is available for AI-assisted conversions
- User has valid Gemini API access

---

## Limitations

- Complex custom JavaScript may require AI assistance
- SQLite is suitable for small to medium workloads
- Generated scripts may require manual review for highly customized workflows

---

## Future Enhancements

- PostgreSQL Support
- Multi-Collection Batch Processing
- CI/CD Integration
- Test Coverage Analytics
- AI-Powered Optimization Suggestions

---

## Deployment

Deployed using Render Cloud Platform.

---



Computer Science and Engineering

J.J. College of Engineering and Technology
