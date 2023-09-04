import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import git
import plotly.express as px


def get_student_dict(path, path2):
    student_list = pd.read_csv(path, encoding='utf-8')
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

    questions = df.iloc[:, :5+num_of_question].loc[:,
                                                   np.arange(1, num_of_question+1)]

    tmp = pd.concat([df.loc[:, ['학번', '성명']], questions], axis=1)
    tmp.set_index('성명', inplace=True)
    tmp.index = tmp.index.astype(str)

    organized_df = pd.merge(student_list, tmp, how='left',
                            left_index=True, right_index=True)
    organized_df.drop(['학번_y'], axis=1, inplace=True)

    organized_df.columns = ['학번', '코드'] + \
        [f'{i}' for i in range(1, num_of_question+1)]

    return organized_df


def auth(my_number, my_code, df):
    search_number = df[df['학번'] == my_number]
    search_code = df[df['코드'] == my_code]
    if len(search_number) == 0:
        st.error("학번을 확인해주세요.")
    elif len(search_code) == 0:
        st.error("코드를 확인해주세요.")
    elif len(search_number) != 0:
        return df[df['학번'] == my_number]
    else:
        st.error('학번과 코드를 확인해주세요.')


def get_question_level(path):
    questions_level = pd.read_csv(path, encoding='utf-8').iloc[1:]
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
    st.set_page_config(layout="wide")
    st.title("문제 분석기")

    with st.sidebar:
        my_number = st.text_input("학번 입력", "")
        my_code = st.text_input("코드 입력", "")
        rounds = st.slider("회차 선택", 1, 15, 1)
        lesson = st.slider("교시 선택", 1, 3, 1)
        submit = st.button("제출")
        st.empty()
        st.caption('made by ajsj2200')

    if not submit:

        st.caption('사이드바에서 학번과 코드를 입력하고 회차와 교시를 선택한 뒤 제출하세요!')

    if submit:
        path1 = "data/name_list.csv"
        path2 = "data/{}/{}_sheet.csv".format(rounds, lesson)
        path3 = 'data/{}/{}_level.csv'.format(rounds, lesson)
        path4 = 'data/{}/{}_contents.csv'.format(rounds, lesson)
        df = get_student_dict(path1, path2)
        my_df = auth(my_number, my_code, df)
        my_df.fillna('-1', inplace=True)

        # 학번, 코드 칼럼 제외하고 int로 변환
        my_df.iloc[:, 2:] = my_df.iloc[:, 2:].astype(int).astype(str)
        my_df = my_df.T.iloc[2:]
        my_df.columns = ['내 정답']

        question_level = get_question_level(path3)
        question = pd.merge(my_df, question_level, how='left',
                            left_index=True, right_index=True)

        question_content = get_question_content(path4)
        question = pd.concat([question, question_content], axis=1)
        question_incorrect = question[question['내 정답'] != question['정답']]

        if my_df is not None:
            col1, col2 = st.columns(2)

            with col1:
                tabs = st.tabs(["출제 경향", "출제 경향별 오답 문제"])

                # 출제 경향 탭
                with tabs[0]:
                    trend_unique = question['과목'].unique()

                    grouby_trend = question.groupby(['과목', '파트']).agg(
                        {'난이도': ['mean'], '파트': ['count']}).reset_index()
                    grouby_trend.columns = ['과목', '파트', '평균 난이도', '문제 개수']

                    # circle chart
                    fig = px.sunburst(grouby_trend, path=['과목', '파트'], values='문제 개수',
                                      color='문제 개수',
                                      hover_data=['평균 난이도'],
                                      color_continuous_scale='RdBu',
                                      color_continuous_midpoint=np.average(grouby_trend['문제 개수']))
                    st.plotly_chart(fig, use_container_width=True)

                    # bar chart
                    fig = px.bar(grouby_trend, x='과목', y='문제 개수', color='파트')
                    fig.update_layout(title='문제 개수')
                    st.plotly_chart(fig, use_container_width=True)

                    trend_tabs = st.tabs(list(trend_unique))
                    for i, trend in enumerate(trend_unique):
                        with trend_tabs[i]:
                            trend_df = question[question['과목'] == trend]
                            part_unique = trend_df['파트'].unique()
                            for j, part in enumerate(part_unique):
                                st.subheader(f"{j+1}. {part} 파트")
                                part_df = trend_df[trend_df['파트'] == part]
                                text = part_df.index.values
                                text = [x+'번' for x in text]
                                text = str(text).replace(
                                    '[', '').replace(']', '').replace("'", '')
                                st.caption(text)
                                st.markdown('---')

                # 오답 문제 탭
                with tabs[1]:
                    trend_unique = question['과목'].unique()

                    grouby_trend = question_incorrect.groupby(['과목', '파트']).agg(
                        {'난이도': ['mean'], '파트': ['count']}).reset_index()
                    grouby_trend.columns = ['과목', '파트', '평균 난이도', '문제 개수']
                    fig = px.sunburst(grouby_trend, path=['과목', '파트'], values='문제 개수',
                                      color='문제 개수',
                                      hover_data=['평균 난이도'],
                                      color_continuous_scale='RdBu',
                                      color_continuous_midpoint=np.average(grouby_trend['문제 개수']))

                    st.plotly_chart(fig, use_container_width=True)

                    # bar chart
                    fig = px.bar(grouby_trend, x='과목', y='문제 개수', color='파트')
                    fig.update_layout(title='틀린 문제 개수')
                    st.plotly_chart(fig, use_container_width=True)

                    trend_tabs = st.tabs(list(trend_unique))
                    for i, trend in enumerate(trend_unique):
                        with trend_tabs[i]:
                            trend_df = question[question['과목'] == trend]
                            part_unique = trend_df['파트'].unique()
                            for j, part in enumerate(part_unique):
                                st.subheader(f"{j+1}. {part} 파트")
                                part_df = trend_df[trend_df['파트'] == part]
                                text = part_df.index.values
                                text = [x+'번' for x in text]
                                text = str(text).replace(
                                    '[', '').replace(']', '').replace("'", '')
                                st.caption(text)
                                st.markdown('---')
            with col2:
                tabs = st.tabs(["난이도", "난이도별 오답문제"])
                # 난이도 탭
                with tabs[0]:
                    tmp = question.copy()
                    tmp['난이도'] = tmp['난이도'].astype(float)

                    # 난이도를 5단위로 구간을 나누고, 그에 따른 라벨링
                    bins = [i for i in range(0, 101, 10)]  # 0~100까지 5단위
                    labels = [f'{i}-{i+10}' for i in range(0, 100, 10)]
                    tmp['난이도 구간'] = pd.cut(
                        tmp['난이도'], bins=bins, labels=labels, right=False)

                    grouby_trend = question.groupby(['과목', '파트']).agg(
                        {'난이도': ['mean'], '파트': ['count']}).reset_index()
                    grouby_trend.columns = ['과목', '파트', '평균 난이도', '문제 개수']
                    grouby_trend[grouby_trend['평균 난이도'] == 0] = 0.01
                    fig = px.sunburst(grouby_trend, path=['과목', '파트'], values='평균 난이도',
                                      color='평균 난이도',
                                      hover_data=['문제 개수'],
                                      color_continuous_scale='RdBu',
                                      color_continuous_midpoint=np.average(grouby_trend['평균 난이도']))

                    st.plotly_chart(fig, use_container_width=True)

                    # bar chart
                    fig = px.bar(grouby_trend, x='과목', y='평균 난이도', color='파트')
                    fig.update_layout(title='평균 난이도')
                    st.plotly_chart(fig, use_container_width=True)

                    level_tabs = st.tabs(list(labels))
                    for i, label in enumerate(labels):
                        with level_tabs[i]:
                            level_df = tmp[tmp['난이도 구간'] == label]
                            text = level_df.index.values
                            text = [x+'번' for x in text]
                            text = str(text).replace(
                                '[', '').replace(']', '').replace("'", '')
                            st.caption(text)
                            st.markdown('---')

                # 난이도별 오답문제 탭
                with tabs[1]:
                    tmp = question_incorrect.copy()
                    tmp['난이도'] = tmp['난이도'].astype(float)

                    # 난이도를 5단위로 구간을 나누고, 그에 따른 라벨링
                    bins = [i for i in range(0, 101, 10)]  # 0~100까지 5단위
                    labels = [f'{i}-{i+10}' for i in range(0, 100, 10)]
                    tmp['난이도 구간'] = pd.cut(
                        tmp['난이도'], bins=bins, labels=labels, right=False)

                    grouby_trend = question_incorrect.groupby(['과목', '파트']).agg(
                        {'난이도': ['mean'], '파트': ['count']}).reset_index()
                    grouby_trend.columns = ['과목', '파트', '평균 난이도', '문제 개수']
                    grouby_trend[grouby_trend['평균 난이도'] == 0] = 0.01
                    fig = px.sunburst(grouby_trend, path=['과목', '파트'], values='평균 난이도',
                                      color='평균 난이도',
                                      hover_data=['문제 개수'],
                                      color_continuous_scale='RdBu',
                                      color_continuous_midpoint=np.average(grouby_trend['평균 난이도']))

                    st.plotly_chart(fig, use_container_width=True)

                    # bar chart
                    fig = px.bar(grouby_trend, x='과목', y='평균 난이도', color='파트')
                    fig.update_layout(title='평균 난이도')
                    st.plotly_chart(fig, use_container_width=True)

                    level_tabs = st.tabs(list(labels))
                    for i, label in enumerate(labels):
                        with level_tabs[i]:
                            level_df = tmp[tmp['난이도 구간'] == label]
                            text = level_df.index.values
                            text = [x+'번' for x in text]
                            text = str(text).replace(
                                '[', '').replace(']', '').replace("'", '')
                            st.caption(text)
                            st.markdown('---')


if __name__ == "__main__":
    main()
