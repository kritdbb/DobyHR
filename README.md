# HR System

Internal company HR management system.

## Tech Stack

- **Backend**: Python (FastAPI) + SQLAlchemy
- **Frontend**: Vue 3 + Vite + TailwindCSS
- **Database**: PostgreSQL
- **Infrastructure**: Docker Compose

## Quick Start

```bash
# 1. Copy env file and customize
cp .env.example .env

# 2. Run with Docker
docker compose up --build

# 3. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Development (without Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt
# Set DATABASE_URL in .env to your local postgres
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Available at http://localhost:5173
# API proxy configured to http://localhost:8000
```

## Features

- **Company Settings**: Company name, Tax ID, logo, location (lat/lon)
- **User Management**: Full CRUD for employees with photo, department, work schedule, leave allocation
- **Approval Lines**: Multi-level approval flow builder with AND/OR conditions per level
