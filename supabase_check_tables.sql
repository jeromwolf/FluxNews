-- 현재 테이블 상태 확인 스크립트

-- 1. 현재 존재하는 테이블 목록
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- 2. companies 테이블 컬럼 확인
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'companies'
ORDER BY ordinal_position;

-- 3. 테이블에 데이터가 있는지 확인
SELECT 
    'companies' as table_name, 
    COUNT(*) as row_count 
FROM companies
UNION ALL
SELECT 
    'news_articles' as table_name, 
    COUNT(*) as row_count 
FROM news_articles
UNION ALL
SELECT 
    'users' as table_name, 
    COUNT(*) as row_count 
FROM users;

-- 4. country 컬럼 추가만 필요한 경우 (테이블은 있지만 컬럼이 없는 경우)
-- ALTER TABLE companies ADD COLUMN IF NOT EXISTS country VARCHAR(2) DEFAULT 'KR';

-- 5. 테이블 구조 확인 (상세)
\d companies