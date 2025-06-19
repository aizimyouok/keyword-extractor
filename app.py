# 구분선 추가 함수
def add_section_divider(title=""):
    if title:
        st.markdown(f"""
        <div style="margin: 2rem 0 1.5rem 0;">
            <div style="border-top: 2px solid #667eea; padding-top: 1rem;">
                <h3 style="color: #667eea; margin: 0; font-size: 1.3rem; font-weight: 600;">
                    {title}
                </h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin: 2rem 0;">
            <div style="border-top: 1px solid #404040;"></div>
        </div>
        """, unsafe_allow_html=True)import streamlit as st
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
        
        # 기존 데이터 읽기 시도
        existing_df = pd.DataFrame()
        sheet_names = ["키워드관리", "Sheet1", "시트1", None]
        used_sheet_name = None
        
        for sheet_name in sheet_names:
            try:
                if sheet_name:
                    existing_df = conn.read(worksheet=sheet_name)
                else:
                    existing_df = conn.read()
                
                if not existing_df.empty:
                    used_sheet_name = sheet_name
                    break
                    
            except:
                continue
        
        # 기존 데이터와 병합
        if not existing_df.empty:
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            updated_df = new_df
            used_sheet_name = "Sheet1"  # 기본 시트 이름
        
        # 업데이트
        if used_sheet_name:
            conn.update(worksheet=used_sheet_name, data=updated_df)
            st.session_state['last_saved_sheet'] = used_sheet_name
        else:
            conn.update(data=updated_df)
            st.session_state['last_saved_sheet'] = "기본 시트"
            
        return True
        
    except Exception as e:
        st.error(f"키워드 저장 실패: {e}")
        return False

def load_keywords_from_sheet(conn):
    """구글시트에서 키워드 불러오기"""
    if not conn:
        return pd.DataFrame()
    
    try:
        # 여러 시트 이름 시도
        sheet_names = ["키워드관리", "Sheet1", "시트1", None]  # None은 첫 번째 시트
        
        for sheet_name in sheet_names:
            try:
                if sheet_name:
                    df = conn.read(worksheet=sheet_name)
                else:
                    df = conn.read()  # 첫 번째 시트 읽기
                
                # 데이터가 있고 필요한 컬럼이 있는지 확인
                if not df.empty and '키워드' in df.columns:
                    st.success(f"✅ 시트 '{sheet_name or '첫번째 시트'}'에서 데이터를 불러왔습니다!")
                    return df
                    
            except Exception as sheet_error:
                continue
        
        # 모든 시트에서 실패한 경우
        st.warning("⚠️ 키워드 데이터를 찾을 수 없습니다. 구글시트를 확인해주세요.")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ 구글시트 연결 오류: {e}")
        return pd.DataFrame()

def update_keyword_usage(conn, original_index, used_status, memo=""):
    """키워드 사용여부 업데이트 (인덱스 문제 해결)"""
    if not conn:
        return False
    
    try:
        # 원본 데이터 읽기
        sheet_names = ["키워드관리", "Sheet1", "시트1", None]
        
        for sheet_name in sheet_names:
            try:
                if sheet_name:
                    df = conn.read(worksheet=sheet_name)
                else:
                    df = conn.read()
                
                if not df.empty and '키워드' in df.columns and original_index < len(df):
                    # 사용여부 업데이트
                    df.loc[original_index, '사용여부'] = '✅' if used_status else '❌'
                    
                    # 메모 업데이트
                    if memo:
                        df.loc[original_index, '메모'] = memo
                    
                    # 구글시트에 업데이트
                    if sheet_name:
                        conn.update(worksheet=sheet_name, data=df)
                    else:
                        conn.update(data=df)
                    
                    return True
                    
            except Exception as sheet_error:
                continue
                
        return False
        
    except Exception as e:
        st.error(f"❌ 사용여부 업데이트 실패: {e}")
        return False

# ---------------- 세션 상태 초기화 ----------------
def initialize_session_state():
    defaults = {
        'keywords_list': [],
        'selected_keywords': [],
        'saved_keywords_df': pd.DataFrame(),
        'extraction_count': 0,
        'session_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ---------------- 메인 UI ----------------

# 헤더 영역 (통계를 오른쪽 상단에 작게 배치)
header_col1, header_col2 = st.columns([3, 1])

with header_col1:
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <div style="font-size: 3rem; font-weight: 700; color: #ffffff; margin-bottom: 1rem; 
                    letter-spacing: -0.02em; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
            🔍 키워드 추출 & 관리 도구
        </div>
        <div style="font-size: 1.2rem; color: #b0b0b0; font-weight: 400; line-height: 1.6;">
            HTML에서 키워드를 추출하고 구글시트로 체계적으로 관리하세요
        </div>
    </div>
    """, unsafe_allow_html=True)

# 구글시트 연결하고 저장된 키워드 수 실시간 확인
conn = get_google_sheet_connection()
if conn:
    current_saved_df = load_keywords_from_sheet(conn)
    total_saved = len(current_saved_df) if not current_saved_df.empty else 0
else:
    total_saved = 0

with header_col2:
    # 통계 정보를 오른쪽 상단에 작게 표시
    keywords_count = len(st.session_state.get('keywords_list', []))
    
    st.markdown(f"""
    <div style="text-align: right; margin-top: 1rem;">
        <div style="background: #2a2a2a; border-radius: 12px; padding: 1rem; border: 1px solid #333333; margin-bottom: 0.5rem;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #667eea; margin-bottom: 0.3rem;">{keywords_count}</div>
            <div style="font-size: 0.8rem; color: #b0b0b0;">추출된 키워드</div>
        </div>
        <div style="background: #2a2a2a; border-radius: 12px; padding: 1rem; border: 1px solid #333333;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #667eea; margin-bottom: 0.3rem;">{total_saved}</div>
            <div style="font-size: 0.8rem; color: #b0b0b0;">총 저장된 키워드</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 구글시트 연결 상태 표시
if conn:
    st.success("✅ 구글시트가 성공적으로 연결되었습니다!")
else:
    st.warning("⚠️ 구글시트 연결을 확인해주세요. secrets.toml 파일에 인증 정보가 설정되어 있나요?")

# 1. 키워드 추출 섹션
add_section_divider("🔍 HTML 소스 분석")

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
                st.success(f"✅ 키워드 추출 완료! (총 {len(st.session_state['keywords_list'])}개)")
                st.rerun()
            else:
                st.warning("⚠️ 키워드를 찾지 못했습니다. HTML 소스를 확인해주세요.")
        else:
            st.error("❌ HTML 소스를 입력해주세요.")

with col2:
    if st.session_state.get('keywords_list'):
        st.info(f"💡 {len(st.session_state['keywords_list'])}개 키워드 발견!")

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
    add_section_divider("💾 구글시트에 저장")
    
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
                    saved_sheet = st.session_state.get('last_saved_sheet', '구글시트')
                    st.success(f"✅ {len(st.session_state['selected_keywords'])}개 키워드가 성공적으로 저장되었습니다! (저장 위치: {saved_sheet})")
                    # 저장 후 선택 해제
                    st.session_state['selected_keywords'] = []
                    st.rerun()
                else:
                    st.error("❌ 저장 중 오류가 발생했습니다.")
            else:
                st.warning("⚠️ 프로젝트명을 입력해주세요.")
    
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

# 4. 저장된 키워드 관리 섹션
if conn:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title"><span class="emoji">📊</span>저장된 키워드 관리</div>', unsafe_allow_html=True)
    
    # 새로고침 버튼과 디버그 정보
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🔍 연결 테스트", use_container_width=True):
            if conn:
                try:
                    # 모든 시트 정보 확인
                    test_df = conn.read()
                    st.success(f"✅ 연결 성공! {len(test_df)}개 행 발견")
                    st.info(f"컬럼: {list(test_df.columns) if not test_df.empty else '없음'}")
                except Exception as e:
                    st.error(f"❌ 연결 실패: {e}")
            else:
                st.error("❌ 구글시트 연결이 안되어 있습니다")
    
    with col3:
        debug_mode = st.checkbox("🐛 디버그 모드")
    
    # 저장된 키워드 불러오기
    saved_df = load_keywords_from_sheet(conn)
    
    if debug_mode and not saved_df.empty:
        st.markdown("#### 🐛 디버그 정보")
        st.write(f"**데이터 형태**: {saved_df.shape}")
        st.write(f"**컬럼명**: {list(saved_df.columns)}")
        st.write(f"**데이터 타입**: {saved_df.dtypes.to_dict()}")
        st.dataframe(saved_df.head(3), use_container_width=True)
    
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
        st.markdown("#### 📝 키워드 목록")
        
        if not filtered_df.empty:
            # 키워드별로 카드 형태로 표시
            for idx, row in filtered_df.iterrows():
                with st.container():
                    # 카드 스타일 컨테이너
                    st.markdown('<div style="background: #333333; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid #404040;">', unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**🔑 {row['키워드']}**")
                        st.caption(f"📁 {row['프로젝트명']} | 📅 {str(row['날짜']).split()[0] if ' ' in str(row['날짜']) else row['날짜']}")
                    
                    with col2:
                        # 메모 입력
                        current_memo = row.get('메모', '')
                        new_memo = st.text_input(
                            "메모", 
                            value=current_memo,
                            key=f"memo_input_{idx}",
                            placeholder="메모를 입력하세요..."
                        )
                    
                    with col3:
                        # 사용여부 토글
                        current_status = row['사용여부'] == '✅'
                        new_status = st.checkbox(
                            "사용완료",
                            value=current_status,
                            key=f"status_check_{idx}"
                        )
                    
                    with col4:
                        # 저장 버튼
                        if st.button("💾 저장", key=f"save_btn_{idx}", use_container_width=True):
                            # 변경사항이 있으면 업데이트
                            if new_status != current_status or new_memo != current_memo:
                                success = update_keyword_usage(conn, idx, new_status, new_memo)
                                if success:
                                    st.success("✅ 업데이트 완료!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ 업데이트 실패")
                            else:
                                st.info("변경사항이 없습니다.")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.markdown("""
            <div class="info-message">
                📝 필터 조건에 맞는 키워드가 없습니다.
            </div>
            """, unsafe_allow_html=True)
        
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
            📝 아직 저장된 키워드가 없습니다. 키워드를 추출하고 저장해보세요!<br><br>
            💡 <strong>저장된 키워드가 안 보인다면:</strong><br>
            • 구글시트에 데이터가 있는지 확인해보세요<br>
            • 새로고침 버튼을 눌러보세요<br>
            • 구글시트의 시트 이름을 확인해보세요 (권장: "키워드관리")
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 푸터
add_section_divider()
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #808080;">
    <p style="font-size: 1.1rem; margin-bottom: 0.5rem; font-weight: 600;">🔍 키워드 추출 & 관리 도구</p>
    <p style="font-size: 0.9rem; margin: 0;">HTML에서 키워드를 추출하고 구글시트로 체계적으로 관리하세요!</p>
</div>
""", unsafe_allow_html=True)
