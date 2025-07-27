#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

def fix_csv_encoding(input_file, output_file):
    """
    깨진 인코딩의 CSV 파일을 수정하는 함수
    """
    try:
        # 파일을 바이너리로 읽기
        with open(input_file, 'rb') as f:
            raw_data = f.read()
        
        # 여러 인코딩 시도
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                # 디코딩 시도
                decoded_data = raw_data.decode(encoding)
                print(f"성공적으로 {encoding} 인코딩으로 디코딩했습니다.")
                
                # pandas로 읽기
                df = pd.read_csv(input_file, encoding=encoding)
                print(f"데이터 형태: {df.shape}")
                print(f"컬럼: {df.columns.tolist()}")
                
                # UTF-8로 저장
                df.to_csv(output_file, index=False, encoding='utf-8')
                print(f"파일이 {output_file}로 저장되었습니다.")
                return True
                
            except UnicodeDecodeError:
                print(f"{encoding} 인코딩 실패")
                continue
            except Exception as e:
                print(f"{encoding} 처리 중 오류: {str(e)}")
                continue
        
        # 마지막 시도: engine='python' 사용
        try:
            df = pd.read_csv(input_file, engine='python', encoding_errors='ignore')
            print("Python 엔진으로 로드 성공")
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"파일이 {output_file}로 저장되었습니다.")
            return True
        except Exception as e:
            print(f"Python 엔진 처리 중 오류: {str(e)}")
            return False
            
    except Exception as e:
        print(f"파일 처리 중 오류: {str(e)}")
        return False

if __name__ == "__main__":
    input_file = "3-4-1._개인사업자_재무제표_주요_계정과목_신고_현황_20250728005955 (1).csv"
    output_file = "fixed_tasis_data.csv"
    
    print("CSV 파일 인코딩 수정 중...")
    success = fix_csv_encoding(input_file, output_file)
    
    if success:
        print("✅ 인코딩 수정 완료!")
    else:
        print("❌ 인코딩 수정 실패") 