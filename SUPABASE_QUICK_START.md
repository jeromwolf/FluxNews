# Supabase 빠른 시작 가이드

## 1. Supabase 프로젝트 생성 (5분)

1. **https://supabase.com** 접속
2. **"Start your project"** 클릭
3. GitHub 또는 이메일로 가입
4. **새 프로젝트 생성**:
   - Name: `fluxnews`
   - Password: 강력한 비밀번호 (저장 필수!)
   - Region: `Northeast Asia (Seoul)`
   - Plan: Free

## 2. 연결 정보 가져오기

프로젝트 생성 완료 후:

### 2.1 Database URL
Settings → Database → Connection string:
```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### 2.2 API Keys
Settings → API:
- **Project URL**: `https://[PROJECT-REF].supabase.co`
- **anon key**: (공개 가능)
- **service_role key**: (비밀 유지!)

## 3. Claude Desktop 설정

`claude_desktop_config.json`에 추가:
```json
{
  "mcpServers": {
    "postgres-supabase": {
      "command": "npx",
      "args": [
        "-y", 
        "@modelcontextprotocol/server-postgres", 
        "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"
      ]
    }
  }
}
```

## 4. 환경변수 설정

`.env` 파일:
```bash
# Supabase
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

## 5. 테이블 생성

Supabase Dashboard → SQL Editor에서 실행:
```sql
-- 빠른 시작용 기본 테이블
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    name_ko VARCHAR(100),
    sector VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    sentiment_score DECIMAL(3,2),
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 샘플 데이터
INSERT INTO companies (symbol, name, name_ko, sector) VALUES
('005930', 'Samsung Electronics', '삼성전자', 'Technology'),
('TSLA', 'Tesla', '테슬라', 'Electric Vehicles');
```

## 6. 연결 테스트

Claude Desktop에서:
1. PostgreSQL 서버가 연결되었는지 확인
2. 테스트 쿼리 실행:
   ```sql
   SELECT * FROM companies;
   ```

## 완료! 🎉

이제 Supabase PostgreSQL을 FluxNews 프로젝트에서 사용할 수 있습니다.

### 다음 단계:
- SUPABASE_SETUP.md에서 전체 스키마 생성
- Realtime 기능 활성화
- Row Level Security 설정