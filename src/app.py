import streamlit as st
from bokeh.plotting import show

import config
from utils import get_xG_html_table, plot_xG_df, process_html

st.set_page_config(page_title="xG Tracker",
                   layout='wide',
                   initial_sidebar_state='auto')

st.title("xG Tracker : quels joueurs surperforment ?")
st.text("")

team_choice = st.sidebar.selectbox(
    'Quelle équipe veux-tu analyser ?',
    config.LIST_OF_TEAMS,
    index=0)

year_choice = st.sidebar.selectbox(
    'Quelle année veux-tu analyser ?',
    config.LIST_OF_YEARS,
    index=0)

col_1, col_2, _, _, _, _ = st.beta_columns(6)

goal_options = col_1.checkbox("Montrer les buts", value=True)
assist_options = col_2.checkbox("Montrer les assists", value=True)

if team_choice != "<Choix d'une équipe>":
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
