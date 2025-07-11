# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FluxNews (Flux AI) is an AI-powered real-time global news impact analysis platform for individual investors interested in mobility and robotics sectors. Currently in initial planning phase for the 2025 Financial AI Challenge.

## Technology Stack

- **Frontend**: Next.js + Tailwind CSS (to be deployed on Vercel)
- **Backend**: FastAPI + Python (to be deployed on Railway)
- **Database**: PostgreSQL initially, with planned Neo4j hybrid migration at 3-6 months
- **AI/ML**: OpenAI API + HuggingFace models (FinBERT for sentiment analysis)
- **Infrastructure Budget**: Under 100,000 KRW/month

## Project Status

The project is in planning phase with a detailed PRD (flux.prd) but no code implementation yet. When implementing:

1. **Frontend Setup** (when created):
   ```bash
   npm install
   npm run dev      # Development server
   npm run build    # Production build
   npm run lint     # Linting
   ```

2. **Backend Setup** (when created):
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload  # Development server
   pytest                      # Run tests
   ```

## Architecture

### AI Analysis Pipeline
1. News collection from RSS feeds and Google News (target: 3,000 articles/day)
2. Sentiment analysis using FinBERT model
3. Company extraction and relationship mapping using OpenAI
4. Impact score calculation (0.0 to 1.0 scale)
5. Real-time alerts and dashboard updates

### Database Schema
PostgreSQL tables with Neo4j preparation:
- `companies` (includes neo4j_node_id for future hybrid)
- `company_relationships`
- `news_articles`
- `news_company_impacts`
- `users` and `user_watchlists`

### Key Implementation Notes

1. **Company Network**: 80 initial companies (50 autonomous driving, 30 robotics)
2. **User Tiers**: 
   - Free: 3 AI analysis/day, 3 watchlist companies
   - Premium ($9.99/month): Unlimited analysis, 50 companies, real-time alerts
3. **MVP Focus**: 20 companies, 50 relationships for competition demo

## Development Timeline

- Week 1: Complete PRD and technical planning
- Week 2-3: Build MVP prototype
- Week 4: Demo preparation and competition submission

## Important Context from PRD

The product targets Korean individual investors aged 20-40 who want to understand how global news impacts Korean companies in mobility/robotics sectors. The platform must handle real-time news processing with Korean language support and provide actionable investment insights through an intuitive dashboard.

## Development Methodology

### Test-Driven Development (TDD)
Always follow the TDD cycle:
1. **Red**: Write a failing test for a small increment of functionality
2. **Green**: Implement minimum code to make the test pass
3. **Refactor**: Improve code structure while keeping tests passing

### Key Principles
- Write one test at a time, make it run, then improve structure
- Run all tests (except long-running ones) after each change
- Use meaningful test names that describe behavior (e.g., "should_extract_companies_from_korean_news")
- Never mix structural and behavioral changes in the same commit

### Tidy First Approach
Separate all changes into two types:
- **Structural Changes**: Code reorganization without behavior change (renaming, extracting methods)
- **Behavioral Changes**: Adding or modifying functionality
- Always make structural changes first when both are needed

### Testing Commands
```bash
# Frontend tests (when implemented)
npm test           # Run all tests
npm test:watch     # Run tests in watch mode

# Backend tests (when implemented)
pytest             # Run all tests
pytest -v          # Verbose output
pytest tests/unit  # Run unit tests only
```

### Commit Guidelines
- Only commit when ALL tests pass and warnings are resolved
- Use clear commit messages indicating change type:
  - `refactor: extract news analysis service`
  - `feat: add sentiment score calculation`
  - `test: add company extraction tests`