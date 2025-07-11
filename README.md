# FluxNews (Flux AI)

AI-powered real-time global news impact analysis platform for individual investors interested in mobility and robotics sectors.

## 🚀 Project Overview

FluxNews analyzes global news in real-time to assess impact on Korean companies in the mobility and robotics sectors, providing actionable insights for individual investors.

### Key Features
- 📰 **Real-time News Analysis**: AI-powered analysis of global news impact on Korean companies
- 🏢 **Company Network Visualization**: Interactive network graph showing relationships between companies
- 📊 **Impact Scoring**: Quantitative impact scores (0.0-1.0) for news articles
- 🔔 **Smart Alerts**: Customizable alerts for significant market events
- 🌏 **Bilingual Support**: Full Korean and English language support
- 📱 **Responsive Design**: Optimized for desktop and mobile devices

## 🛠 Tech Stack

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + Shadcn/ui
- **Backend**: FastAPI + Python 3.9+
- **Database**: Supabase (PostgreSQL) with Neo4j migration planned
- **AI/ML**: OpenAI GPT-4 API + HuggingFace (FinBERT)
- **Authentication**: Supabase Auth
- **Deployment**: Frontend on Vercel, Backend on Railway

## 📋 Prerequisites

- Node.js 18+ 
- Python 3.9+
- Supabase account
- OpenAI API key
- Git

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/fluxnews/fluxnews.git
cd fluxnews
```

### 2. Environment Setup
```bash
# Backend environment
cp backend/.env.example backend/.env
# Frontend environment  
cp frontend/.env.local.example frontend/.env.local
```

### 3. Configure Environment Variables

**Backend (.env)**:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

✅ Backend API available at: http://localhost:8000  
📚 API Documentation: http://localhost:8000/docs

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

✅ Frontend available at: http://localhost:3000

## 📚 API Documentation

### Available Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/logout` - User logout

#### News
- `GET /api/v1/news` - Get news feed
- `GET /api/v1/news/{id}` - Get specific article
- `POST /api/v1/news/analyze` - AI analysis of article
- `GET /api/v1/news/company/{company_id}` - Get company news

#### Companies
- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/{id}` - Get company details
- `GET /api/v1/companies/network` - Get network visualization data
- `GET /api/v1/companies/search` - Search companies

#### Watchlist
- `GET /api/v1/watchlist` - Get user watchlist
- `POST /api/v1/watchlist` - Add to watchlist
- `PUT /api/v1/watchlist/{id}` - Update watchlist item
- `DELETE /api/v1/watchlist/{id}` - Remove from watchlist

Full interactive documentation available at http://localhost:8000/docs

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:watch  # Watch mode
```

## 📁 Project Structure

```
FluxNews/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # Utilities and configurations
│   │   └── types/           # TypeScript type definitions
│   └── public/              # Static assets
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configurations
│   │   └── models/         # Data models
│   └── requirements.txt    # Python dependencies
├── .taskmaster/            # Task management system
├── docs/                   # Documentation
└── tests/                  # Integration tests
```

## 🌟 Current Progress

### Completed Features ✅
- [x] Landing page with modern UI/UX
- [x] User authentication (login/signup/logout)
- [x] Real-time news dashboard
- [x] Company network visualization
- [x] Watchlist management
- [x] Korean/English localization
- [x] Backend API implementation
- [x] Frontend-backend integration

### Upcoming Features 🚧
- [ ] Real-time news data ingestion
- [ ] Advanced AI analysis with FinBERT
- [ ] Push notifications for alerts
- [ ] Mobile app development
- [ ] Neo4j graph database migration
- [ ] Premium subscription management

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Copyright 2025 FluxNews. All rights reserved.

## 📞 Contact

- Email: support@fluxnews.ai
- Website: https://fluxnews.ai
- GitHub: https://github.com/fluxnews/fluxnews

---

<p align="center">
  Made with ❤️ by the FluxNews Team
</p>