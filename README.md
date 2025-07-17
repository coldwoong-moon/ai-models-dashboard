# 🤖 AI Models Dashboard

AI Models Dashboard는 주요 AI 모델들의 가격과 스펙을 실시간으로 비교할 수 있는 웹 기반 대시보드입니다. GitHub Pages에서 완전히 무료로 호스팅되며, GitHub Actions를 통해 자동으로 데이터를 업데이트합니다.

## ✨ 주요 기능

- **실시간 가격 비교**: OpenAI, Anthropic, Google, OpenRouter 등 주요 AI 제공업체의 모델 가격 비교
- **자동 업데이트**: 6시간마다 자동으로 최신 데이터 수집
- **가격 계산기**: 예상 사용량에 따른 월간 비용 계산
- **히스토리 추적**: 가격 변동 이력 및 트렌드 차트
- **반응형 디자인**: 모바일, 태블릿, 데스크톱에서 최적화된 UI
- **다크 모드 지원**: 사용자 선호에 따른 테마 전환

## 🚀 빠른 시작

### 1. 저장소 Fork

이 저장소를 Fork하여 자신의 GitHub 계정에 복사합니다.

### 2. GitHub Pages 활성화

1. Fork한 저장소의 Settings로 이동
2. Pages 섹션에서 Source를 `GitHub Actions`로 설정
3. Save 클릭

### 3. 로컬 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/ai-models-dashboard.git
cd ai-models-dashboard

# 의존성 설치
npm install
pip install -r requirements.txt

# 개발 서버 실행
npm run dev
```

브라우저에서 `http://localhost:8000` 접속

## 📁 프로젝트 구조

```
ai-models-dashboard/
├── .github/
│   └── workflows/
│       ├── update-data.yml      # 데이터 수집 자동화
│       └── deploy.yml           # GitHub Pages 배포
├── data/
│   ├── models/                  # 제공업체별 모델 데이터
│   ├── history/                 # 일별 히스토리 스냅샷
│   └── consolidated.json        # 통합 데이터
├── scripts/
│   ├── crawlers/                # 제공업체별 크롤러
│   ├── data_processor.py        # 데이터 통합 처리
│   └── price_monitor.py         # 가격 변경 모니터링
├── src/
│   ├── js/                      # JavaScript 모듈
│   └── css/                     # 스타일시트
├── index.html                   # 메인 페이지
├── package.json                 # Node.js 설정
└── requirements.txt             # Python 의존성
```

## 🛠️ 기술 스택

- **Frontend**: Vanilla JavaScript, Tailwind CSS, Chart.js
- **Backend**: Python (크롤러), GitHub Actions
- **Hosting**: GitHub Pages
- **Data Storage**: JSON 파일 (Git 기반 버전 관리)

## 📊 데이터 수집

### 지원 제공업체

- **OpenAI** (GPT-4o, o1-preview, GPT-4, GPT-3.5 등)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 시리즈)
- **Google AI** (Gemini 2.0 Flash, Gemini 1.5 Pro/Flash 시리즈)
- **DeepSeek** (DeepSeek V3, DeepSeek Coder V2, 수학/코딩 특화)
- **xAI** (Grok 2, Grok 2 Vision, 실시간 X 데이터 연동)
- **Mistral AI** (Mistral Large, Codestral, Pixtral Vision)
- **Cohere** (Command R+, Embed v3.0, Rerank 모델)
- **OpenRouter** (다양한 오픈소스 및 상용 모델 라우팅)

### 데이터 업데이트 주기

- 자동: 6시간마다 (GitHub Actions)
- 수동: Actions 탭에서 'Update AI Models Data' 워크플로우 실행

### 크롤러 추가 방법

새로운 AI 제공업체를 추가하려면:

1. `scripts/crawlers/` 디렉토리에 새 크롤러 생성
2. `base_crawler.py`를 상속받아 구현
3. `scripts/run_all_crawlers.py`에 추가
4. GitHub Actions 워크플로우 업데이트

## 🔧 커스터마이징

### 테마 색상 변경

`tailwind.config.js`에서 색상 팔레트 수정:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // 원하는 색상으로 변경
      }
    }
  }
}
```

### 새로운 기능 추가

1. `src/js/` 디렉토리에 새 모듈 생성
2. `app.js`에서 import 및 초기화
3. 필요시 HTML 구조 업데이트

## 📈 성능 최적화

- **정적 파일 압축**: esbuild와 Tailwind CSS의 minification
- **이미지 최적화**: SVG 아이콘 사용
- **캐싱**: 브라우저 캐싱 및 GitHub Pages CDN 활용
- **코드 분할**: 동적 import를 통한 필요시 로딩

## 🤝 기여 방법

1. Fork 및 새 브랜치 생성
2. 변경사항 구현
3. 테스트 확인
4. Pull Request 제출

### 기여 가이드라인

- 코드 스타일 일관성 유지
- 주석 및 문서화 충실
- 새 기능은 이슈 생성 후 논의
- 커밋 메시지는 명확하게

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🙏 크레딧

- 데이터 출처: 각 AI 제공업체 공식 웹사이트
- 아이콘: Heroicons
- 차트: Chart.js
- CSS Framework: Tailwind CSS

## 💡 문제 해결

### 데이터가 업데이트되지 않는 경우

1. GitHub Actions 권한 확인
2. 크롤러 로그 확인
3. API 키 설정 확인 (필요한 경우)

### 빌드 오류

```bash
# 캐시 삭제 및 재설치
rm -rf node_modules package-lock.json
npm install
```

### 로컬 테스트

```bash
# 크롤러 테스트
python scripts/crawlers/openai_crawler.py

# 데이터 통합 테스트
python scripts/data_processor.py
```

## 📮 연락처

질문이나 제안사항이 있으시면 이슈를 생성해주세요.

---

Made with ❤️ for the AI community