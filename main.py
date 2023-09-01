import pandas as pd
import streamlit as st

st.header('난이도 파일 업로드')
uploaded_file = st.file_uploader("파일 업로드", type="xlsx")
st.header('내 정답 파일 업로드')
uploaded_file_sheet = st.file_uploader("파일 업로드", type="csv")

# 파일이 업로드 되었는지 확인
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    if uploaded_file_sheet is not None:
        df_sheet = pd.read_csv(uploaded_file_sheet)

        # 문제수는 df의 ['반응도']의 길이
        df.dropna(subset=['반응도'], inplace=True)
        num_of_question = len(df['반응도'])

        df = df[:num_of_question]
        df_sheet = df_sheet[:num_of_question]

        df['제출답안'] = df_sheet['제출답안']

        # 문제 내용이 없으므로 우선 '반응도'를 문제 내용으로 사용
        df['문제 내용'] = df['반응도']

        # 정답과 제출답안이 다른 번호만 추출
        wrong_answer = df[df['정답'] != df['제출답안']]

        # 틀린 문제만 header에 '틀린문제 {번호}'로 출력. text_area에 틀린 문제 출력
        for i in wrong_answer.index.values:
            st.header(f'문제 {i}')
            st.markdown(
                f'**정답**: {wrong_answer.loc[i]["정답"]}, **제출답안**: {wrong_answer.loc[i]["제출답안"]}')
            st.text_area(
                f'틀린문제 {i+1}', value=wrong_answer.loc[i]['문제 내용'], height=100)
            st.markdown('---')
