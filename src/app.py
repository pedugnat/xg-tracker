import streamlit as st
from bokeh.plotting import show

import config
from utils import (get_xG_html_table, make_situation_chart, plot_xG_df,
                   process_html, make_quality_shot_chart)


def make_sidebar():
    st.sidebar.header("Paramètres")

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

    st.sidebar.header("Analyses")
    st.sidebar.subheader("Par joueur")

    goal_options = st.sidebar.checkbox("Montrer les buts", value=True)
    assist_options = st.sidebar.checkbox("Montrer les assists", value=True)
    top_players_options = st.sidebar.checkbox(
        "Montrer les top killers/croqueurs", value=True)

    st.sidebar.subheader("Par équipe")

    situations_options = st.sidebar.checkbox(
        "Montrer les situations", value=True)
    shots_quality_options = st.sidebar.checkbox(
        "Montrer la qualité des tirs", value=True)

    parameters = country_choice, team_choice, year_choice
    analysis = goal_options, assist_options, situations_options, shots_quality_options, top_players_options

    return parameters, analysis


st.set_page_config(page_title="xG Tracker",
                   layout='wide',
                   initial_sidebar_state='auto')

st.title("xG Tracker")
st.subheader("Quelles équipes et quels joueurs surperforment ?")
st.text("")

parameters, analysis = make_sidebar()

country_choice, team_choice, year_choice = parameters
goal_options, assist_options, situations_options, shots_quality_options, top_players_options = analysis


if (team_choice != "<Choix d'une équipe>") & (country_choice != "<Choix d'un pays>"):
    html_team_table = get_xG_html_table(team_choice, year=year_choice)
    df_team = process_html(html_team_table)

    goal_plot = plot_xG_df(df_team, team_name=team_choice,
                           year=year_choice, mode="G")
    assist_plot = plot_xG_df(df_team, team_name=team_choice,
                             year=year_choice, mode="A")

    html_stats_table = get_xG_html_table(
        team_choice, year=year_choice, stats="statistics")
    df_stats_team = process_html(html_stats_table, mode="GA")

    situation_chart = make_situation_chart(
        df_stats_team, team_choice, year_choice)
    quality_shot_char = make_quality_shot_chart(
        df_stats_team, team_choice, year_choice)

    if goal_options:
        st.header("Goals vs xGoals")
        st.bokeh_chart(goal_plot)

    if assist_options:
        st.header("Assists vs xAssists")
        st.bokeh_chart(assist_plot)

    if top_players_options:
        formating_dict = {"xG": "{:.2f}",
                          "xA": "{:.2f}",
                          "diff_xG": "{:.2f}",
                          "Apparitions": "{:,.0f}",
                          "Minutes": "{:,.0f}"}

        cols_to_drop = ["Pos", "Sh90", "KP90", "xG90", "xA90", "diff_xA"]
        df_team_top = (df_team
                       .drop(cols_to_drop, axis=1)
                       .set_index('Player')
                       .round(2)
                       .rename(columns={"Apps": "Apparitions",
                                        "Min": "Minutes",
                                        "G": "Buts",
                                        "A": "Passes dé",
                                        # "diff_xG": "différence de xG",
                                        }))

        st.header("Top 3 killers")
        df_killers = (df_team_top
                      .sort_values(by="diff_xG", ascending=False)
                      .head(3)
                      .style
                      .format(formating_dict))

        st.dataframe(df_killers)

        st.header("Top 3 croqueurs")
        df_croqueurs = (df_team_top
                        .sort_values(by="diff_xG")
                        .head(3)
                        .style
                        .format(formating_dict))

        st.dataframe(df_croqueurs)

    if situations_options:
        st.header("Différence xG par situation de jeu")
        st.bokeh_chart(situation_chart)

    if shots_quality_options:
        st.header("Qualité des tirs pour et contre")
        st.bokeh_chart(quality_shot_char)

    st.text("")
    st.info('Source / credits: https://understat.com/')

# hide footer "Made with Streamlit"
hide_streamlit_style = """
            <style>
            # MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
