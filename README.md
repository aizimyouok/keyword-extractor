# 🔍 키워드 추출 & 관리 도구

HTML에서 키워드를 추출하고 구글시트로 체계적으로 관리하는 Streamlit 앱입니다.

## ✨ 주요 기능

- 🔍 **HTML 소스 분석**: 웹페이지에서 자동으로 키워드 추출
- 🎯 **키워드 선택**: 필요한 키워드만 골라서 선택
- 💾 **구글시트 저장**: 프로젝트별로 분류하여 저장  
- 📊 **키워드 관리**: 사용여부 체크 및 메모 기능
- 📈 **통계 제공**: 사용률 및 프로젝트별 현황

## 🚀 빠른 시작

### 1. 설치
```bash
git clone <repository-url>
cd keyword-extractor
pip install -r requirements.txt
```

### 2. 구글시트 설정 (🔐 중요!)
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Google Sheets API & Google Drive API 활성화
3. 서비스 계정 생성 및 JSON 키 다운로드
4. 구글시트 생성 후 서비스 계정에 편집 권한 부여
5. **보안 설정**:
   ```bash
   # 템플릿 복사
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   
   # secrets.toml 파일 편집 (실제 값 입력)
   # ⚠️ 이 파일은 .gitignore에 의해 깃허브에 업로드되지 않습니다
   ```

### 3. 실행
```bash
streamlit run app.py
```

## 📁 파일 구조

```
keyword-extractor/
├── app.py                   # 메인 애플리케이션
├── requirements.txt         # 의존성 목록
├── .gitignore              # 보안 파일 제외 설정
├── .streamlit/
│   ├── secrets.toml        # 🔐 인증 정보 (로컬 전용, 업로드 금지!)
│   └── secrets.toml.example # 📋 설정 템플릿 (안전)
└── README.md               # 이 파일
```

## 🔐 보안 주의사항

⚠️ **절대 깃허브에 올리면 안 되는 파일:**
- `.streamlit/secrets.toml` - 구글 API 인증 정보
- `*.json` - 서비스 계정 키 파일

✅ **안전하게 관리되는 파일:**
- `.gitignore`가 자동으로 보안 파일들을 제외
- `secrets.toml.example`은 템플릿이므로 안전

## 🎯 사용 방법

1. **키워드 추출**: 웹페이지 소스를 복사 → 붙여넣기 → 추출
2. **키워드 선택**: 필요한 키워드들을 클릭하여 선택
3. **프로젝트 저장**: 프로젝트명 입력 후 구글시트에 저장
4. **키워드 관리**: 저장된 키워드의 사용여부 체크 및 메모 작성

## 📊 구글시트 구조

| 날짜 | 프로젝트명 | 키워드 | 사용여부 | 메모 |
|------|------------|--------|----------|------|
| 2025-06-19 | 블로그_A | 키워드1 | ✅ | 작성 완료 |
| 2025-06-19 | 블로그_A | 키워드2 | ❌ | 준비중 |

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **HTML 파싱**: BeautifulSoup4  
- **데이터 처리**: Pandas
- **저장소**: Google Sheets
- **연동**: streamlit-gsheets

## 💡 활용 예시

- 📝 **블로그 키워드 관리**: 글감 발굴 및 작성 현황 추적
- 🎯 **마케팅 키워드**: 캠페인별 키워드 분류 및 성과 관리
- 📊 **SEO 키워드**: 검색어 발굴 및 콘텐츠 제작 계획
- 🔍 **경쟁사 분석**: 경쟁사 키워드 수집 및 분석

## 🔄 향후 계획

- [ ] 프로젝트별 대시보드
- [ ] 키워드 카테고리 분류
- [ ] CSV 내보내기/가져오기  
- [ ] 키워드 트렌드 분석
- [ ] 팀 협업 기능

---

**Made with ❤️ using Streamlit & Google Sheets**