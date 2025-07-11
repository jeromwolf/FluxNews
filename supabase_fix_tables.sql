-- FluxNews 테이블 수정 및 재생성 스크립트
-- 기존 테이블이 있다면 안전하게 처리

-- 1. 기존 테이블 확인 및 백업 (필요시)
-- SELECT * FROM companies; -- 데이터가 있다면 먼저 백업

-- 2. 기존 테이블 삭제 (CASCADE로 관련 테이블도 함께 삭제)
DROP TABLE IF EXISTS user_watchlists CASCADE;
DROP TABLE IF EXISTS news_company_impacts CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS news_articles CASCADE;
DROP TABLE IF EXISTS company_relationships CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

-- 3. 함수 삭제 (있다면)
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- 4. 테이블 다시 생성
-- 기업 정보 테이블
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    name_ko VARCHAR(100),
    country VARCHAR(2) DEFAULT 'KR',
    sector VARCHAR(50),
    market_cap BIGINT,
    description TEXT,
    neo4j_node_id BIGINT,
    sync_status VARCHAR(20) DEFAULT 'pending',
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 기업 관계 테이블
CREATE TABLE company_relationships (
    id SERIAL PRIMARY KEY,
    from_company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    to_company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    relationship_type VARCHAR(30) NOT NULL,
    strength DECIMAL(3,2) CHECK (strength >= 0 AND strength <= 1),
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    neo4j_rel_id BIGINT,
    sync_status VARCHAR(20) DEFAULT 'pending',
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(from_company_id, to_company_id, relationship_type)
);

-- 뉴스 기사 테이블
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    content TEXT,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100),
    author VARCHAR(200),
    language VARCHAR(5) DEFAULT 'ko',
    sentiment_score DECIMAL(3,2),
    published_at TIMESTAMP WITH TIME ZONE,
    analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 뉴스-기업 영향 분석 테이블
CREATE TABLE news_company_impacts (
    id SERIAL PRIMARY KEY,
    news_id INTEGER REFERENCES news_articles(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    impact_score DECIMAL(3,2) CHECK (impact_score >= -1 AND impact_score <= 1),
    impact_magnitude DECIMAL(3,2) CHECK (impact_magnitude >= 0 AND impact_magnitude <= 1),
    confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT,
    ai_model VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(news_id, company_id)
);

-- 사용자 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    daily_analysis_count INTEGER DEFAULT 0,
    last_analysis_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 사용자 관심 기업 테이블
CREATE TABLE user_watchlists (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    alert_threshold DECIMAL(3,2) DEFAULT 0.7,
    alert_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, company_id)
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX idx_companies_symbol ON companies(symbol);
CREATE INDEX idx_companies_country ON companies(country);
CREATE INDEX idx_news_published_at ON news_articles(published_at DESC);
CREATE INDEX idx_news_analyzed_at ON news_articles(analyzed_at DESC);
CREATE INDEX idx_impacts_company_id ON news_company_impacts(company_id);
CREATE INDEX idx_impacts_news_id ON news_company_impacts(news_id);
CREATE INDEX idx_watchlists_user_id ON user_watchlists(user_id);

-- 업데이트 타임스탬프 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5. 샘플 데이터 삽입
INSERT INTO companies (symbol, name, name_ko, sector, country) VALUES
('005930', 'Samsung Electronics', '삼성전자', 'Technology', 'KR'),
('000660', 'SK Hynix', 'SK하이닉스', 'Semiconductors', 'KR'),
('051910', 'LG Chem', 'LG화학', 'Battery', 'KR'),
('006400', 'Samsung SDI', '삼성SDI', 'Battery', 'KR'),
('TSLA', 'Tesla', '테슬라', 'Electric Vehicles', 'US'),
('AAPL', 'Apple', '애플', 'Technology', 'US');

-- 테이블 생성 확인
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;