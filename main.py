import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import git

local_directory_path = './chohan'

# Repository URL
repo_url = 'https://github.com/ajsj2200/chohan.git'

# 디렉토리가 존재하지 않을 경우에만 clone
if not os.path.exists(local_directory_path):
    git.Repo.clone_from(repo_url, local_directory_path)
else:
    print(f"{local_directory_path} already exists. Skipping clone.")

# 현재 작업 디렉터리 가져오기
current_directory = os.getcwd()

file_list = os.listdir('data')
st.text(current_directory)
st.text(file_list)
def get_student_dict(path, path2):
    student_list = pd.read_csv(path)
    student_list = student_list.iloc[2:]
    student_list.columns = student_list.iloc[0]
    student_list = student_list.iloc[1:]
    student_list.dropna(subset=['학번'], inplace=True)
    student_list['학번'] = student_list['학번'].astype(int).astype(str)
    student_list.set_index('이름', inplace=True)
    student_list = student_list.loc[:, ['학번', '코드']]

    df = pd.read_csv(path2)
    df.columns = df.iloc[0, :]
    df = df.iloc[1:]
    df.dropna(subset=['학번'], inplace=True)

    num_of_question = len(df.columns[5:-4]) // 2

    questions = df.iloc[:, :5+num_of_question].loc[:, np.arange(1, num_of_question+1)]

    tmp = pd.concat([df.loc[:, ['학번', '성명']], questions], axis=1)
    tmp.set_index('성명', inplace=True)
    tmp.index = tmp.index.astype(str)

    organized_df = pd.merge(student_list, tmp, how='left', left_index=True, right_index=True)
    organized_df.drop(['학번_y'], axis=1, inplace=True)

    organized_df.columns = ['학번', '코드'] + [f'{i}' for i in range(1, num_of_question+1)]
    
    return organized_df

def auth(my_number, my_code, df):
    search_number = df[df['학번'] == my_number]
    search_code = df[df['코드'] == my_code]
    if len(search_number) == 0:
        st.error("학번을 확인해주세요.")
    elif len(search_code) == 0:
        st.error("코드를 확인해주세요.")
    else:
        return df[df['학번'] == my_number]

def get_question_level(path):
    questions_level = pd.read_csv(path, encoding='cp949').iloc[1:]
    questions_level['번호'] = questions_level['번호'].astype(int).astype(str)
    questions_level.set_index('번호', inplace=True)

    questions_level = questions_level.loc[:, ['정답', '난이도']]
    questions_level.dropna(subset=['정답'], inplace=True)
    questions_level['정답'] = questions_level['정답'].astype(int).astype(str)
    return questions_level

def get_question_content(path):
    questions_content = pd.read_csv(path)
    questions_content.set_index('번호', inplace=True)
    questions_content.columns = ['과목', '파트']
    questions_content.index = questions_content.index.astype(int).astype(str)
    return questions_content

def main():

    with st.sidebar:
        my_number = st.text_input("학번 입력", "202119124")
        my_code = st.text_input("코드 입력", "진짜조한웅")
        rounds = st.slider("회차 선택", 1, 15, 1)
        lesson = st.slider("교시 선택", 1, 3, 1)
        submit = st.button("제출")

    if submit:
        
        path1 = "{}/data/2023학년도 3학년 모의고사 결과표.csv".format(current_directory)
        path2 = "{}/{}/data/{}회차/{}교시 답안지.csv".format(current_directory, local_directory_path, rounds, lesson)
        path3 = '{}/{}/data/{}회차/{}교시 난이도.csv'.format(current_directory, local_directory_path, rounds, lesson)
        path4 = '{}/{}/data/{}회차/{}교시 문제내용.csv'.format(current_directory, local_directory_path, rounds, lesson)
        df = get_student_dict(path1, path2)
        my_df = auth(my_number, my_code, df)

        # 학번, 코드 칼럼 제외하고 int로 변환
        my_df.iloc[:, 2:] = my_df.iloc[:, 2:].astype(int).astype(str)
        my_df = my_df.T.iloc[2:]
        my_df.columns = ['내 정답']

        question_level = get_question_level(path3)
        question = pd.merge(my_df, question_level, how='left', left_index=True, right_index=True)

        question_content = get_question_content(path4)
        question = pd.concat([question, question_content], axis=1)
        question_incorrect = question[question['내 정답'] != question['정답']]

        if my_df is not None:
            tabs = st.tabs(["출제 경향", "오답 문제", "난이도", "난이도별 오답문제"])

            # 출제 경향 탭
            with tabs[0]:
                trend_unique = question['과목'].unique()
                
                for trend in trend_unique:
                    st.header(f"{trend} 과목")
                    trend_df = question[question['과목'] == trend]
                    
                    part_unique = trend_df['파트'].unique()
                    for i, part in enumerate(part_unique):
                        st.subheader(f"{i+1}. {part} 파트")
                        part_df = trend_df[trend_df['파트'] == part]
                        text = part_df.index.values
                        text = [x+'번' for x in text]
                        st.text(text)
                        st.markdown('---')
            
            # 오답 문제 탭
            with tabs[1]:
                trend_unique = question['과목'].unique()
                
                for trend in trend_unique:
                    st.header(f"{trend} 과목")
                    trend_df_incorrect = question_incorrect[question_incorrect['과목'] == trend]
                    
                    part_unique = trend_df_incorrect['파트'].unique()
                    for i, part in enumerate(part_unique):
                        st.subheader(f"{i+1}. {part} 파트")
                        part_df = trend_df_incorrect[trend_df_incorrect['파트'] == part]
                        text = part_df.index.values
                        text = [x+'번' for x in text]
                        st.text(text)
                        st.markdown('---')

            # 난이도 탭
            with tabs[2]:
                tmp = question.copy()
                tmp['난이도'] = tmp['난이도'].astype(float)

                # 난이도를 5단위로 구간을 나누고, 그에 따른 라벨링
                bins = [i for i in range(0, 101, 5)]  # 0~100까지 5단위
                labels = [f'{i}-{i+5}' for i in range(0, 100, 5)]
                tmp['난이도 구간'] = pd.cut(tmp['난이도'], bins=bins, labels=labels, right=False)

                # 각 구간별 데이터 출력
                for label in reversed(labels):
                    st.subheader(f"난이도 {label}")
                    df_level = tmp[tmp['난이도 구간'] == label]
                    text = df_level.index.values
                    text = [x+'번' for x in text]
                    if len(text) > 0:
                        st.text(text)
                    else:
                        st.text("해당 구간에 문제가 없습니다.")
                    st.markdown('---')

            # 난이도별 오답문제 탭
            with tabs[3]:
                tmp = question_incorrect.copy()
                tmp['난이도'] = tmp['난이도'].astype(float)

                # 난이도를 5단위로 구간을 나누고, 그에 따른 라벨링
                bins = [i for i in range(0, 101, 5)]  # 0~100까지 5단위
                labels = [f'{i}-{i+5}' for i in range(0, 100, 5)]
                tmp['난이도 구간'] = pd.cut(tmp['난이도'], bins=bins, labels=labels, right=False)

                # 각 구간별 데이터 출력
                for label in reversed(labels):
                    st.subheader(f"난이도 {label}")
                    df_level = tmp[tmp['난이도 구간'] == label]
                    text = df_level.index.values
                    text = [x+'번' for x in text]
                    if len(text) > 0:
                        st.text(text)
                    else:
                        st.text("해당 구간에 문제가 없습니다.")
                    st.markdown('---')


if __name__ == "__main__":
    main()
