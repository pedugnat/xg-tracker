import streamlit as st
from bokeh.plotting import show

import config
from utils import get_xG_html_table, plot_xG_df, process_html

st.set_page_config(page_title="xG Tracker",
                   layout='wide',
                   initial_sidebar_state='auto')

st.title("xG Tracker : quels joueurs surperforment ?")
st.text("")

country_choice = st.sidebar.selectbox(
    'Quelle pays veux-tu analyser ?',
    config.LIST_OF_COUNTRIES,
    index=0)

team_choice = st.sidebar.selectbox(
    'Quelle équipe veux-tu analyser ?',
    config.COUNTRY_TEAMS[country_choice],
    index=0)

year_choice = st.sidebar.selectbox(
    'Quelle année veux-tu analyser ?',
    config.LIST_OF_YEARS,
    index=0)

col_1, col_2, *_ = st.beta_columns(6)

st.sidebar.text("")
goal_options = st.sidebar.checkbox("Montrer les buts", value=True)

st.sidebar.text("")
assist_options = st.sidebar.checkbox("Montrer les assists", value=True)

if (team_choice != "<Choix d'une équipe>") & (country_choice != "<Choix d'un pays>"):
    html_team_table = get_xG_html_table(team_choice, year=year_choice)
    df_team = process_html(html_team_table)

    goal_plot = plot_xG_df(df_team, team_name=team_choice,
                           year=year_choice, mode="G")
    assist_plot = plot_xG_df(df_team, team_name=team_choice,
                             year=year_choice, mode="A")

    if goal_options:
        st.header("Goals vs xGoals")
        st.bokeh_chart(goal_plot)

    if assist_options:
        st.header("Assists vs xAssists")
        st.bokeh_chart(assist_plot)

    st.write('Source: https://understat.com/league/Ligue_1')
