import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

# 구글시트 연동을 위한 import
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    st.warning("⚠️ streamlit-gsheets가 설치되지 않았습니다. 'pip install streamlit-gsheets' 명령으로 설치해주세요.")

# ---------------- 페이지 기본 설정 ----------------
st.set_page_config(
    page_title="키워드 추출 & 관리 도구", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- 스타일 CSS ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #1a1a1a;
        color: #ffffff;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .main-header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 3rem 0;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        color: #b0b0b0;
        font-weight: 400;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3rem;
    }
    
    .stat-card {
        background: #2a2a2a;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        border: 1px solid #333333;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: #667eea;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #b0b0b0;
        font-weight: 500;
    }
    
    .content-card {
        background: #2a2a2a;
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid #333333;
        transition: all 0.3s ease;
    }
    
    .content-card:hover {
        border-color: #404040;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
    }
    
    .card-title .emoji {
        margin-right: 1rem;
        font-size: 1.8rem;
    }
    
    .success-message {
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.1) 0%, rgba(56, 161, 105, 0.1) 100%);
        border: 1px solid #48bb78;
        border-left: 4px solid #48bb78;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 1.5rem 0;
        color: #68d391;
        font-weight: 500;
    }
    
    .warning-message {
        background: linear-gradient(135deg, rgba(237, 137, 54, 0.1) 0%, rgba(221, 107, 32, 0.1) 100%);
        border: 1px solid #ed8936;
        border-left: 4px solid #ed8936;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 1.5rem 0;
        color: #f6ad55;
        font-weight: 500;
    }
    
    .error-message {
        background: linear-gradient(135deg, rgba(245, 101, 101, 0.1) 0%, rgba(229, 62, 62, 0.1) 100%);
        border: 1px solid #f56565;
        border-left: 4px solid #f56565;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 1.5rem 0;
        color: #fc8181;
        font-weight: 500;
    }
    
    .info-message {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid #667eea;
        border-left: 4px solid #667eea;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 1.5rem 0;
        color: #a78bfa;
        font-weight: 500;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3) !important;
        text-transform: none !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
    }
    
    .stTextArea > div > div > textarea,
    .stTextInput > div > div > input {
        background: #333333 !important;
        border: 1px solid #404040 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea > div > div > textarea:focus,
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
        outline: none !important;
    }
    
    .keyword-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .keyword-chip {
        background: #333333;
        border: 1px solid #404040;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.95rem;
        font-weight: 500;
        color: #ffffff;
    }
    
    .keyword-chip:hover {
        border-color: #667eea;
        background: #404040;
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    .keyword-chip.selected {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: #667eea;
        color: #ffffff;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ---------------- 유틸리티 함수들 ----------------

def parse_keywords_from_html(html_content):
    """HTML에서 키워드 추출"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        selector = '.keyword, .keyword-blur, .end-board-td-blur'
        keyword_tags = soup.select(selector)
        
        seen = set()
        unique_keywords = []
        
        for tag in keyword_tags:
            text = tag.get_text(strip=True)
            if text and text not in seen and len(text) >= 2:
                seen.add(text)
                unique_keywords.append(text)
        
        return unique_keywords[:100]  # 최대 100개
        
    except Exception as e:
        st.error(f"HTML 분석 중 오류: {e}")
        return []

def get_google_sheet_connection():
    """구글시트 연결"""
    if not GSHEETS_AVAILABLE:
        return None
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn
    except Exception as e:
        st.error(f"구글시트 연결 실패: {e}")
        return None

def save_keywords_to_sheet(conn, project_name, keywords_list):
    """키워드를 구글시트에 저장"""
    if not conn:
        return False
    
    try:
        # 새로운 데이터 준비
        new_data = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for keyword in keywords_list:
            new_data.append({
                '날짜': current_time,
                '프로젝트명': project_name,
                '키워드': keyword,
                '사용여부': '❌',
                '메모': ''
            })
        
        # 데이터프레임으로 변환
        new_df = pd.DataFrame(new_data)
        
        # 기존 데이터 읽기
        try:
            existing_df = conn.read(worksheet="키워드관리")
            # 새 데이터를 기존 데이터에 추가
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        except:
            # 시트가 없거나 비어있는 경우 새로 생성
            updated_df = new_df
        
        # 업데이트
        conn.update(worksheet="키워드관리", data=updated_df)
        return True
        
    except Exception as e:
        st.error(f"키워드 저장 실패: {e}")
        return False

def load_keywords_from_sheet(conn):
    """구글시트에서 키워드 불러오기"""
    if not conn:
        return pd.DataFrame()
    
    try:
        df = conn.read(worksheet="키워드관리")
        return df
    except Exception as e:
        st.warning(f"저장된 키워드를 불러올 수 없습니다: {e}")
        return pd.DataFrame()

def update_keyword_usage(conn, index, used_status, memo=""):
    """키워드 사용여부 업데이트"""
    if not conn:
        return False
    
    try:
        df = conn.read(worksheet="키워드관리")
        if index < len(df):
            df.loc[index, '사용여부'] = '✅' if used_status else '❌'
            if memo:
                df.loc[index, '메모'] = memo
            
            conn.update(worksheet="키워드관리", data=df)
            return True
        return False
    except Exception as e:
        st.error(f"사용여부 업데이트 실패: {e}")
        return False

# ---------------- 세션 상태 초기화 ----------------
def initialize_session_state():
    defaults = {
        'keywords_list': [],
        'selected_keywords': [],
        'saved_keywords_df': pd.DataFrame(),
        'extraction_count': 0,
        'total_saved': 0,
        'session_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ---------------- 메인 UI ----------------

# 헤더 영역
st.markdown("""
<div class="main-header">
    <div class="main-title">🔍 키워드 추출 & 관리 도구</div>
    <div class="main-subtitle">HTML에서 키워드를 추출하고 구글시트로 체계적으로 관리하세요</div>
</div>
""", unsafe_allow_html=True)

# 통계 카드
keywords_count = len(st.session_state.get('keywords_list', []))
selected_count = len(st.session_state.get('selected_keywords', []))
total_saved = len(st.session_state.get('saved_keywords_df', pd.DataFrame()))

st.markdown(f"""
<div class="stats-grid">
    <div class="stat-card">
        <span class="stat-number">{keywords_count}</span>
        <div class="stat-label">추출된 키워드</div>
    </div>
    <div class="stat-card">
        <span class="stat-number">{selected_count}</span>
        <div class="stat-label">선택된 키워드</div>
    </div>
    <div class="stat-card">
        <span class="stat-number">{total_saved}</span>
        <div class="stat-label">총 저장된 키워드</div>
    </div>
    <div class="stat-card">
        <span class="stat-number">{st.session_state['extraction_count']}</span>
        <div class="stat-label">추출 작업 횟수</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 구글시트 연결 확인
conn = get_google_sheet_connection()
if conn:
    st.markdown("""
    <div class="success-message">
        ✅ 구글시트가 성공적으로 연결되었습니다!
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="warning-message">
        ⚠️ 구글시트 연결을 확인해주세요. secrets.toml 파일에 인증 정보가 설정되어 있나요?
    </div>
    """, unsafe_allow_html=True)

# 1. 키워드 추출 섹션
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title"><span class="emoji">🔍</span>HTML 소스 분석</div>', unsafe_allow_html=True)

html_input = st.text_area(
    "웹사이트 페이지 소스를 붙여넣으세요",
    height=200,
    placeholder="<DOCTYPE html>...",
    help="Ctrl+U → Ctrl+A → Ctrl+C → 여기에 붙여넣기"
)

col1, col2 = st.columns([2, 1])
with col1:
    if st.button("🔍 키워드 추출 시작", type="primary", use_container_width=True):
        if html_input:
            with st.spinner("키워드를 추출하고 있습니다..."):
                keywords = parse_keywords_from_html(html_input)
                st.session_state['keywords_list'] = keywords
                st.session_state['selected_keywords'] = []
                st.session_state['extraction_count'] += 1
            
            if st.session_state['keywords_list']:
                st.markdown(f"""
                <div class="success-message">
                    ✅ 키워드 추출 완료! (총 {len(st.session_state['keywords_list'])}개)
                </div>
                """, unsafe_allow_html=True)
                st.rerun()
            else:
                st.markdown("""
                <div class="warning-message">
                    ⚠️ 키워드를 찾지 못했습니다. HTML 소스를 확인해주세요.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-message">
                ❌ HTML 소스를 입력해주세요.
            </div>
            """, unsafe_allow_html=True)

with col2:
    if st.session_state.get('keywords_list'):
        st.markdown(f"""
        <div class="info-message">
            💡 {len(st.session_state['keywords_list'])}개 키워드 발견!
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 2. 키워드 선택 섹션
if st.session_state.get('keywords_list'):
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title"><span class="emoji">🎯</span>키워드 선택</div>', unsafe_allow_html=True)
    
    # 전체 선택/해제 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ 전체 선택", use_container_width=True):
            st.session_state['selected_keywords'] = st.session_state['keywords_list'].copy()
            st.rerun()
    
    with col2:
        if st.button("❌ 전체 해제", use_container_width=True):
            st.session_state['selected_keywords'] = []
            st.rerun()
    
    with col3:
        if st.session_state.get('selected_keywords'):
            st.markdown(f"""
            <div class="success-message">
                ✅ 선택된 키워드: {len(st.session_state['selected_keywords'])}개
            </div>
            """, unsafe_allow_html=True)
    
    # 키워드를 4개씩 나누어 표시
    keywords = st.session_state['keywords_list']
    cols_per_row = 4
    
    for i in range(0, len(keywords), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(keywords):
                keyword = keywords[i + j]
                is_selected = keyword in st.session_state.get('selected_keywords', [])
                
                with col:
                    button_type = "primary" if is_selected else "secondary"
                    
                    if st.button(
                        keyword, 
                        key=f"keyword_btn_{i+j}",
                        type=button_type,
                        use_container_width=True
                    ):
                        # 키워드 선택/해제 토글
                        if keyword in st.session_state['selected_keywords']:
                            st.session_state['selected_keywords'].remove(keyword)
                        else:
                            st.session_state['selected_keywords'].append(keyword)
                        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# 3. 저장 섹션
if st.session_state.get('selected_keywords') and conn:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title"><span class="emoji">💾</span>구글시트에 저장</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        project_name = st.text_input(
            "프로젝트명을 입력하세요",
            placeholder="예: 블로그_A, 마케팅_캠페인_2025",
            help="키워드를 분류할 프로젝트명을 입력하세요"
        )
    
    with col2:
        if st.button("💾 구글시트에 저장", type="primary", use_container_width=True):
            if project_name:
                with st.spinner("구글시트에 저장 중..."):
                    success = save_keywords_to_sheet(conn, project_name, st.session_state['selected_keywords'])
                
                if success:
                    st.markdown(f"""
                    <div class="success-message">
                        ✅ {len(st.session_state['selected_keywords'])}개 키워드가 성공적으로 저장되었습니다!
                    </div>
                    """, unsafe_allow_html=True)
                    # 저장 후 선택 해제
                    st.session_state['selected_keywords'] = []
                    st.rerun()
                else:
                    st.markdown("""
                    <div class="error-message">
                        ❌ 저장 중 오류가 발생했습니다.
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="warning-message">
                    ⚠️ 프로젝트명을 입력해주세요.
                </div>
                """, unsafe_allow_html=True)
    
    # 선택된 키워드 미리보기
    if st.session_state.get('selected_keywords'):
        st.markdown("#### 📋 저장할 키워드 목록")
        selected_text = " | ".join(st.session_state['selected_keywords'])
        st.text_area(
            f"선택된 키워드 ({len(st.session_state['selected_keywords'])}개)",
            value=selected_text,
            height=100,
            help="저장할 키워드 목록입니다"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

# 4. 저장된 키워드 관리 섹션
if conn:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title"><span class="emoji">📊</span>저장된 키워드 관리</div>', unsafe_allow_html=True)
    
    # 새로고침 버튼
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    # 저장된 키워드 불러오기
    saved_df = load_keywords_from_sheet(conn)
    
    if not saved_df.empty:
        st.session_state['saved_keywords_df'] = saved_df
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            projects = ['전체'] + list(saved_df['프로젝트명'].unique())
            selected_project = st.selectbox("프로젝트 필터", projects)
        
        with col2:
            usage_filter = st.selectbox("사용여부 필터", ['전체', '사용함(✅)', '미사용(❌)'])
        
        with col3:
            if st.button("📊 통계 보기"):
                total_keywords = len(saved_df)
                used_keywords = len(saved_df[saved_df['사용여부'] == '✅'])
                usage_rate = (used_keywords / total_keywords * 100) if total_keywords > 0 else 0
                
                st.markdown(f"""
                <div class="info-message">
                    📈 전체 키워드: {total_keywords}개<br>
                    ✅ 사용한 키워드: {used_keywords}개<br>
                    📊 사용률: {usage_rate:.1f}%
                </div>
                """, unsafe_allow_html=True)
        
        # 필터 적용
        filtered_df = saved_df.copy()
        
        if selected_project != '전체':
            filtered_df = filtered_df[filtered_df['프로젝트명'] == selected_project]
        
        if usage_filter == '사용함(✅)':
            filtered_df = filtered_df[filtered_df['사용여부'] == '✅']
        elif usage_filter == '미사용(❌)':
            filtered_df = filtered_df[filtered_df['사용여부'] == '❌']
        
        # 키워드 목록 표시 (편집 가능)
        st.markdown("#### 📝 키워드 목록 (사용여부 클릭으로 변경 가능)")
        
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
            
            with col1:
                st.write(f"**{row['키워드']}**")
            
            with col2:
                st.write(row['프로젝트명'])
            
            with col3:
                current_status = row['사용여부'] == '✅'
                if st.button(
                    row['사용여부'], 
                    key=f"status_{idx}",
                    help="클릭하여 사용여부 변경"
                ):
                    new_status = not current_status
                    if update_keyword_usage(conn, idx, new_status):
                        st.success("✅ 사용여부가 업데이트되었습니다!")
                        st.rerun()
            
            with col4:
                st.write(row['날짜'].split()[0] if ' ' in str(row['날짜']) else row['날짜'])
            
            with col5:
                memo = st.text_input(
                    "메모", 
                    value=row.get('메모', ''),
                    key=f"memo_{idx}",
                    placeholder="메모 입력..."
                )
                if st.button("💾", key=f"save_memo_{idx}", help="메모 저장"):
                    if update_keyword_usage(conn, idx, row['사용여부'] == '✅', memo):
                        st.success("메모가 저장되었습니다!")
                        st.rerun()
        
        # 데이터프레임으로도 표시
        st.markdown("#### 📊 전체 데이터")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.markdown("""
        <div class="info-message">
            📝 아직 저장된 키워드가 없습니다. 키워드를 추출하고 저장해보세요!
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 3rem 0; color: #808080;">
    <p style="font-size: 1.2rem; margin-bottom: 0.5rem; font-weight: 600;">🔍 키워드 추출 & 관리 도구</p>
    <p style="font-size: 1rem; margin: 0;">HTML에서 키워드를 추출하고 구글시트로 체계적으로 관리하세요!</p>
</div>
""", unsafe_allow_html=True)