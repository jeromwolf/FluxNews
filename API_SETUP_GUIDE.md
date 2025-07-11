# FluxNews API 설정 가이드

## 필수 API (MVP를 위해 반드시 필요)

### 1. OpenAI API
- **용도**: 뉴스 분석, 기업 추출, 관계 매핑
- **가입**: https://platform.openai.com
- **요금**: GPT-3.5-turbo 약 $0.002/1K tokens
- **예상 비용**: 월 $20-50 (하루 3,000개 뉴스 기준)

### 2. PostgreSQL (로컬 또는 클라우드)
- **로컬 설치**: 
  ```bash
  brew install postgresql@15
  brew services start postgresql@15
  createdb fluxnews_db
  ```
- **클라우드 옵션**: 
  - Supabase (무료 500MB)
  - Railway ($5/월)
  - Neon (무료 3GB)

## 권장 API (더 나은 서비스를 위해)

### 3. DART API (한국 공시 정보)
- **용도**: 한국 기업 공시 정보 수집
- **가입**: https://opendart.fss.or.kr
- **요금**: 무료 (일 10,000건)
- **신청 방법**: 
  1. 회원가입 후 로그인
  2. 오픈API → 인증키 신청
  3. 이메일로 API 키 수령

### 4. Brave Search API
- **용도**: 추가 뉴스 검색
- **가입**: https://brave.com/search/api
- **요금**: 무료 2,000 queries/월
- **유료**: $3/1,000 queries

### 5. GitHub Personal Access Token
- **용도**: 코드 버전 관리
- **생성 방법**:
  1. GitHub Settings → Developer settings
  2. Personal access tokens → Tokens (classic)
  3. Generate new token
  4. 권한 선택: repo, workflow

## 선택 API (특정 기능용)

### 6. Slack API (프리미엄 알림)
- **용도**: 실시간 알림 전송
- **설정**:
  1. https://api.slack.com/apps 에서 앱 생성
  2. OAuth & Permissions에서 Bot Token Scopes 추가
     - `chat:write`
     - `channels:read`
  3. Install to Workspace

### 7. Google Maps API
- **용도**: 기업 위치 정보
- **가입**: https://console.cloud.google.com
- **무료**: $200 크레딧/월
- **필요 API**: Places API, Geocoding API

### 8. HuggingFace (선택)
- **용도**: FinBERT 모델 가속화
- **가입**: https://huggingface.co/settings/tokens
- **요금**: 무료 (Rate limit 있음)

## 프로덕션 준비 (나중에)

### 9. 결제 시스템
- **토스페이먼츠** (한국)
  - https://developers.tosspayments.com
  - 테스트 키 무료 제공
- **Stripe** (글로벌)
  - https://stripe.com
  - 테스트 모드 무료

### 10. Neo4j (3-6개월 후)
- **Neo4j AuraDB Free**: 
  - 50,000 노드/175,000 관계 무료
  - https://neo4j.com/cloud/aura-free

## 빠른 시작 체크리스트

1. [ ] OpenAI API 키 발급 (필수)
2. [ ] PostgreSQL 설치 또는 클라우드 DB 설정 (필수)
3. [ ] DART API 키 신청 (권장 - 승인 1-2일 소요)
4. [ ] GitHub Personal Access Token 생성 (권장)
5. [ ] `.env.example`을 `.env`로 복사하고 API 키 입력

## 예산 관리 팁

### 월 10만원 예산 배분 (권장)
- OpenAI API: 3-5만원
- PostgreSQL (Railway/Supabase): 0-1만원
- Vercel Pro (필요시): 2만원
- 기타 API: 1-2만원
- 여유분: 2-3만원

### 무료로 시작하기
1. OpenAI API 무료 크레딧 활용
2. Supabase/Neon 무료 티어 사용
3. Vercel 무료 배포
4. 모든 API 무료 티어 활용

## 트러블슈팅

### PostgreSQL 연결 문제
```bash
# 로컬 PostgreSQL 상태 확인
brew services list

# 연결 테스트
psql -U postgres -d fluxnews_db
```

### API 키 관련
- 절대 `.env` 파일을 git에 커밋하지 마세요
- `.gitignore`에 `.env` 포함 확인
- 프로덕션에서는 환경변수로 관리