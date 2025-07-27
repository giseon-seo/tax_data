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
    create_advanced_anomaly_analysis,
    create_anomaly_correlation_analysis,
    calculate_anomaly_risk_score,
    generate_anomaly_insights,
    validate_tax_invoice_data
)
from data_processor import process_tasis_data

# 페이지 설정
st.set_page_config(
    page_title="세금계산서 분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Arial', sans-serif;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .kpi-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        font-weight: 500;
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
    st.markdown("---")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 데이터 소스 선택
        data_source = st.radio(
            "데이터 소스 선택",
            ["샘플 데이터", "CSV 파일 업로드"],
            help="분석할 데이터를 선택하세요"
        )
        
        # 파일 업로드
        if data_source == "CSV 파일 업로드":
            uploaded_file = st.file_uploader(
                "CSV 파일을 업로드하세요",
                type=['csv'],
                help="작성월, 거래유형, 발행형태, 공급가액, 세액 컬럼이 포함된 CSV 파일"
            )
            
            if uploaded_file is not None:
                # 파일 타입 확인
                file_name = uploaded_file.name
                if "재무제표" in file_name or "tasis" in file_name.lower():
                    st.info("TASIS 재무제표 데이터를 감지했습니다. 데이터를 변환 중...")
                    df = process_tasis_data(uploaded_file)
                else:
                    df = load_and_preprocess_data(uploaded_file)
                    
                if df is not None:
                    # 데이터 유효성 검증
                    if validate_tax_invoice_data(df):
                        st.success("데이터가 성공적으로 로드되었습니다!")
                    else:
                        st.warning("데이터 형식에 문제가 있습니다. 샘플 데이터를 사용합니다.")
                        df = create_sample_data()
            else:
                st.info("파일을 업로드하거나 샘플 데이터를 선택하세요.")
                df = None
        else:
            df = create_sample_data()
            st.success("샘플 데이터가 로드되었습니다.")
        
        # 필터 설정
        if df is not None:
            st.header("🔍 필터")
            
            # 월 선택
            available_months = ["전체"] + sorted(df['작성월'].unique().tolist())
            selected_month = st.selectbox(
                "분석 월 선택",
                available_months,
                help="특정 월의 데이터만 분석하려면 선택하세요"
            )
            
            # 이상치 탐지 민감도
            st.header("🎯 이상치 탐지")
            contamination = st.slider(
                "이상치 탐지 민감도",
                min_value=0.01,
                max_value=0.3,
                value=0.1,
                step=0.01,
                help="높을수록 더 많은 데이터를 이상치로 탐지합니다"
            )
    
    # 메인 콘텐츠
    if df is not None:
        # KPI 카드
        kpis = calculate_kpis(df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{kpis['거래_건수']:,}건</div>
                <div class="kpi-label">총 거래 건수</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{kpis['총_매출']:,}원</div>
                <div class="kpi-label">총 매출</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{kpis['총_매입']:,}원</div>
                <div class="kpi-label">총 매입</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{kpis['평균_세액']:,.0f}원</div>
                <div class="kpi-label">평균 세액</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 탭 구성
        tab1, tab2, tab3 = st.tabs(["📈 거래 추이 분석", "🥧 유형별 분포 분석", "🔍 이상치 탐지"])
        
        with tab1:
            st.header("📈 거래 추이 분석")
            st.write("월별 공급가액과 세액의 변화 추이를 분석합니다.")
            
            # 추이 차트
            trend_fig = create_trend_chart(df)
            st.plotly_chart(trend_fig, use_container_width=True)
            
            # 해석 텍스트
            st.markdown("""
            **📊 분석 해석:**
            - 위 차트는 월별 매출과 매입의 공급가액 및 세액 추이를 보여줍니다
            - 매출과 매입의 패턴을 비교하여 비즈니스 성과를 평가할 수 있습니다
            - 계절성이나 특정 시점의 급증/감소를 파악할 수 있습니다
            """)
        
        with tab2:
            st.header("🥧 유형별 분포 분석")
            st.write("거래유형과 발행형태별 분포를 분석합니다.")
            
            # 분포 차트
            col1, col2 = st.columns(2)
            
            with col1:
                type_fig, form_fig = create_distribution_charts(df, selected_month)
                st.plotly_chart(type_fig, use_container_width=True)
            
            with col2:
                st.plotly_chart(form_fig, use_container_width=True)
            
            # 해석 텍스트
            st.markdown("""
            **📊 분석 해석:**
            - **거래유형 분포**: 매출과 매입의 비율을 통해 비즈니스 구조를 파악할 수 있습니다
            - **발행형태 분포**: 전자세금계산서 사용 비율을 통해 디지털화 수준을 평가할 수 있습니다
            - 높은 전자 발행 비율은 세무 처리의 효율성을 나타냅니다
            """)
        
        with tab3:
            st.header("🔍 이상치 탐지 및 심화 분석")
            st.write("공급가액과 세액 기준으로 이상치를 탐지하고 심화 분석을 제공합니다.")
            
            # 이상치 탐지
            df_with_anomalies, anomaly_labels = detect_anomalies(df, contamination)
            
            # 기본 이상치 차트
            anomaly_fig = create_anomaly_chart(df_with_anomalies)
            st.plotly_chart(anomaly_fig, use_container_width=True)
            
            # 이상치 통계
            anomaly_count = df_with_anomalies['이상치'].sum()
            total_count = len(df_with_anomalies)
            anomaly_rate = (anomaly_count / total_count) * 100
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("이상치 건수", f"{anomaly_count:,}건")
            
            with col2:
                st.metric("이상치 비율", f"{anomaly_rate:.1f}%")
            
            with col3:
                st.metric("정상 거래", f"{total_count - anomaly_count:,}건")
            
            # 심화 분석
            if anomaly_count > 0:
                st.markdown("---")
                st.subheader("📊 심화 분석")
                
                # 심화 분석 데이터 생성
                anomaly_stats, normal_stats, fig_type_dist, fig_month_dist = create_advanced_anomaly_analysis(df_with_anomalies)
                
                # 통계 정보 표시
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📈 이상치 통계")
                    if anomaly_stats:
                        st.metric("평균 공급가액", f"{anomaly_stats['이상치_평균_공급가액']:,.0f}원")
                        st.metric("평균 세액", f"{anomaly_stats['이상치_평균_세액']:,.0f}원")
                        st.metric("최대 공급가액", f"{anomaly_stats['이상치_최대_공급가액']:,.0f}원")
                        st.metric("공급가액 표준편차", f"{anomaly_stats['이상치_공급가액_표준편차']:,.0f}원")
                
                with col2:
                    st.subheader("📊 정상 거래 통계")
                    if normal_stats:
                        st.metric("평균 공급가액", f"{normal_stats['정상_평균_공급가액']:,.0f}원")
                        st.metric("평균 세액", f"{normal_stats['정상_평균_세액']:,.0f}원")
                        st.metric("공급가액 표준편차", f"{normal_stats['정상_공급가액_표준편차']:,.0f}원")
                        st.metric("세액 표준편차", f"{normal_stats['정상_세액_표준편차']:,.0f}원")
                
                # 차트 표시
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(fig_type_dist, use_container_width=True)
                
                with col2:
                    st.plotly_chart(fig_month_dist, use_container_width=True)
                
                # 상관관계 분석
                st.subheader("📊 상관관계 분석")
                correlation_fig = create_anomaly_correlation_analysis(df_with_anomalies)
                st.plotly_chart(correlation_fig, use_container_width=True)
                
                # 위험도 점수 계산
                risk_score, risk_level = calculate_anomaly_risk_score(df_with_anomalies)
                
                # 위험도 표시
                st.subheader("⚠️ 이상치 위험도 평가")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("위험도 점수", f"{risk_score:.1f}/100")
                
                with col2:
                    if risk_level == "낮음":
                        st.success(f"위험도 등급: {risk_level}")
                    elif risk_level == "보통":
                        st.warning(f"위험도 등급: {risk_level}")
                    elif risk_level == "높음":
                        st.error(f"위험도 등급: {risk_level}")
                    else:
                        st.error(f"위험도 등급: {risk_level}")
                
                with col3:
                    if risk_score > 60:
                        st.error("🔴 높은 위험도 - 즉시 검토 필요")
                    elif risk_score > 30:
                        st.warning("🟡 보통 위험도 - 주기적 모니터링 권장")
                    else:
                        st.success("🟢 낮은 위험도 - 정상 상태")
                
                # 인사이트 생성
                insights = generate_anomaly_insights(df_with_anomalies, contamination)
                
                if insights:
                    st.subheader("💡 분석 인사이트")
                    for insight in insights:
                        st.info(insight)
                
                # 이상치 상세 정보
                st.subheader("🚨 이상치 상세 정보")
                anomaly_data = df_with_anomalies[df_with_anomalies['이상치']].copy()
                anomaly_data = anomaly_data[['작성월', '거래유형', '발행형태', '공급가액', '세액']]
                anomaly_data['공급가액'] = anomaly_data['공급가액'].apply(lambda x: f"{x:,}원")
                anomaly_data['세액'] = anomaly_data['세액'].apply(lambda x: f"{x:,}원")
                st.dataframe(anomaly_data, use_container_width=True)
            
            # 해석 텍스트
            st.markdown("""
            **📊 심화 분석 해석:**
            
            **이상치 탐지 원리:**
            - Isolation Forest 알고리즘을 사용하여 공급가액과 세액의 패턴을 분석
            - 일반적인 거래 패턴과 크게 벗어난 거래를 이상치로 탐지
            
            **분석 지표:**
            - **이상치 비율**: 전체 거래 중 이상치로 탐지된 비율
            - **평균 공급가액/세액**: 이상치와 정상 거래의 평균값 비교
            - **표준편차**: 데이터의 분산 정도를 나타내는 지표
            - **위험도 점수**: 이상치의 심각성을 종합적으로 평가한 점수 (0-100)
            
            **상관관계 분석:**
            - **산점도**: 공급가액과 세액의 관계를 시각적으로 분석
            - **분포 비교**: 정상 거래와 이상치의 분포 차이를 히스토그램으로 비교
            - **패턴 분석**: 이상치가 특정 패턴을 보이는지 분석
            
            **실무 활용:**
            - 높은 위험도 점수: 즉시 검토가 필요한 상황
            - 특정 월의 이상치 집중: 해당 시기의 특별한 거래 패턴 분석
            - 거래유형별 이상치 분포: 매출/매입 거래의 특성 차이 분석
            - 상관관계 분석: 이상치의 특성을 더 정확히 파악
            """)
    
    else:
        st.info("데이터를 로드해주세요.")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        📊 세금계산서 분석 대시보드 | 회계 데이터 시각화 포트폴리오
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 