import streamlit as st
from bokeh.plotting import show

import config
import texts
from utils import *

if config.UPDATE_DB:
    for national_teams in config.COUNTRY_TEAMS.values():
        update_db(national_teams[1:], [config.UPDATE_YEAR], stats="players")
        update_db(national_teams[1:], [config.UPDATE_YEAR], stats="statistics")
        update_db(national_teams[1:], [config.UPDATE_YEAR], stats="matches")
    update_db(config.COUNTRY_LEAGUES.values(),
              [config.UPDATE_YEAR],
              stats="league")


st.set_page_config(page_title="xG Tracker",
                   layout='wide',
                   initial_sidebar_state='auto')

st.title("xG Tracker")
st.subheader("Quelles équipes et quels joueurs surperforment ?")

intro_txt = st.markdown(texts.INTRO_TXT)
explanation_txt = st.markdown(texts.EXPLANATION_TXT)
st.text("")

parameters, analysis = make_sidebar()

country_choice, team_choice, year_choice, team_mode = parameters
goal_options, assist_options, situations_options, shots_quality_options, top_players_options = analysis

if team_mode == "Par ligue":
    if (country_choice != "<Choix d'un pays>"):
        intro_txt.empty()
        explanation_txt.empty()

        league_name = config.COUNTRY_LEAGUES[country_choice]
        html_league_table = get_xG_html_table(league_name,
                                              year=year_choice,
                                              stats="league")
        df_league = process_html_league(html_league_table)

        # Goals per league
        st.header(
            f"Goals vs xGoals en {league_name}, saison {year_choice}-{year_choice + 1}")

        meaning_league_xg_graph = st.checkbox(
            "Que représente ce graph ?", key="league_goals_graph")
        if meaning_league_xg_graph:
            st.markdown(texts.MEANING_LEAGUE_XG_GRAPH)

        league_plot_G = plot_xG_league(df_league,
                                       league_name=league_name,
                                       year=year_choice,
                                       mode="G")

        st.bokeh_chart(league_plot_G)

        # Points per league
        st.header(
            f"Points vs xPoints en {league_name}, saison {year_choice}-{year_choice + 1}")

        meaning_league_xpts_graph = st.checkbox(
            "Que représente ce graph ?", key="league_pts_graph")
        if meaning_league_xpts_graph:
            st.markdown(texts.MEANING_LEAGUE_XPTS_GRAPH)

        league_plot_PTS = plot_xG_league(df_league,
                                         league_name=league_name,
                                         year=year_choice,
                                         mode="PTS")

        st.bokeh_chart(league_plot_PTS)

        # Goal Against per league
        st.header(
            f"Goal Against (GA) vs xGoal Against (xGA) en {league_name},"
            f"saison {year_choice}-{year_choice + 1}")

        meaning_league_xGA_graph = st.checkbox(
            "Que représente ce graph ?", key="league_GA_graph")
        if meaning_league_xGA_graph:
            st.markdown(texts.MEANING_LEAGUE_XGA_GRAPH)

        league_plot_GA = plot_xG_league(df_league,
                                        league_name=league_name,
                                        year=year_choice,
                                        mode="GA")

        st.bokeh_chart(league_plot_GA)

elif team_mode == "Par équipe":
    if (team_choice != "<Choix d'une équipe>") & (country_choice != "<Choix d'un pays>"):
        intro_txt.empty()
        explanation_txt.empty()

        table_html = get_xG_html_table(team_choice,
                                       year=year_choice,
                                       stats="matches")
        df_matches = make_matches_df_from_html(table_html)

        left, right = st.beta_columns(2)
        with left:
            rolling_xG = st.checkbox("Afficher la moyenne glissante de xG ?",
                                     value=True)
        with right:
            rolling_xGA = st.checkbox(
                "Afficher la moyenne glissante de xG concédés ?")

        matches_plot = plot_xG_team_df(df_matches,
                                       team_name=team_choice,
                                       year=year_choice,
                                       rolling_xG=rolling_xG,
                                       rolling_xGA=rolling_xGA)

        html_team_table = get_xG_html_table(team_choice, year=year_choice)
        df_team = process_html(html_team_table)

        goal_plot = plot_xG_df(df_team, team_name=team_choice,
                               year=year_choice, mode="G")
        assist_plot = plot_xG_df(df_team, team_name=team_choice,
                                 year=year_choice, mode="A")

        html_stats_table = get_xG_html_table(
            team_choice, year=year_choice, stats="statistics")
        df_stats_team = process_html(html_stats_table, mode="GA")

        situation_chart = make_situation_chart(df_stats_team,
                                               team_choice,
                                               year_choice)
        quality_shot_char = make_quality_shot_chart(df_stats_team,
                                                    team_choice,
                                                    year_choice)

        st.bokeh_chart(matches_plot)

        if goal_options:
            st.header("Goals vs xGoals")

            meaning_xg_graph = st.checkbox("Que représente ce graph ?",
                                           key="goals_graph")
            if meaning_xg_graph:
                st.markdown(texts.MEANING_XG_GRAPH)

            st.bokeh_chart(goal_plot)

        if assist_options:
            st.header("Assists vs xAssists")

            meaning_xa_graph = st.checkbox("Que représente ce graph ?",
                                           key="assists_graph")
            if meaning_xa_graph:
                st.markdown(texts.MEANING_XA_GRAPH)

            st.bokeh_chart(assist_plot)

        if top_players_options:
            df_killers, df_croqueurs = make_croqueurs_killers(df_team)

            st.header("Top 3 killers")
            st.dataframe(df_killers)

            st.header("Top 3 croqueurs")
            st.dataframe(df_croqueurs)

        if situations_options:
            st.header("Différence xG par situation de jeu")

            meaning_diff_situations = st.checkbox("Que représente ce graph ?",
                                                  key="situations_graph")
            if meaning_diff_situations:
                st.markdown(texts.MEANING_DIFF_SITUATIONS)

            st.bokeh_chart(situation_chart)

        if shots_quality_options:
            st.header("Qualité des tirs pour et contre")

            meaning_diff_shots = st.checkbox("Que représente ce graph ?",
                                             key="differentiel_graph")
            if meaning_diff_shots:
                st.markdown(texts.MEANING_DIFF_SHOTS)

            st.bokeh_chart(quality_shot_char)

st.text("")
st.info('Source / credits: https://understat.com/')

st.markdown(config.HIDE_FOOTER, unsafe_allow_html=True)
