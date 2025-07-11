# FluxNews (Flux AI)

AI-powered real-time global news impact analysis platform for individual investors interested in mobility and robotics sectors.

## Project Overview

FluxNews analyzes global news in real-time to assess impact on Korean companies in the mobility and robotics sectors, providing actionable insights for individual investors.

## Tech Stack

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: Supabase (PostgreSQL)
- **AI/ML**: OpenAI API + HuggingFace (FinBERT)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- Supabase account

### Environment Setup

1. Clone the repository
2. Copy environment files:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.local.example frontend/.env.local
   ```
3. Fill in your Supabase and OpenAI credentials

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Project Structure

```
FluxNews/
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend application
├── docs/             # Documentation
└── tests/            # Integration tests
```

## License

Copyright 2025 FluxNews. All rights reserved.