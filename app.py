import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import (
    load_and_preprocess_data, 
    create_sample_data, 
    calculate_kpis, 
    create_trend_chart, 
    create_distribution_charts, 
    detect_anomalies, 
    create_anomaly_chart,
    validate_tax_invoice_data,
    create_account_analysis,
    create_monthly_comparison,
    create_highlight_analysis,
    create_advanced_statistics,
    create_detailed_account_analysis,
    create_clean_data_analysis,
    create_clean_data_visualization,
    create_data_quality_report
)
import data_processor

# 페이지 설정
st.set_page_config(
    page_title="세금계산서 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4e79;
    }
    .highlight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0px 0px;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f4e79;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 헤더
    st.markdown('<h1 class="main-header">📊 세금계산서 분석 대시보드</h1>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 데이터 소스 선택
        data_source = st.selectbox(
            "데이터 소스 선택",
            ["샘플 데이터", "파일 업로드"]
        )
        
        # 파일 업로드
        uploaded_file = None
        if data_source == "파일 업로드":
            uploaded_file = st.file_uploader(
                "CSV 파일을 업로드하세요",
                type=['csv']
            )
        
        # 월 필터
        st.subheader("📅 월별 필터")
        month_filter = st.selectbox(
            "분석할 월 선택",
            ["전체"] + [f"2024-{i:02d}" for i in range(1, 13)]
        )
        
        # 이상치 탐지 민감도
        st.subheader("🔍 이상치 탐지 설정")
        contamination = st.slider(
            "민감도 (Contamination)",
            min_value=0.01,
            max_value=0.3,
            value=0.1,
            step=0.01,
            help="높을수록 더 많은 거래를 이상치로 탐지합니다"
        )
    
    # 데이터 로드
    df = None
    if data_source == "샘플 데이터":
        df = create_sample_data()
        st.success("✅ 샘플 데이터를 로드했습니다.")
    elif uploaded_file is not None:
        # 파일명에 따라 처리 방식 결정
        if "재무제표" in uploaded_file.name or "tasis" in uploaded_file.name.lower():
            df = data_processor.process_tasis_data(uploaded_file)
        else:
            df = load_and_preprocess_data(uploaded_file)
        
        if df is not None:
            # 데이터 유효성 검증
            if validate_tax_invoice_data(df):
                st.success("✅ 파일을 성공적으로 로드했습니다.")
            else:
                st.warning("⚠️ 데이터 형식에 문제가 있습니다. 샘플 데이터를 사용합니다.")
                df = create_sample_data()
        else:
            st.error("❌ 파일 로드에 실패했습니다. 샘플 데이터를 사용합니다.")
            df = create_sample_data()
    else:
        st.info("📁 파일을 업로드하거나 샘플 데이터를 선택해주세요.")
        return
    
    # 데이터 필터링
    if month_filter != "전체":
        df = df[df['작성월'] == month_filter]
        st.info(f"📅 {month_filter} 데이터만 분석합니다.")
    
    # KPI 계산 및 표시
    kpis = calculate_kpis(df)
    
    st.subheader("📈 주요 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 매출", f"{kpis['총_매출']:,.0f}원")
        st.metric("매출 건수", f"{kpis['매출_건수']:,}건")
    
    with col2:
        st.metric("총 매입", f"{kpis['총_매입']:,.0f}원")
        st.metric("매입 건수", f"{kpis['매입_건수']:,}건")
    
    with col3:
        st.metric("총 비용", f"{kpis['총_비용']:,.0f}원")
        st.metric("비용 건수", f"{kpis['비용_건수']:,}건")
    
    with col4:
        st.metric("총 수익", f"{kpis['총_수익']:,.0f}원")
        st.metric("수익 건수", f"{kpis['수익_건수']:,}건")
    
    # 추가 KPI
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 세액", f"{kpis['총_세액']:,.0f}원")
        st.metric("평균 세액", f"{kpis['평균_세액']:,.0f}원")
    
    with col2:
        st.metric("총 거래 건수", f"{kpis['거래_건수']:,}건")
        st.metric("전자 발행 비율", f"{kpis['전자_발행_비율']:.1f}%")
    
    with col3:
        st.metric("최대 거래", f"{kpis['최대_거래']:,.0f}원")
        st.metric("최소 거래", f"{kpis['최소_거래']:,.0f}원")
    
    with col4:
        st.metric("거래 표준편차", f"{kpis['거래_표준편차']:,.0f}원")
        net_profit = kpis['총_매출'] + kpis['총_수익'] - kpis['총_매입'] - kpis['총_비용']
        st.metric("순이익", f"{net_profit:,.0f}원")
    
    # 하이라이트 박스
    st.markdown("""
    <div class="highlight-box">
        <h3>🎯 주요 하이라이트</h3>
        <p>• 최대 거래: {:,}원 | 최소 거래: {:,}원</p>
        <p>• 거래 표준편차: {:.0f}원 | 평균 거래: {:.0f}원</p>
        <p>• 순이익: {:,}원 | 총 거래 건수: {:,}건</p>
    </div>
    """.format(
        kpis['최대_거래'], 
        kpis['최소_거래'], 
        kpis['거래_표준편차'], 
        kpis['평균_세액'],
        net_profit,
        kpis['거래_건수']
    ), unsafe_allow_html=True)
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 거래 추이 분석", 
        "🍰 유형별 분포 분석", 
        "📊 주요 계정과목 분석",
        "🔍 상세 계정과목 분석",
        "🎯 하이라이트 분석",
        "🚨 이상치 탐지",
        "✨ 데이터 품질 분석"
    ])
    
    with tab1:
        st.subheader("📈 거래 추이 분석")
        
        # 추이 차트 생성
        trend_fig = create_trend_chart(df)
        st.plotly_chart(trend_fig, use_container_width=True)
        
        # 월별 비교 차트
        monthly_fig = create_monthly_comparison(df)
        st.plotly_chart(monthly_fig, use_container_width=True)
        
        st.markdown("""
        **📊 분석 해석:**
        - 월별 공급가액과 세액의 변화 추이를 확인할 수 있습니다
        - 매출과 매입의 패턴을 비교하여 비즈니스 성과를 분석할 수 있습니다
        - 거래 건수와 금액의 상관관계를 파악할 수 있습니다
        - 급격한 변화가 있는 월은 특별히 주목해보세요
        """)
    
    with tab2:
        st.subheader("🍰 유형별 분포 분석")
        
        # 분포 차트 생성
        type_fig, form_fig = create_distribution_charts(df, month_filter)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(type_fig, use_container_width=True)
        with col2:
            st.plotly_chart(form_fig, use_container_width=True)
        
        st.markdown("""
        **📊 분석 해석:**
        - **거래유형 분포**: 매출과 매입의 비율을 확인하여 수익성을 분석할 수 있습니다
        - **발행형태 분포**: 전자와 종이 발행의 비율을 통해 디지털화 수준을 파악할 수 있습니다
        - 월별 필터를 사용하여 특정 시기의 분포를 분석할 수 있습니다
        """)
    
    with tab3:
        st.subheader("📊 주요 계정과목 분석")
        
        # 계정과목 분석 차트 생성
        amount_fig, tax_fig = create_account_analysis(df)
        
        st.plotly_chart(amount_fig, use_container_width=True)
        st.plotly_chart(tax_fig, use_container_width=True)
        
        # 고급 통계 표시
        advanced_stats = create_advanced_statistics(df)
        
        if advanced_stats:
            st.subheader("📋 상세 통계")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**거래유형별 통계**")
                st.dataframe(advanced_stats['거래유형_통계'], use_container_width=True)
            
            with col2:
                st.write("**발행형태별 통계**")
                st.dataframe(advanced_stats['발행형태_통계'], use_container_width=True)
        
        st.markdown("""
        **📊 분석 해석:**
        - **내림차순 막대그래프**: 거래유형별 공급가액과 세액을 내림차순으로 정렬하여 주요 계정과목을 한눈에 파악할 수 있습니다
        - **상세 통계**: 거래유형과 발행형태별로 합계, 평균, 건수를 확인할 수 있습니다
        - 매출과 매입의 규모 차이를 명확히 비교할 수 있습니다
        """)
    
    with tab4:
        st.subheader("🔍 상세 계정과목 분석")
        
        # 상세 계정과목 분석 차트 생성
        detailed_fig = create_detailed_account_analysis(df)
        
        if detailed_fig.data:  # 차트가 있는 경우만 표시
            st.plotly_chart(detailed_fig, use_container_width=True)
            
            # 계정과목별 상세 통계
            if '계정과목' in df.columns:
                st.subheader("📋 계정과목별 상세 통계")
                
                account_stats = df.groupby(['거래유형', '계정과목']).agg({
                    '공급가액': ['sum', 'mean', 'count'],
                    '세액': ['sum', 'mean']
                }).round(0)
                
                st.dataframe(account_stats, use_container_width=True)
        else:
            st.info("계정과목 정보가 없습니다. 샘플 데이터를 사용해보세요!")
        
        st.markdown("""
        **📊 분석 해석:**
        - **거래유형별 계정과목 분석**: 매출, 매입, 비용, 수익 각각의 세부 계정과목을 분석합니다
        - **상세 통계**: 각 계정과목별 합계, 평균, 건수를 확인할 수 있습니다
        - **내림차순 정렬**: 각 거래유형 내에서 계정과목을 금액 순으로 정렬하여 주요 항목을 파악할 수 있습니다
        """)
    
    with tab5:
        st.subheader("🎯 하이라이트 분석")
        
        # 하이라이트 분석 차트 생성
        highlight_amount_fig, highlight_tax_fig = create_highlight_analysis(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(highlight_amount_fig, use_container_width=True)
        with col2:
            st.plotly_chart(highlight_tax_fig, use_container_width=True)
        
        # 주요 거래 상세 정보
        st.subheader("💎 주요 거래 상세 정보")
        
        try:
            max_idx = df['공급가액'].idxmax()
            min_idx = df['공급가액'].idxmin()
            max_transaction = df.loc[max_idx]
            min_transaction = df.loc[min_idx]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔥 최대 거래**")
                st.write(f"공급가액: {max_transaction['공급가액']:,.0f}원")
                st.write(f"세액: {max_transaction['세액']:,.0f}원")
                st.write(f"거래유형: {max_transaction['거래유형']}")
                st.write(f"발행형태: {max_transaction['발행형태']}")
                st.write(f"작성월: {max_transaction['작성월']}")
            
            with col2:
                st.markdown("**💎 최소 거래**")
                st.write(f"공급가액: {min_transaction['공급가액']:,.0f}원")
                st.write(f"세액: {min_transaction['세액']:,.0f}원")
                st.write(f"거래유형: {min_transaction['거래유형']}")
                st.write(f"발행형태: {min_transaction['발행형태']}")
                st.write(f"작성월: {min_transaction['작성월']}")
                
        except Exception as e:
            st.error(f"주요 거래 정보 표시 중 오류: {str(e)}")
        
        st.markdown("""
        **📊 분석 해석:**
        - **하이라이트 기능**: 최대/최소 거래와 평균 이상 거래를 강조하여 주요 거래를 쉽게 파악할 수 있습니다
        - **동작 기능**: 차트에 마우스를 올리면 상세 정보를 확인할 수 있습니다
        - **주요 거래 상세 정보**: 최대/최소 거래의 모든 정보를 표로 확인할 수 있습니다
        """)
    
    with tab6:
        st.subheader("🚨 이상치 탐지")
        
        # 이상치 탐지
        df_with_anomalies = detect_anomalies(df, contamination)
        
        # 이상치 통계
        anomaly_count = len(df_with_anomalies[df_with_anomalies['이상치'] == -1])
        total_count = len(df_with_anomalies)
        anomaly_ratio = (anomaly_count / total_count) * 100 if total_count > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("이상치 건수", f"{anomaly_count:,}건")
        with col2:
            st.metric("이상치 비율", f"{anomaly_ratio:.1f}%")
        with col3:
            st.metric("정상 거래", f"{total_count - anomaly_count:,}건")
        
        # 이상치 시각화
        anomaly_fig = create_anomaly_chart(df_with_anomalies)
        st.plotly_chart(anomaly_fig, use_container_width=True)
        
        # 이상치 상세 정보
        if anomaly_count > 0:
            st.subheader("🚨 이상치 상세 정보")
            anomaly_data = df_with_anomalies[df_with_anomalies['이상치'] == -1]
            st.dataframe(
                anomaly_data[['작성월', '거래유형', '발행형태', '공급가액', '세액']].sort_values('공급가액', ascending=False),
                use_container_width=True
            )
        
        st.markdown("""
        **📊 분석 해석:**
        - **이상치**: 일반적인 패턴과 다른 거래를 의미합니다
        - **높은 공급가액/세액**: 대규모 거래나 특별한 거래일 수 있습니다
        - **낮은 공급가액/세액**: 소규모 거래나 오타일 수 있습니다
        - 민감도 슬라이더를 조정하여 이상치 탐지 기준을 변경할 수 있습니다
        """)
    
    with tab7:
        st.subheader("✨ 데이터 품질 분석")
        
        # 데이터 품질 분석
        clean_stats, clean_summary, clean_detailed_stats = create_clean_data_analysis(df)
        
        if clean_stats:
            # 데이터 품질 KPI
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "원본 데이터", 
                    f"{clean_stats['원본_데이터_수']:,}건",
                    help="전체 데이터 수"
                )
            
            with col2:
                st.metric(
                    "깨끗한 데이터", 
                    f"{clean_stats['깨끗한_데이터_수']:,}건",
                    f"{clean_stats['깨끗한_데이터_수'] - clean_stats['원본_데이터_수']:,}건",
                    help="이상치와 결측치를 제거한 데이터"
                )
            
            with col3:
                st.metric(
                    "데이터 품질", 
                    f"{clean_stats['데이터_품질_비율']:.1f}%",
                    help="깨끗한 데이터 비율"
                )
            
            with col4:
                st.metric(
                    "제거된 데이터", 
                    f"{clean_stats['제거된_데이터_수']:,}건",
                    help="이상치와 결측치로 제거된 데이터"
                )
            
            # 데이터 품질 시각화
            quality_fig, distribution_fig = create_clean_data_visualization(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(quality_fig, use_container_width=True)
            with col2:
                st.plotly_chart(distribution_fig, use_container_width=True)
            
            # 깨끗한 데이터 통계
            if clean_summary is not None:
                st.subheader("📋 깨끗한 데이터 요약 통계")
                st.dataframe(clean_summary, use_container_width=True)
                
                # 상세 통계
                if clean_detailed_stats:
                    st.subheader("📊 깨끗한 데이터 상세 통계")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**거래유형별 깨끗한 통계**")
                        st.dataframe(clean_detailed_stats['거래유형_통계'], use_container_width=True)
                    
                    with col2:
                        st.write("**발행형태별 깨끗한 통계**")
                        st.dataframe(clean_detailed_stats['발행형태_통계'], use_container_width=True)
                    
                    st.write("**월별 깨끗한 통계**")
                    st.dataframe(clean_detailed_stats['월별_통계'], use_container_width=True)
            
            # 데이터 품질 리포트
            st.subheader("📄 데이터 품질 리포트")
            quality_report = create_data_quality_report(df)
            st.markdown(quality_report)
            
        else:
            st.warning("데이터 품질 분석을 수행할 수 없습니다.")
        
        st.markdown("""
        **📊 분석 해석:**
        - **데이터 품질**: 이상치와 결측치를 제거한 깨끗한 데이터의 비율을 확인합니다
        - **결측치 분석**: 각 컬럼별 결측치 현황을 파악하여 데이터 완성도를 평가합니다
        - **이상치 분석**: IQR 방법을 사용하여 공급가액과 세액의 이상치를 탐지합니다
        - **깨끗한 데이터 통계**: 이상치와 결측치를 제거한 후의 신뢰할 수 있는 통계를 제공합니다
        - **데이터 품질 리포트**: 전체적인 데이터 품질 현황을 종합적으로 분석합니다
        """)

if __name__ == "__main__":
    main() 