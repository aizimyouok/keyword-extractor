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
    st.warning("⚠️ streamlit-gsheets가 설치되지 않았습니다. 'pip install st-gsheets-connection' 명령으로 설치해주세요.")

# ---------------- 유틸리티 함수들 ----------------

def parse_keywords_from_html(html_content, existing_keywords=None):
    """HTML에서 키워드 추출 (중복 제거 포함)"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        selector = '.keyword, .keyword-blur, .end-board-td-blur'
        keyword_tags = soup.select(selector)
        
        if existing_keywords is None:
            existing_keywords = set()
        
        seen = set()
        unique_keywords = []
        duplicate_count = 0
        
        for tag in keyword_tags:
            text = tag.get_text(strip=True)
            if text and len(text) >= 2:
                # 기존 키워드와 중복 체크
                if text in existing_keywords:
                    duplicate_count += 1
                    continue
                
                # 이번 추출에서 중복 체크
                if text not in seen:
                    seen.add(text)
                    unique_keywords.append(text)
        
        # 중복 제거 정보를 세션에 저장
        st.session_state['extraction_info'] = {
            'total_found': len(keyword_tags),
            'duplicates_removed': duplicate_count,
            'new_keywords': len(unique_keywords)
        }
        
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

def load_keywords_from_sheet(conn, force_refresh=False):
    """구글시트에서 키워드 불러오기"""
    if not conn:
        return pd.DataFrame()
    
    # 강제 새로고침이 요청되거나 캐시가 없으면 새로 로드
    cache_key = 'cached_keywords_df'
    if force_refresh or cache_key not in st.session_state:
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
                        # 캐시에 저장
                        st.session_state[cache_key] = df
                        # 성공 메시지를 세션에 저장 (한번만 표시)
                        if 'sheet_load_success' not in st.session_state:
                            st.session_state['sheet_load_success'] = f"시트 '{sheet_name or '첫번째 시트'}'"
                        return df
                        
                except Exception as sheet_error:
                    continue
            
            # 모든 시트에서 실패한 경우
            st.warning("⚠️ 키워드 데이터를 찾을 수 없습니다. 구글시트를 확인해주세요.")
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"❌ 구글시트 연결 오류: {e}")
            return pd.DataFrame()
    else:
        # 캐시된 데이터 반환
        return st.session_state.get(cache_key, pd.DataFrame())

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

def add_section_divider(title=""):
    """구분선 추가 함수"""
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
        """, unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
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
    
    /* 헤더 영역 - 간소화 */
    .main-header {
        margin-bottom: 2rem;
        padding: 2rem 0;
    }
    
    /* 통계 카드 영역 - 제거됨, 오른쪽 상단으로 이동 */
    
    /* 카드 스타일 - 간소화 */
    .content-card {
        background: #2a2a2a;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #333333;
    }
    
    .card-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .card-title .emoji {
        margin-right: 0.8rem;
        font-size: 1.5rem;
    }
    
    /* 단계 표시기 - 제거됨 */
    
    /* 버튼 스타일 */
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
    
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #b0b0b0 !important;
        border: 2px solid #404040 !important;
        box-shadow: none !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #404040 !important;
        color: #ffffff !important;
        border-color: #606060 !important;
        transform: translateY(-2px) !important;
    }
    
    /* 입력 필드 스타일 */
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > div > div,
    .stNumberInput > div > div > input,
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
    .stSelectbox > div > div > div:focus,
    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
        outline: none !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: #808080 !important;
        font-style: italic;
    }
    
    /* 라벨 스타일 */
    .stTextArea label,
    .stSelectbox label,
    .stNumberInput label,
    .stTextInput label {
        font-weight: 600 !important;
        font-size: 1rem !important;
        color: #ffffff !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 키워드 그리드 - 간소화 */
    .keyword-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
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
    }
    
    .keyword-chip.selected {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: #667eea;
        color: #ffffff;
    }
    
    /* 메시지 스타일 - 간소화 */
    
    /* 탭 스타일 - 제거됨 */
    
    /* 메트릭 카드 - 간소화 */
    
    /* API 상태 - 제거됨 */
    
    /* 스크롤바 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #2a2a2a;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #404040;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #606060;
    }
    
    /* 선택된 텍스트 */
    ::selection {
        background: rgba(102, 126, 234, 0.3);
        color: #ffffff;
    }
    
    /* 반응형 - 간소화 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
        
        .keyword-grid {
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        }
        
        .content-card {
            padding: 1rem;
        }
    }
    
    /* 애니메이션 - 간소화 */
    @keyframes fadeInUp {
        from { 
            opacity: 0; 
            transform: translateY(10px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    /* 포커스 아웃라인 제거 */
    button:focus,
    input:focus,
    textarea:focus,
    select:focus {
        outline: none !important;
    }
    
    /* Streamlit 기본 스타일 오버라이드 */
    .main .stMarkdown,
    .main .stMarkdown p,
    .main .stMarkdown div,
    .main .stMarkdown span,
    .main .stMarkdown h1,
    .main .stMarkdown h2,
    .main .stMarkdown h3,
    .main .stMarkdown h4 {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- 세션 상태 초기화 ----------------
initialize_session_state()

# ---------------- 메인 UI 시작 ----------------

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
    # 처음 로드 시에는 캐시 사용, 저장 후에는 강제 새로고침
    current_saved_df = load_keywords_from_sheet(conn)
    total_saved = len(current_saved_df) if not current_saved_df.empty else 0
    # 기존 키워드 목록을 세션에 저장 (중복 체크용)
    if not current_saved_df.empty and '키워드' in current_saved_df.columns:
        st.session_state['existing_keywords'] = set(current_saved_df['키워드'].tolist())
    else:
        st.session_state['existing_keywords'] = set()
else:
    total_saved = 0
    st.session_state['existing_keywords'] = set()

with header_col2:
    # 통계 정보를 오른쪽 상단에 더 작게 표시 (가로로 배치)
    keywords_count = len(st.session_state.get('keywords_list', []))
    
    st.markdown(f"""
    <div style="text-align: right; margin-top: 1rem;">
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <div style="background: #2a2a2a; border-radius: 8px; padding: 0.5rem 0.8rem; border: 1px solid #333333; min-width: 70px;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #667eea; margin-bottom: 0.1rem;">{keywords_count}</div>
                <div style="font-size: 0.7rem; color: #b0b0b0;">추출됨</div>
            </div>
            <div style="background: #2a2a2a; border-radius: 8px; padding: 0.5rem 0.8rem; border: 1px solid #333333; min-width: 70px;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #667eea; margin-bottom: 0.1rem;">{total_saved}</div>
                <div style="font-size: 0.7rem; color: #b0b0b0;">총 저장</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 구글시트 연결 상태 표시 (작게, 한 줄로)
connection_status = ""
if conn:
    if not current_saved_df.empty:
        connection_status = f'<span style="color: #10b981; font-size: 0.85rem;">✅ 구글시트 연결됨 | 시트에서 데이터 로드됨</span>'
    else:
        connection_status = f'<span style="color: #10b981; font-size: 0.85rem;">✅ 구글시트 연결됨</span>'
else:
    connection_status = f'<span style="color: #f59e0b; font-size: 0.85rem;">⚠️ 구글시트 연결 확인 필요</span>'

# 성공 메시지를 세션에 저장하고 일정 시간 후 숨김
if 'show_connection_status' not in st.session_state:
    st.session_state['show_connection_status'] = True

if st.session_state.get('show_connection_status', True):
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem;">
        {connection_status}
    </div>
    """, unsafe_allow_html=True)
    
    # 5초 후 상태 메시지 숨김 (자동으로는 안되니 수동으로 버튼 제공)
    if conn and not current_saved_df.empty:
        # 성공적으로 연결되고 데이터도 있으면 버튼으로 숨길 수 있게
        if st.button("✖", help="상태 메시지 숨기기", key="hide_status"):
            st.session_state['show_connection_status'] = False
            st.rerun()

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
                # 기존 키워드 목록 가져오기
                existing_keywords = st.session_state.get('existing_keywords', set())
                keywords = parse_keywords_from_html(html_input, existing_keywords)
                st.session_state['keywords_list'] = keywords
                st.session_state['selected_keywords'] = []
                st.session_state['extraction_count'] += 1
            
            # 추출 결과 표시
            extraction_info = st.session_state.get('extraction_info', {})
            if st.session_state['keywords_list']:
                success_msg = f"✅ 키워드 추출 완료! (새로운 키워드 {len(st.session_state['keywords_list'])}개)"
                if extraction_info.get('duplicates_removed', 0) > 0:
                    success_msg += f" | 중복 제거됨: {extraction_info['duplicates_removed']}개"
                st.success(success_msg)
                st.rerun()
            else:
                if extraction_info.get('duplicates_removed', 0) > 0:
                    st.warning(f"⚠️ 추출된 키워드가 모두 기존에 저장된 키워드와 중복됩니다. (중복 제거: {extraction_info['duplicates_removed']}개)")
                else:
                    st.warning("⚠️ 키워드를 찾지 못했습니다. HTML 소스를 확인해주세요.")
        else:
            st.error("❌ HTML 소스를 입력해주세요.")

with col2:
    if st.session_state.get('keywords_list'):
        extraction_info = st.session_state.get('extraction_info', {})
        info_text = f"💡 {len(st.session_state['keywords_list'])}개 새 키워드 발견!"
        if extraction_info.get('duplicates_removed', 0) > 0:
            info_text += f"\n(중복 {extraction_info['duplicates_removed']}개 제거됨)"
        st.info(info_text)

# 2. 수동 키워드 입력 섹션
add_section_divider("✏️ 수동 키워드 입력")

col1, col2 = st.columns([3, 1])

with col1:
    manual_keywords_input = st.text_area(
        "키워드를 직접 입력하세요 (쉼표로 구분)",
        height=100,
        placeholder="키워드1, 키워드2, 키워드3, ...",
        help="쉼표(,)로 구분하여 여러 키워드를 한번에 입력할 수 있습니다"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # 약간의 공간
    if st.button("📝 키워드 추가", type="primary", use_container_width=True):
        if manual_keywords_input.strip():
            # 쉼표로 분리하고 정리
            manual_keywords = [kw.strip() for kw in manual_keywords_input.split(',') if kw.strip()]
            
            if manual_keywords:
                # 기존 키워드와 중복 체크
                existing_keywords = st.session_state.get('existing_keywords', set())
                new_keywords = []
                duplicate_count = 0
                
                for keyword in manual_keywords:
                    if len(keyword) >= 2:  # 최소 2글자 이상
                        if keyword not in existing_keywords:
                            new_keywords.append(keyword)
                        else:
                            duplicate_count += 1
                
                if new_keywords:
                    # 기존 추출된 키워드와 합치기
                    current_keywords = st.session_state.get('keywords_list', [])
                    combined_keywords = current_keywords + new_keywords
                    st.session_state['keywords_list'] = combined_keywords
                    
                    success_msg = f"✅ {len(new_keywords)}개 키워드가 추가되었습니다!"
                    if duplicate_count > 0:
                        success_msg += f" (중복 제거: {duplicate_count}개)"
                    st.success(success_msg)
                    st.rerun()
                else:
                    if duplicate_count > 0:
                        st.warning(f"⚠️ 입력된 키워드가 모두 기존에 저장된 키워드와 중복됩니다. (중복: {duplicate_count}개)")
                    else:
                        st.warning("⚠️ 유효한 키워드가 없습니다. (최소 2글자 이상 입력해주세요)")
            else:
                st.warning("⚠️ 키워드를 입력해주세요.")
        else:
            st.error("❌ 키워드를 입력해주세요.")

# 입력된 키워드 미리보기 및 바로 저장 옵션
if manual_keywords_input.strip():
    preview_keywords = [kw.strip() for kw in manual_keywords_input.split(',') if kw.strip() and len(kw.strip()) >= 2]
    if preview_keywords:
        st.markdown("#### 🔍 입력 미리보기")
        col1, col2 = st.columns([3, 1])
        with col1:
            preview_text = " | ".join(preview_keywords)
            st.text_area(
                f"추가될 키워드 ({len(preview_keywords)}개)",
                value=preview_text,
                height=68,  # 최소 68px로 수정
                disabled=True
            )
        with col2:
            existing_keywords = st.session_state.get('existing_keywords', set())
            duplicates = [kw for kw in preview_keywords if kw in existing_keywords]
            if duplicates:
                st.warning(f"⚠️ 중복 {len(duplicates)}개")
            else:
                st.info(f"✅ 모두 새로운 키워드")
        
        # 바로 저장 옵션
        if conn:
            st.markdown("#### 💾 바로 저장하기")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                manual_project_name = st.text_input(
                    "프로젝트명 (바로 저장용)",
                    placeholder="예: 수동입력_키워드_모음",
                    help="프로젝트명을 입력하면 바로 구글시트에 저장됩니다",
                    key="manual_project_input"
                )
            
            with col2:
                if st.button("💾 바로 저장", use_container_width=True, key="manual_direct_save"):
                    if manual_project_name:
                        # 중복 제거된 새로운 키워드만 저장
                        existing_keywords = st.session_state.get('existing_keywords', set())
                        new_keywords_to_save = [kw for kw in preview_keywords if kw not in existing_keywords]
                        
                        if new_keywords_to_save:
                            with st.spinner("구글시트에 저장 중..."):
                                success = save_keywords_to_sheet(conn, manual_project_name, new_keywords_to_save)
                            
                            if success:
                                saved_sheet = st.session_state.get('last_saved_sheet', '구글시트')
                                st.success(f"✅ {len(new_keywords_to_save)}개 키워드가 성공적으로 저장되었습니다! (저장 위치: {saved_sheet})")
                                # 저장된 키워드들을 기존 키워드 목록에 추가
                                if 'existing_keywords' not in st.session_state:
                                    st.session_state['existing_keywords'] = set()
                                st.session_state['existing_keywords'].update(new_keywords_to_save)
                                # 캐시 클리어해서 즉시 업데이트 반영
                                st.session_state.pop('saved_keywords_df', None)
                                st.session_state.pop('cached_keywords_df', None)  # 새로운 캐시도 클리어
                                # 입력창도 비우기
                                st.session_state['manual_project_input'] = ""
                                st.rerun()
                            else:
                                st.error("❌ 저장 중 오류가 발생했습니다.")
                        else:
                            st.warning("⚠️ 저장할 새로운 키워드가 없습니다. (모두 중복)")
                    else:
                        st.warning("⚠️ 프로젝트명을 입력해주세요.")

# 3. 키워드 선택 섹션
if st.session_state.get('keywords_list'):
    add_section_divider("🎯 키워드 선택")
    
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
            st.success(f"✅ 선택된 키워드: {len(st.session_state['selected_keywords'])}개")
    
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
    
    # 선택된 키워드 관리
    if st.session_state.get('selected_keywords'):
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_text = " | ".join(st.session_state['selected_keywords'])
            st.text_area(
                f"선택된 키워드 ({len(st.session_state['selected_keywords'])}개)",
                value=selected_text,
                height=80,
                help="Ctrl+A로 전체 선택 후 Ctrl+C로 복사하세요"
            )
        
        with col2:
            if st.button("🔄 전체 해제", use_container_width=True, key="clear_selected"):
                st.session_state['selected_keywords'] = []
                st.rerun()

# 4. 저장 섹션
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
                    # 저장된 키워드들을 기존 키워드 목록에 추가 (중복 체크용)
                    if 'existing_keywords' not in st.session_state:
                        st.session_state['existing_keywords'] = set()
                    st.session_state['existing_keywords'].update(st.session_state['selected_keywords'])
                    # 캐시 클리어해서 즉시 업데이트 반영
                    st.session_state.pop('saved_keywords_df', None)
                    st.session_state.pop('cached_keywords_df', None)  # 새로운 캐시도 클리어
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

# 5. 저장된 키워드 관리 섹션 (토글 방식)
if conn:
    add_section_divider("📊 저장된 키워드 관리")
    
    # 새로고침 버튼과 디버그 정보
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        if st.button("🔄 새로고침", use_container_width=True):
            st.session_state.pop('saved_keywords_df', None)  # 캐시 클리어
            st.session_state.pop('cached_keywords_df', None)  # 새로운 캐시도 클리어
            st.session_state.pop('sheet_load_success', None)  # 성공 메시지 초기화
            st.rerun()
    
    with col2:
        if st.button("🔍 연결 테스트", use_container_width=True):
            if conn:
                try:
                    # 강제 새로고침으로 최신 데이터 확인
                    test_df = load_keywords_from_sheet(conn, force_refresh=True)
                    st.success(f"✅ 연결 성공! {len(test_df)}개 행 발견")
                    st.info(f"컬럼: {list(test_df.columns) if not test_df.empty else '없음'}")
                except Exception as e:
                    st.error(f"❌ 연결 실패: {e}")
            else:
                st.error("❌ 구글시트 연결이 안되어 있습니다")
    
    with col3:
        debug_mode = st.checkbox("🐛 디버그 모드")
    
    with col4:
        # 키워드 목록 토글 버튼
        show_keywords = st.checkbox("📋 키워드 목록 보기", value=False)
    
    with col5:
        # 전체 데이터 테이블 토글 버튼
        show_full_table = st.checkbox("📊 전체 테이블 보기", value=False)
    
    # 저장된 키워드 불러오기 (새로고침 버튼 눌렸으면 강제 새로고침)
    force_refresh = 'cached_keywords_df' not in st.session_state
    saved_df = load_keywords_from_sheet(conn, force_refresh=force_refresh)
    
    # 성공 메시지 표시 (한번만)
    if 'sheet_load_success' in st.session_state and st.session_state.get('show_connection_status', True):
        sheet_name = st.session_state['sheet_load_success']
        st.success(f"✅ {sheet_name}에서 데이터를 불러왔습니다!")
        # 메시지 표시 후 제거
        del st.session_state['sheet_load_success']
    
    if debug_mode and not saved_df.empty:
        st.markdown("#### 🐛 디버그 정보")
        st.write(f"**데이터 형태**: {saved_df.shape}")
        st.write(f"**컬럼명**: {list(saved_df.columns)}")
        st.write(f"**데이터 타입**: {saved_df.dtypes.to_dict()}")
        st.dataframe(saved_df.head(3), use_container_width=True)
    
    if not saved_df.empty:
        st.session_state['saved_keywords_df'] = saved_df
        
        # 키워드 목록을 토글로 표시
        if show_keywords:
            # 필터링 옵션 - 더 자연스럽게 스타일링
            st.markdown("""
            <div style="background: #2a2a2a; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; border: 1px solid #333333;">
                <h4 style="color: #667eea; margin: 0 0 1rem 0; font-size: 1.1rem;">🔍 필터 옵션</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                projects = ['전체'] + list(saved_df['프로젝트명'].unique())
                selected_project = st.selectbox("📁 프로젝트", projects, label_visibility="visible")
            
            with col2:
                usage_filter = st.selectbox("✅ 사용여부", ['전체', '사용함(✅)', '미사용(❌)'], label_visibility="visible")
            
            with col3:
                if st.button("📊 통계 보기", use_container_width=True):
                    total_keywords = len(saved_df)
                    used_keywords = len(saved_df[saved_df['사용여부'] == '✅'])
                    usage_rate = (used_keywords / total_keywords * 100) if total_keywords > 0 else 0
                    
                    st.info(f"📈 전체: {total_keywords}개 | ✅ 사용: {used_keywords}개 | 📊 사용률: {usage_rate:.1f}%")
            
            # 필터 적용
            filtered_df = saved_df.copy()
            
            if selected_project != '전체':
                filtered_df = filtered_df[filtered_df['프로젝트명'] == selected_project]
            
            if usage_filter == '사용함(✅)':
                filtered_df = filtered_df[filtered_df['사용여부'] == '✅']
            elif usage_filter == '미사용(❌)':
                filtered_df = filtered_df[filtered_df['사용여부'] == '❌']
            
            # 키워드 목록 표시 (간소화된 레이아웃)
            st.markdown("#### 📝 키워드 목록")
            
            if not filtered_df.empty:
                # 키워드별로 간소한 형태로 표시
                for idx, row in filtered_df.iterrows():
                    # 원본 데이터프레임에서의 실제 인덱스 찾기
                    original_idx = saved_df.index[saved_df['키워드'] == row['키워드']].tolist()[0]
                    
                    # 간소한 구분선
                    if idx > 0:
                        st.markdown('<div style="border-top: 1px solid #404040; margin: 1rem 0;"></div>', unsafe_allow_html=True)
                    
                    # 키워드 정보와 컨트롤을 한 줄에 배치
                    col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
                    
                    with col1:
                        st.markdown(f"**🔑 {row['키워드']}**")
                        st.caption(f"📁 {row['프로젝트명']} | 📅 {str(row['날짜']).split()[0] if ' ' in str(row['날짜']) else row['날짜']}")
                    
                    with col2:
                        # 사용여부 토글
                        current_status = row['사용여부'] == '✅'
                        new_status = st.checkbox(
                            "사용완료",
                            value=current_status,
                            key=f"status_check_{original_idx}"
                        )
                    
                    with col3:
                        # 메모 입력 (오른쪽으로 이동)
                        current_memo = row.get('메모', '')
                        new_memo = st.text_input(
                            "메모", 
                            value=current_memo,
                            key=f"memo_input_{original_idx}",
                            placeholder="메모를 입력하세요...",
                            label_visibility="collapsed"
                        )
                    
                    with col4:
                        # 저장 버튼
                        if st.button("💾", key=f"save_btn_{original_idx}", use_container_width=True, help="변경사항 저장"):
                            # 변경사항이 있으면 업데이트
                            if new_status != current_status or new_memo != current_memo:
                                success = update_keyword_usage(conn, original_idx, new_status, new_memo)
                                if success:
                                    st.success("✅ 업데이트 완료!")
                                    # 캐시 클리어하고 새로고침
                                    st.session_state.pop('saved_keywords_df', None)
                                    st.session_state.pop('cached_keywords_df', None)  # 새로운 캐시도 클리어
                                    # 기존 키워드 목록도 다시 로드
                                    updated_df = load_keywords_from_sheet(conn, force_refresh=True)
                                    if not updated_df.empty and '키워드' in updated_df.columns:
                                        st.session_state['existing_keywords'] = set(updated_df['키워드'].tolist())
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("❌ 업데이트 실패")
                            else:
                                st.info("변경사항이 없습니다.")
            
            # 데이터프레임으로도 표시 (접기 가능) - 제거됨, 아래로 분리
            else:
                st.info("📝 필터 조건에 맞는 키워드가 없습니다.")
        else:
            st.info(f"💡 총 {len(saved_df)}개의 키워드가 저장되어 있습니다. '📋 키워드 목록 보기'를 체크하여 확인하세요.")
        
        # 전체 데이터 테이블 (별도 섹션으로 분리)
        if show_full_table:
            add_section_divider("📊 전체 데이터 테이블")
            
            # 페이지네이션 설정
            items_per_page = 30
            total_items = len(saved_df)
            total_pages = (total_items - 1) // items_per_page + 1 if total_items > 0 else 1
            
            # 페이지 번호 초기화
            if 'current_page' not in st.session_state:
                st.session_state['current_page'] = 1
            
            # 페이지 컨트롤
            if total_pages > 1:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⬅️ 이전", disabled=st.session_state['current_page'] <= 1):
                        st.session_state['current_page'] -= 1
                        st.rerun()
                
                with col2:
                    if st.button("➡️ 다음", disabled=st.session_state['current_page'] >= total_pages):
                        st.session_state['current_page'] += 1
                        st.rerun()
                
                with col3:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem; color: #b0b0b0;">
                        페이지 {st.session_state['current_page']} / {total_pages} 
                        (총 {total_items}개 항목)
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    # 페이지 직접 이동
                    page_input = st.number_input(
                        "페이지", 
                        min_value=1, 
                        max_value=total_pages, 
                        value=st.session_state['current_page'],
                        key="page_input"
                    )
                    if page_input != st.session_state['current_page']:
                        st.session_state['current_page'] = page_input
                        st.rerun()
                
                with col5:
                    if st.button("🔄", help="새로고침"):
                        st.rerun()
            
            # 현재 페이지 데이터 계산
            start_idx = (st.session_state['current_page'] - 1) * items_per_page
            end_idx = start_idx + items_per_page
            current_page_df = saved_df.iloc[start_idx:end_idx]
            
            # 데이터프레임 표시
            if not current_page_df.empty:
                st.dataframe(
                    current_page_df,
                    use_container_width=True,
                    hide_index=False,
                    column_config={
                        '날짜': st.column_config.DatetimeColumn('날짜', width="medium"),
                        '프로젝트명': st.column_config.TextColumn('프로젝트명', width="medium"),
                        '키워드': st.column_config.TextColumn('키워드', width="large"),
                        '사용여부': st.column_config.TextColumn('사용여부', width="small"),
                        '메모': st.column_config.TextColumn('메모', width="large")
                    }
                )
                
                # 페이지 정보 하단에도 표시
                if total_pages > 1:
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: 1rem; padding: 0.5rem; 
                                background: #2a2a2a; border-radius: 8px; color: #b0b0b0;">
                        {start_idx + 1}~{min(end_idx, total_items)}번째 항목 표시 중 
                        (전체 {total_items}개 중 {len(current_page_df)}개)
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📝 해당 페이지에 표시할 데이터가 없습니다.")
        
    else:
        st.info("📝 아직 저장된 키워드가 없습니다. 키워드를 추출하고 저장해보세요!")
        
        if conn:
            st.markdown("""
            **💡 저장된 키워드가 안 보인다면:**
            - 구글시트에 데이터가 있는지 확인해보세요
            - 새로고침 버튼을 눌러보세요  
            - 구글시트의 시트 이름을 확인해보세요 (권장: "키워드관리")
            """)
        else:
            st.warning("⚠️ 구글시트 연결을 확인해주세요.")

# 푸터
add_section_divider()
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #808080;">
    <p style="font-size: 1.1rem; margin-bottom: 0.5rem; font-weight: 600;">🔍 키워드 추출 & 관리 도구</p>
    <p style="font-size: 0.9rem; margin: 0;">HTML에서 키워드를 추출하고 구글시트로 체계적으로 관리하세요!</p>
</div>
""", unsafe_allow_html=True)
