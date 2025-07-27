import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="테스트 앱", page_icon="🧪")

st.title("🧪 테스트 앱")

# 샘플 데이터 생성
@st.cache_data
def create_test_data():
    np.random.seed(42)
    months = pd.date_range('2024-01-01', '2024-06-30', freq='M')
    data = []
    
    for month in months:
        # 매출 데이터
        for _ in range(np.random.randint(5, 15)):
            data.append({
                '작성월': month.strftime('%Y-%m'),
                '거래유형': '매출',
                '발행형태': np.random.choice(['전자', '종이'], p=[0.8, 0.2]),
                '공급가액': np.random.randint(100000, 5000000),
                '세액': np.random.randint(10000, 500000)
            })
        
        # 매입 데이터
        for _ in range(np.random.randint(3, 10)):
            data.append({
                '작성월': month.strftime('%Y-%m'),
                '거래유형': '매입',
                '발행형태': np.random.choice(['전자', '종이'], p=[0.7, 0.3]),
                '공급가액': np.random.randint(50000, 3000000),
                '세액': np.random.randint(5000, 300000)
            })
    
    return pd.DataFrame(data)

# 데이터 로드
df = create_test_data()

st.write("데이터 형태:", df.shape)
st.write("컬럼:", df.columns.tolist())
st.write("첫 5행:")
st.dataframe(df.head())

# 기본 통계
st.subheader("📊 기본 통계")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("총 거래 건수", len(df))
    st.metric("매출 건수", len(df[df['거래유형'] == '매출']))
    st.metric("매입 건수", len(df[df['거래유형'] == '매입']))

with col2:
    st.metric("총 매출", f"{df[df['거래유형'] == '매출']['공급가액'].sum():,}원")
    st.metric("총 매입", f"{df[df['거래유형'] == '매입']['공급가액'].sum():,}원")
    st.metric("총 세액", f"{df['세액'].sum():,}원")

with col3:
    st.metric("평균 공급가액", f"{df['공급가액'].mean():,.0f}원")
    st.metric("평균 세액", f"{df['세액'].mean():,.0f}원")
    st.metric("전자 발행 비율", f"{(len(df[df['발행형태'] == '전자']) / len(df)) * 100:.1f}%")

# 월별 집계
st.subheader("📈 월별 집계")
monthly_data = df.groupby(['작성월', '거래유형']).agg({
    '공급가액': 'sum',
    '세액': 'sum'
}).reset_index()

st.dataframe(monthly_data)

st.success("✅ 테스트 앱이 정상적으로 작동합니다!") 