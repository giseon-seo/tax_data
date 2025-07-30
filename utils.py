import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

def load_and_preprocess_data(uploaded_file):
    """
    업로드된 파일을 로드하고 전처리
    """
    if uploaded_file is None:
        return create_sample_data()
    
    try:
        # 파일 내용을 바이트로 읽기
        content = uploaded_file.read()
        uploaded_file.seek(0)  # 파일 포인터를 처음으로 되돌리기
        
        # 다양한 인코딩 시도
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1', 'iso-8859-1', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                # 바이트를 문자열로 디코딩
                text_content = content.decode(encoding)
                
                # StringIO를 사용하여 pandas로 읽기
                import io
                df = pd.read_csv(io.StringIO(text_content), encoding=encoding)
                
                # 성공하면 루프 탈출
                break
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        else:
            # 모든 인코딩이 실패한 경우
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, engine='python')
        
        # 데이터 전처리
        if '공급가액' in df.columns and '세액' in df.columns:
            # 숫자 컬럼 변환
            df['공급가액'] = pd.to_numeric(df['공급가액'], errors='coerce')
            df['세액'] = pd.to_numeric(df['세액'], errors='coerce')
            
            # 결측치 제거
            df = df.dropna(subset=['공급가액', '세액'])
            
            return df
        else:
            st.error("필수 컬럼이 누락되었습니다: ['공급가액', '세액']")
            return create_sample_data()
            
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {str(e)}")
        return create_sample_data()

def create_sample_data():
    """
    샘플 데이터 생성
    """
    np.random.seed(42)
    
    # 날짜 범위 생성
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    
    # 거래유형과 발행형태
    transaction_types = ['매출', '매입', '비용', '수익']
    issuance_types = ['전자', '종이']
    
    # 계정과목 (거래유형별)
    account_categories = {
        '매출': ['상품매출', '서비스매출', '임대수익', '이자수익', '배당수익'],
        '매입': ['상품매입', '서비스매입', '임대료', '이자비용', '수수료'],
        '비용': ['인건비', '관리비', '광고선전비', '여비', '도서구입비'],
        '수익': ['이자수익', '배당수익', '임대수익', '기타수익', '환차익']
    }
    
    data = []
    
    for _ in range(1000):
        date = np.random.choice(dates)
        transaction_type = np.random.choice(transaction_types)
        issuance_type = np.random.choice(issuance_types)
        
        # 거래유형에 따른 계정과목 선택
        if transaction_type in account_categories:
            account = np.random.choice(account_categories[transaction_type])
        else:
            account = '기타'
        
        # 공급가액 생성 (거래유형별로 다른 범위)
        if transaction_type == '매출':
            supply_amount = np.random.randint(100000, 5000000)
        elif transaction_type == '매입':
            supply_amount = np.random.randint(50000, 3000000)
        elif transaction_type == '비용':
            supply_amount = np.random.randint(10000, 1000000)
        else:  # 수익
            supply_amount = np.random.randint(50000, 2000000)
        
        # 세액 계산 (10%)
        tax_amount = int(supply_amount * 0.1)
        
        data.append({
            '작성월': date.strftime('%Y-%m'),
            '거래유형': transaction_type,
            '발행형태': issuance_type,
            '공급가액': supply_amount,
            '세액': tax_amount,
            '계정과목': account
        })
    
    return pd.DataFrame(data)

def validate_tax_invoice_data(df):
    """
    세금계산서 데이터 유효성 검사
    """
    required_columns = ['작성월', '거래유형', '발행형태', '공급가액', '세액']
    
    # 필수 컬럼 확인
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"필수 컬럼이 누락되었습니다: {missing_columns}")
        return False
    
    # 거래유형 유효성 확인
    valid_types = ['매출', '매입', '비용', '수익']
    invalid_types = df[~df['거래유형'].isin(valid_types)]['거래유형'].unique()
    if len(invalid_types) > 0:
        st.warning(f"유효하지 않은 거래유형이 있습니다: {invalid_types}")
    
    # 발행형태 유효성 확인
    valid_forms = ['전자', '종이']
    invalid_forms = df[~df['발행형태'].isin(valid_forms)]['발행형태'].unique()
    if len(invalid_forms) > 0:
        st.warning(f"유효하지 않은 발행형태가 있습니다: {invalid_forms}")
    
    # 숫자 컬럼 확인
    try:
        df['공급가액'] = pd.to_numeric(df['공급가액'], errors='coerce')
        df['세액'] = pd.to_numeric(df['세액'], errors='coerce')
    except Exception as e:
        st.error(f"숫자 컬럼 변환 중 오류: {str(e)}")
        return False
    
    return True

def calculate_kpis(df):
    """
    주요 KPI 계산
    """
    if df is None or df.empty:
        return {}
    
    kpis = {
        '총_매출': df[df['거래유형'] == '매출']['공급가액'].sum(),
        '총_매입': df[df['거래유형'] == '매입']['공급가액'].sum(),
        '총_비용': df[df['거래유형'] == '비용']['공급가액'].sum(),
        '총_수익': df[df['거래유형'] == '수익']['공급가액'].sum(),
        '매출_건수': len(df[df['거래유형'] == '매출']),
        '매입_건수': len(df[df['거래유형'] == '매입']),
        '비용_건수': len(df[df['거래유형'] == '비용']),
        '수익_건수': len(df[df['거래유형'] == '수익']),
        '전자_발행_비율': (len(df[df['발행형태'] == '전자']) / len(df)) * 100,
        '최대_거래': df['공급가액'].max(),
        '최소_거래': df['공급가액'].min(),
        '거래_표준편차': df['공급가액'].std()
    }
    
    return kpis

def create_trend_chart(df):
    """
    거래 추이 분석 차트 생성
    """
    if df is None or df.empty:
        return go.Figure()
    
    # 월별 데이터 집계 (거래건수 포함)
    monthly_data = df.groupby(['작성월', '거래유형']).agg({
        '공급가액': 'sum',
        '세액': 'sum'
    }).reset_index()
    
    # 거래 건수 계산 (별도로 계산하여 병합)
    transaction_counts = df.groupby(['작성월', '거래유형']).size().reset_index()
    transaction_counts.columns = ['작성월', '거래유형', '거래건수']
    monthly_data = monthly_data.merge(transaction_counts, on=['작성월', '거래유형'])
    
    # 매출/매입 분리
    sales_data = monthly_data[monthly_data['거래유형'] == '매출']
    purchase_data = monthly_data[monthly_data['거래유형'] == '매입']
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('월별 공급가액 추이', '월별 세액 추이', '월별 거래 건수'),
        vertical_spacing=0.08,
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]]
    )
    
    # 공급가액 차트
    fig.add_trace(
        go.Scatter(
            x=sales_data['작성월'],
            y=sales_data['공급가액'],
            name='매출',
            line=dict(color='#1f77b4', width=3),
            mode='lines+markers'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=purchase_data['작성월'],
            y=purchase_data['공급가액'],
            name='매입',
            line=dict(color='#ff7f0e', width=3),
            mode='lines+markers'
        ),
        row=1, col=1
    )
    
    # 세액 차트
    fig.add_trace(
        go.Scatter(
            x=sales_data['작성월'],
            y=sales_data['세액'],
            name='매출 세액',
            line=dict(color='#1f77b4', width=3),
            mode='lines+markers',
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=purchase_data['작성월'],
            y=purchase_data['세액'],
            name='매입 세액',
            line=dict(color='#ff7f0e', width=3),
            mode='lines+markers',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 거래 건수 차트
    fig.add_trace(
        go.Bar(
            x=sales_data['작성월'],
            y=sales_data['거래건수'],
            name='매출 건수',
            marker_color='#1f77b4',
            opacity=0.7
        ),
        row=3, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=purchase_data['작성월'],
            y=purchase_data['거래건수'],
            name='매입 건수',
            marker_color='#ff7f0e',
            opacity=0.7
        ),
        row=3, col=1
    )
    
    fig.update_layout(
        title_text="거래 추이 분석",
        title_x=0.5,
        height=700,
        template="plotly_white",
        showlegend=True
    )
    
    # x축 라벨 회전
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_distribution_charts(df, selected_month=None):
    """
    유형별 분포 차트 생성
    """
    if df is None or df.empty:
        return go.Figure(), go.Figure()
    
    # 월별 필터 적용
    if selected_month and selected_month != "전체":
        df_filtered = df[df['작성월'] == selected_month]
    else:
        df_filtered = df
    
    # 거래유형 분포
    type_counts = df_filtered['거래유형'].value_counts()
    fig_type = go.Figure(data=[go.Pie(
        labels=type_counts.index,
        values=type_counts.values,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig_type.update_layout(
        title_text="거래유형별 분포",
        title_x=0.5,
        height=400,
        template="plotly_white"
    )
    
    # 발행형태 분포
    form_counts = df_filtered['발행형태'].value_counts()
    fig_form = go.Figure(data=[go.Pie(
        labels=form_counts.index,
        values=form_counts.values,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig_form.update_layout(
        title_text="발행형태별 분포",
        title_x=0.5,
        height=400,
        template="plotly_white"
    )
    
    return fig_type, fig_form

def create_account_analysis(df):
    """
    주요 계정과목 분석 차트 생성
    """
    if df is None or df.empty:
        return go.Figure(), go.Figure()
    
    if '계정과목' not in df.columns:
        return go.Figure(), go.Figure()
    
    # 계정과목별 공급가액 합계 (내림차순 TOP 10)
    account_amount = df.groupby('계정과목')['공급가액'].sum().sort_values(ascending=False).head(10)
    
    fig_amount = go.Figure(data=[
        go.Bar(
            x=account_amount.index,
            y=account_amount.values,
            text=[f"{val:,.0f}원" for val in account_amount.values],
            textposition='auto',
            marker_color=px.colors.qualitative.Set3
        )
    ])
    
    fig_amount.update_layout(
        title_text="주요 계정과목별 공급가액 (내림차순 TOP 10)",
        title_x=0.5,
        xaxis_title="계정과목",
        yaxis_title="공급가액 (원)",
        height=500,
        template="plotly_white"
    )
    
    # 계정과목별 세액 합계 (내림차순 TOP 10)
    account_tax = df.groupby('계정과목')['세액'].sum().sort_values(ascending=False).head(10)
    
    fig_tax = go.Figure(data=[
        go.Bar(
            x=account_tax.index,
            y=account_tax.values,
            text=[f"{val:,.0f}원" for val in account_tax.values],
            textposition='auto',
            marker_color=px.colors.qualitative.Pastel
        )
    ])
    
    fig_tax.update_layout(
        title_text="주요 계정과목별 세액 (내림차순 TOP 10)",
        title_x=0.5,
        xaxis_title="계정과목",
        yaxis_title="세액 (원)",
        height=500,
        template="plotly_white"
    )
    
    return fig_amount, fig_tax

def create_detailed_account_analysis(df):
    """
    상세 계정과목 분석
    """
    if df is None or df.empty:
        return go.Figure()
    
    if '계정과목' not in df.columns:
        return go.Figure()
    
    # 거래유형별 계정과목 분석
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('매출 계정과목', '매입 계정과목', '비용 계정과목', '수익 계정과목'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 매출 계정과목
    sales_accounts = df[df['거래유형'] == '매출'].groupby('계정과목')['공급가액'].sum().sort_values(ascending=False)
    if not sales_accounts.empty:
        fig.add_trace(
            go.Bar(
                x=sales_accounts.index,
                y=sales_accounts.values,
                name='매출',
                marker_color='#1f77b4'
            ),
            row=1, col=1
        )
    
    # 매입 계정과목
    purchase_accounts = df[df['거래유형'] == '매입'].groupby('계정과목')['공급가액'].sum().sort_values(ascending=False)
    if not purchase_accounts.empty:
        fig.add_trace(
            go.Bar(
                x=purchase_accounts.index,
                y=purchase_accounts.values,
                name='매입',
                marker_color='#ff7f0e'
            ),
            row=1, col=2
        )
    
    # 비용 계정과목
    expense_accounts = df[df['거래유형'] == '비용'].groupby('계정과목')['공급가액'].sum().sort_values(ascending=False)
    if not expense_accounts.empty:
        fig.add_trace(
            go.Bar(
                x=expense_accounts.index,
                y=expense_accounts.values,
                name='비용',
                marker_color='#2ca02c'
            ),
            row=2, col=1
        )
    
    # 수익 계정과목
    income_accounts = df[df['거래유형'] == '수익'].groupby('계정과목')['공급가액'].sum().sort_values(ascending=False)
    if not income_accounts.empty:
        fig.add_trace(
            go.Bar(
                x=income_accounts.index,
                y=income_accounts.values,
                name='수익',
                marker_color='#d62728'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=600,
        title_text="거래유형별 계정과목 상세 분석",
        title_x=0.5,
        template="plotly_white",
        showlegend=False
    )
    
    # x축 라벨 회전
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=10)
    
    return fig

def create_monthly_comparison(df):
    """
    월별 비교 분석 차트
    """
    if df is None or df.empty:
        return go.Figure()
    
    # 월별 매출/매입 비교
    monthly_comparison = df.groupby(['작성월', '거래유형']).agg({
        '공급가액': 'sum',
        '세액': 'sum'
    }).reset_index()
    
    # 피벗 테이블 생성 (안전하게 처리)
    try:
        pivot_data = monthly_comparison.pivot(index='작성월', columns='거래유형', values='공급가액').fillna(0)
    except Exception as e:
        st.error(f"피벗 테이블 생성 중 오류: {str(e)}")
        return go.Figure()
    
    fig = go.Figure()
    
    # 매출 데이터
    if '매출' in pivot_data.columns:
        fig.add_trace(go.Bar(
            x=pivot_data.index,
            y=pivot_data['매출'],
            name='매출',
            marker_color='#1f77b4',
            text=[f"{val:,.0f}원" for val in pivot_data['매출']],
            textposition='auto'
        ))
    
    # 매입 데이터
    if '매입' in pivot_data.columns:
        fig.add_trace(go.Bar(
            x=pivot_data.index,
            y=pivot_data['매입'],
            name='매입',
            marker_color='#ff7f0e',
            text=[f"{val:,.0f}원" for val in pivot_data['매입']],
            textposition='auto'
        ))
    
    # 비용 데이터
    if '비용' in pivot_data.columns:
        fig.add_trace(go.Bar(
            x=pivot_data.index,
            y=pivot_data['비용'],
            name='비용',
            marker_color='#2ca02c',
            text=[f"{val:,.0f}원" for val in pivot_data['비용']],
            textposition='auto'
        ))
    
    # 수익 데이터
    if '수익' in pivot_data.columns:
        fig.add_trace(go.Bar(
            x=pivot_data.index,
            y=pivot_data['수익'],
            name='수익',
            marker_color='#d62728',
            text=[f"{val:,.0f}원" for val in pivot_data['수익']],
            textposition='auto'
        ))
    
    fig.update_layout(
        title_text="월별 거래유형별 비교",
        title_x=0.5,
        xaxis_title="작성월",
        yaxis_title="공급가액 (원)",
        barmode='group',
        height=500,
        template="plotly_white"
    )
    
    return fig

def create_highlight_analysis(df):
    """
    하이라이트 분석 차트
    """
    if df is None or df.empty:
        return go.Figure(), go.Figure()
    
    try:
        # 최대 거래 하이라이트
        max_idx = df['공급가액'].idxmax()
        max_transaction = df.loc[max_idx]
        
        # 최소 거래 하이라이트
        min_idx = df['공급가액'].idxmin()
        min_transaction = df.loc[min_idx]
        
        # 평균 이상 거래 하이라이트
        avg_amount = df['공급가액'].mean()
        above_avg = df[df['공급가액'] > avg_amount]
        
        # 하이라이트 데이터
        highlight_data = pd.DataFrame({
            '구분': ['최대 거래', '최소 거래', '평균 이상 거래'],
            '공급가액': [max_transaction['공급가액'], min_transaction['공급가액'], above_avg['공급가액'].mean()],
            '세액': [max_transaction['세액'], min_transaction['세액'], above_avg['세액'].mean()],
            '거래유형': [max_transaction['거래유형'], min_transaction['거래유형'], '평균'],
            '발행형태': [max_transaction['발행형태'], min_transaction['발행형태'], '평균']
        })
        
        # 공급가액 하이라이트 차트
        fig_amount = go.Figure(data=[
            go.Bar(
                x=highlight_data['구분'],
                y=highlight_data['공급가액'],
                text=[f"{val:,.0f}원" for val in highlight_data['공급가액']],
                textposition='auto',
                marker_color=['#ff4444', '#44ff44', '#4444ff'],
                name='공급가액'
            )
        ])
        
        fig_amount.update_layout(
            title_text="주요 거래 하이라이트 (공급가액)",
            title_x=0.5,
            xaxis_title="구분",
            yaxis_title="공급가액 (원)",
            height=400,
            template="plotly_white"
        )
        
        # 세액 하이라이트 차트
        fig_tax = go.Figure(data=[
            go.Bar(
                x=highlight_data['구분'],
                y=highlight_data['세액'],
                text=[f"{val:,.0f}원" for val in highlight_data['세액']],
                textposition='auto',
                marker_color=['#ff6666', '#66ff66', '#6666ff'],
                name='세액'
            )
        ])
        
        fig_tax.update_layout(
            title_text="주요 거래 하이라이트 (세액)",
            title_x=0.5,
            xaxis_title="구분",
            yaxis_title="세액 (원)",
            height=400,
            template="plotly_white"
        )
        
        return fig_amount, fig_tax
        
    except Exception as e:
        st.error(f"하이라이트 분석 중 오류: {str(e)}")
        return go.Figure(), go.Figure()

def detect_anomalies(df, contamination=0.1):
    """
    이상치 탐지
    """
    if df is None or df.empty:
        return df
    
    # 이상치 탐지를 위한 특성 선택
    features = df[['공급가액', '세액']].copy()
    
    # Isolation Forest 모델
    iso_forest = IsolationForest(contamination=contamination, random_state=42)
    anomalies = iso_forest.fit_predict(features)
    
    # 결과를 데이터프레임에 추가
    df_with_anomalies = df.copy()
    df_with_anomalies['이상치'] = anomalies
    
    return df_with_anomalies

def create_anomaly_chart(df_with_anomalies):
    """
    이상치 시각화 차트
    """
    if df_with_anomalies is None or df_with_anomalies.empty:
        return go.Figure()
    
    # 정상 데이터와 이상치 분리
    normal_data = df_with_anomalies[df_with_anomalies['이상치'] == 1]
    anomaly_data = df_with_anomalies[df_with_anomalies['이상치'] == -1]
    
    fig = go.Figure()
    
    # 정상 데이터
    fig.add_trace(go.Scatter(
        x=normal_data['공급가액'],
        y=normal_data['세액'],
        mode='markers',
        name='정상',
        marker=dict(color='blue', size=8, opacity=0.6)
    ))
    
    # 이상치
    if len(anomaly_data) > 0:
        fig.add_trace(go.Scatter(
            x=anomaly_data['공급가액'],
            y=anomaly_data['세액'],
            mode='markers',
            name='이상치',
            marker=dict(color='red', size=12, symbol='x')
        ))
    
    fig.update_layout(
        title_text="이상치 탐지 결과",
        title_x=0.5,
        xaxis_title="공급가액 (원)",
        yaxis_title="세액 (원)",
        height=500,
        template="plotly_white"
    )
    
    return fig

def create_advanced_statistics(df):
    """
    고급 통계 생성
    """
    if df is None or df.empty:
        return None
    
    # 거래유형별 통계
    type_stats = df.groupby('거래유형').agg({
        '공급가액': ['count', 'sum', 'mean', 'std', 'min', 'max'],
        '세액': ['sum', 'mean', 'std', 'min', 'max']
    }).round(0)
    
    # 발행형태별 통계
    form_stats = df.groupby('발행형태').agg({
        '공급가액': ['count', 'sum', 'mean', 'std'],
        '세액': ['sum', 'mean', 'std']
    }).round(0)
    
    return {
        '거래유형_통계': type_stats,
        '발행형태_통계': form_stats
    }

def create_clean_data_analysis(df):
    """
    이상치와 결측치를 제외한 깨끗한 데이터 분석
    """
    if df is None or df.empty:
        return None, None, None
    
    # 결측치 확인
    missing_data = df.isnull().sum()
    missing_percentage = (missing_data / len(df)) * 100
    
    # 이상치 탐지 (IQR 방법)
    def detect_outliers_iqr(series):
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return (series < lower_bound) | (series > upper_bound)
    
    # 공급가액과 세액의 이상치 탐지
    supply_outliers = detect_outliers_iqr(df['공급가액'])
    tax_outliers = detect_outliers_iqr(df['세액'])
    
    # 결측치나 이상치가 있는 행 제거
    clean_df = df.copy()
    clean_df = clean_df.dropna()  # 결측치 제거
    clean_df = clean_df[~supply_outliers]  # 공급가액 이상치 제거
    clean_df = clean_df[~tax_outliers]  # 세액 이상치 제거
    
    # 깨끗한 데이터 통계
    clean_stats = {
        '원본_데이터_수': len(df),
        '깨끗한_데이터_수': len(clean_df),
        '제거된_데이터_수': len(df) - len(clean_df),
        '데이터_품질_비율': (len(clean_df) / len(df)) * 100 if len(df) > 0 else 0,
        '결측치_비율': missing_percentage.sum(),
        '이상치_비율': ((supply_outliers | tax_outliers).sum() / len(df)) * 100 if len(df) > 0 else 0
    }
    
    # 깨끗한 데이터 기반 통계
    if len(clean_df) > 0:
        clean_summary = clean_df.describe()
        
        # 거래유형별 깨끗한 통계
        clean_type_stats = clean_df.groupby('거래유형').agg({
            '공급가액': ['count', 'sum', 'mean', 'std', 'min', 'max'],
            '세액': ['sum', 'mean', 'std', 'min', 'max']
        }).round(0)
        
        # 발행형태별 깨끗한 통계
        clean_form_stats = clean_df.groupby('발행형태').agg({
            '공급가액': ['count', 'sum', 'mean', 'std'],
            '세액': ['sum', 'mean', 'std']
        }).round(0)
        
        # 월별 깨끗한 통계
        clean_monthly_stats = clean_df.groupby('작성월').agg({
            '공급가액': ['count', 'sum', 'mean'],
            '세액': ['sum', 'mean']
        }).round(0)
        
        return clean_stats, clean_summary, {
            '거래유형_통계': clean_type_stats,
            '발행형태_통계': clean_form_stats,
            '월별_통계': clean_monthly_stats
        }
    else:
        return clean_stats, None, None

def create_clean_data_visualization(df):
    """
    깨끗한 데이터 시각화
    """
    if df is None or df.empty:
        return go.Figure(), go.Figure()
    
    # 결측치 확인
    missing_data = df.isnull().sum()
    
    # 이상치 탐지 (IQR 방법)
    def detect_outliers_iqr(series):
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return (series < lower_bound) | (series > upper_bound)
    
    # 공급가액과 세액의 이상치 탐지
    supply_outliers = detect_outliers_iqr(df['공급가액'])
    tax_outliers = detect_outliers_iqr(df['세액'])
    
    # 결측치나 이상치가 있는 행 제거
    clean_df = df.copy()
    clean_df = clean_df.dropna()
    clean_df = clean_df[~supply_outliers]
    clean_df = clean_df[~tax_outliers]
    
    # 데이터 품질 차트
    quality_data = {
        '구분': ['원본 데이터', '깨끗한 데이터', '제거된 데이터'],
        '데이터 수': [len(df), len(clean_df), len(df) - len(clean_df)],
        '비율': [100, (len(clean_df) / len(df)) * 100, ((len(df) - len(clean_df)) / len(df)) * 100]
    }
    
    quality_df = pd.DataFrame(quality_data)
    
    # 데이터 품질 파이 차트
    fig_quality = go.Figure(data=[go.Pie(
        labels=quality_df['구분'],
        values=quality_df['데이터 수'],
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig_quality.update_layout(
        title_text="데이터 품질 분석",
        title_x=0.5,
        height=400,
        template="plotly_white"
    )
    
    # 깨끗한 데이터 분포 차트
    if len(clean_df) > 0:
        fig_distribution = go.Figure()
        
        # 공급가액 분포
        fig_distribution.add_trace(go.Histogram(
            x=clean_df['공급가액'],
            name='공급가액',
            nbinsx=30,
            marker_color='#1f77b4'
        ))
        
        # 세액 분포
        fig_distribution.add_trace(go.Histogram(
            x=clean_df['세액'],
            name='세액',
            nbinsx=30,
            marker_color='#ff7f0e'
        ))
        
        fig_distribution.update_layout(
            title_text="깨끗한 데이터 분포",
            title_x=0.5,
            xaxis_title="금액 (원)",
            yaxis_title="빈도",
            height=400,
            template="plotly_white",
            barmode='overlay'
        )
        
        return fig_quality, fig_distribution
    else:
        return fig_quality, go.Figure()

def create_data_quality_report(df):
    """
    데이터 품질 리포트 생성
    """
    if df is None or df.empty:
        return "데이터가 없습니다."
    
    report = []
    report.append("## 📊 데이터 품질 분석 리포트")
    report.append("")
    
    # 기본 정보
    report.append(f"**📈 전체 데이터 수**: {len(df):,}건")
    report.append("")
    
    # 결측치 분석
    missing_data = df.isnull().sum()
    missing_percentage = (missing_data / len(df)) * 100
    
    report.append("### 🔍 결측치 분석")
    for col in df.columns:
        if missing_data[col] > 0:
            report.append(f"- **{col}**: {missing_data[col]:,}건 ({missing_percentage[col]:.2f}%)")
        else:
            report.append(f"- **{col}**: 결측치 없음 ✅")
    report.append("")
    
    # 이상치 분석
    def detect_outliers_iqr(series):
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return (series < lower_bound) | (series > upper_bound)
    
    supply_outliers = detect_outliers_iqr(df['공급가액'])
    tax_outliers = detect_outliers_iqr(df['세액'])
    
    report.append("### 🚨 이상치 분석")
    report.append(f"- **공급가액 이상치**: {supply_outliers.sum():,}건 ({(supply_outliers.sum() / len(df)) * 100:.2f}%)")
    report.append(f"- **세액 이상치**: {tax_outliers.sum():,}건 ({(tax_outliers.sum() / len(df)) * 100:.2f}%)")
    report.append("")
    
    # 깨끗한 데이터 통계
    clean_df = df.copy()
    clean_df = clean_df.dropna()
    clean_df = clean_df[~supply_outliers]
    clean_df = clean_df[~tax_outliers]
    
    report.append("### ✨ 깨끗한 데이터 통계")
    report.append(f"- **깨끗한 데이터 수**: {len(clean_df):,}건")
    report.append(f"- **데이터 품질 비율**: {(len(clean_df) / len(df)) * 100:.2f}%")
    report.append(f"- **제거된 데이터 수**: {len(df) - len(clean_df):,}건")
    report.append("")
    
    if len(clean_df) > 0:
        report.append("### 📋 깨끗한 데이터 요약 통계")
        report.append(f"- **공급가액 평균**: {clean_df['공급가액'].mean():,.0f}원")
        report.append(f"- **공급가액 중앙값**: {clean_df['공급가액'].median():,.0f}원")
        report.append(f"- **세액 평균**: {clean_df['세액'].mean():,.0f}원")
        report.append(f"- **세액 중앙값**: {clean_df['세액'].median():,.0f}원")
        report.append("")
        
        # 거래유형별 깨끗한 통계
        type_stats = clean_df.groupby('거래유형')['공급가액'].agg(['count', 'sum', 'mean']).round(0)
        report.append("### 💼 거래유형별 깨끗한 데이터")
        for idx, row in type_stats.iterrows():
            report.append(f"- **{idx}**: {row['count']:,}건, {row['sum']:,.0f}원, 평균 {row['mean']:,.0f}원")
    
    return "\n".join(report)
