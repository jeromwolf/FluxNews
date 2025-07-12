# Backend Architecture Overview

## 🏗️ Architecture Design

FluxNews backend follows a modular, service-oriented architecture designed for scalability and maintainability.

### Core Principles
- **Separation of Concerns**: Clear boundaries between API, business logic, and data access
- **Dependency Injection**: Loose coupling between components
- **Async-First**: Leveraging Python's async/await for high performance
- **Type Safety**: Comprehensive type hints and Pydantic models

## 📁 Service Layer Architecture

### News Collection Service (`/services/news/`)
- **RSS Parser**: Collects news from multiple RSS feeds
- **Google News Collector**: Scrapes trending news
- **Deduplication System**: Prevents duplicate articles
- **News Pipeline**: Orchestrates the collection process

### AI/ML Services (`/services/ai/`, `/services/sentiment/`)
- **OpenAI Integration**: Company extraction and analysis
- **FinBERT Sentiment**: Financial sentiment analysis
- **Cost Tracking**: Monitors API usage and costs

### Impact Calculation (`/services/impact/`)
- **Multi-layer Analysis**: Direct, indirect, sector, and market impacts
- **Time Decay**: Recent news weighted more heavily
- **Relationship Propagation**: Impact spreads through company network

### Real-time Notifications (`/services/notification/`)
- **WebSocket Manager**: Handles persistent connections
- **Priority Queue**: Ensures important alerts delivered first
- **Retry Mechanism**: Handles failed deliveries

### Subscription Management (`/services/subscription/`)
- **Tier System**: Free, Premium, Enterprise levels
- **Usage Tracking**: Monitors API calls and feature usage
- **Payment Ready**: Prepared for Stripe/Toss integration

## 🚀 Performance Optimizations

### Redis Caching Strategy
```python
# Cache Layers:
1. API Response Cache (15 min TTL)
2. News Article Cache (1 hour TTL)
3. AI Analysis Cache (24 hour TTL)
4. Company Data Cache (6 hour TTL)
```

### Database Optimizations
- **Connection Pooling**: asyncpg with 5-20 connections
- **Prepared Statements**: Reduce query parsing overhead
- **Indexes**: Optimized for common query patterns
- **Full-text Search**: GIN indexes for news search

### Async Processing
- **Concurrent Fetching**: Parallel RSS feed processing
- **Batch Operations**: Bulk inserts using COPY
- **Background Tasks**: Non-blocking AI analysis

## 🔒 Security Measures

### API Security
- **Authentication**: Supabase Auth integration
- **Rate Limiting**: Per-tier API limits
- **Input Validation**: Pydantic models ensure data integrity
- **SQL Injection Prevention**: Parameterized queries

### Data Protection
- **Encryption**: Sensitive data encrypted at rest
- **API Key Management**: Secure storage in environment
- **Audit Logging**: Track all data access

## 📊 Monitoring & Observability

### Health Checks
- Database connectivity
- Redis availability
- External API status
- WebSocket connections

### Performance Metrics
- API response times
- Cache hit rates
- Database query performance
- AI processing times

### Error Tracking
- Structured logging with context
- Error aggregation by service
- Alert thresholds for critical issues

## 🔄 Data Flow

```
1. News Collection
   RSS/Google → Deduplication → Database
   
2. AI Analysis
   Article → OpenAI/FinBERT → Impact Score → Cache
   
3. User Request
   API → Cache Check → Database → Response
   
4. Real-time Updates
   Impact Event → WebSocket → Client
```

## 🛠️ Development Guidelines

### Adding New Services
1. Create service directory under `/services/`
2. Implement business logic with clear interfaces
3. Add caching decorators where appropriate
4. Write comprehensive tests
5. Document API changes

### Performance Checklist
- [ ] Use async/await for I/O operations
- [ ] Implement caching for expensive operations
- [ ] Add database indexes for new queries
- [ ] Profile and optimize hot paths
- [ ] Monitor memory usage

### Code Quality Standards
- Type hints for all functions
- Docstrings for public APIs
- Unit tests with >80% coverage
- Integration tests for critical paths
- Regular security audits