# 구글시트 연결하고 저장된 키워드 수 실시간 확인
conn = get_google_sheet_connection()
if conn:
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
