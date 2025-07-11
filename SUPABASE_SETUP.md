# Supabase PostgreSQL 설정 가이드

## 1. Supabase 계정 생성 및 프로젝트 설정

### 1.1 계정 생성
1. https://supabase.com 접속
2. "Start your project" 클릭
3. GitHub 또는 이메일로 가입

### 1.2 새 프로젝트 생성
1. Dashboard에서 "New project" 클릭
2. 프로젝트 정보 입력:
   - **Name**: `fluxnews`
   - **Database Password**: 강력한 비밀번호 설정 (저장 필수!)
   - **Region**: `Northeast Asia (Seoul)` 선택 (한국 서비스)
   - **Plan**: Free (500MB 스토리지, 2GB 전송량)

3. "Create new project" 클릭 (1-2분 소요)

### 1.3 데이터베이스 연결 정보 확인
1. 프로젝트 생성 완료 후 Settings → Database 이동
2. Connection string 섹션에서 URI 복사:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
   

## 2. FluxNews 테이블 생성

### 2.1 SQL Editor 접속
1. 좌측 메뉴에서 "SQL Editor" 클릭
2. "New query" 클릭

### 2.2 초기 스키마 생성
아래 SQL을 복사하여 실행:

```sql
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
```

### 2.3 초기 데이터 삽입 (선택사항)
```sql
-- 샘플 기업 데이터
INSERT INTO companies (symbol, name, name_ko, sector, country) VALUES
('005930', 'Samsung Electronics', '삼성전자', 'Technology', 'KR'),
('000660', 'SK Hynix', 'SK하이닉스', 'Semiconductors', 'KR'),
('051910', 'LG Chem', 'LG화학', 'Battery', 'KR'),
('006400', 'Samsung SDI', '삼성SDI', 'Battery', 'KR'),
('TSLA', 'Tesla', '테슬라', 'Electric Vehicles', 'US'),
('AAPL', 'Apple', '애플', 'Technology', 'US');

-- 샘플 관계 데이터
INSERT INTO company_relationships (from_company_id, to_company_id, relationship_type, strength, confidence) VALUES
(5, 4, 'CUSTOMER', 0.8, 0.9),  -- Tesla → Samsung SDI (배터리 공급)
(5, 3, 'CUSTOMER', 0.6, 0.8),  -- Tesla → LG Chem (배터리 공급)
(6, 1, 'PARTNER', 0.7, 0.9);   -- Apple → Samsung Electronics (디스플레이)
```

## 3. Supabase 기능 활성화

### 3.1 Row Level Security (RLS) 설정
```sql
-- RLS 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_watchlists ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 데이터만 볼 수 있음
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own watchlist" ON user_watchlists
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own watchlist" ON user_watchlists
    FOR ALL USING (auth.uid() = user_id);
```

### 3.2 Realtime 구독 활성화
1. Database → Replication 메뉴로 이동
2. 다음 테이블에 대해 Realtime 활성화:
   - `news_articles`
   - `news_company_impacts`
   - `user_watchlists`

## 4. API 키 및 URL 확인

Settings → API에서 확인:
- **Project URL**: `https://[PROJECT-REF].supabase.co`
- **Anon/Public Key**: 프론트엔드용
- **Service Role Key**: 백엔드용 (비밀 유지!)

## 5. 환경변수 설정

`.env` 파일에 추가:
```bash
# Supabase
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# PostgreSQL 직접 연결 (선택)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

## 6. 무료 티어 제한사항

- **스토리지**: 500MB
- **대역폭**: 2GB/월
- **Edge Functions**: 500K 호출/월
- **동시 연결**: 최대 50개
- **백업**: 7일 point-in-time recovery

## 7. 모니터링

1. Dashboard에서 실시간 모니터링 가능
2. Database → Query Performance로 느린 쿼리 확인
3. Storage 사용량 주기적 확인

## 팁

- 개발 중에는 Table Editor 사용하여 GUI로 데이터 관리
- SQL Editor에서 쿼리 저장 기능 활용
- Database Functions로 복잡한 로직 서버사이드 처리
- Storage 기능으로 뉴스 이미지 저장 가능