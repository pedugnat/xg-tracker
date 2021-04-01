import streamlit as st
from bokeh.plotting import show

import config
from utils import (get_xG_html_table, make_situation_chart, plot_xG_df,
                   process_html, make_quality_shot_chart, make_sidebar,
                   update_db, process_html_league, plot_xG_league)

if config.UPDATE_DB:
    for national_teams in config.COUNTRY_TEAMS.values():
        update_db(national_teams[1:], [config.UPDATE_YEAR], stats="players")
        update_db(national_teams[1:], [config.UPDATE_YEAR], stats="statistics")
    update_db(config.COUNTRY_LEAGUES.values(),
              [config.UPDATE_YEAR],
              stats="league")


st.set_page_config(page_title="xG Tracker",
                   layout='wide',
                   initial_sidebar_state='auto')

st.title("xG Tracker")
st.subheader("Quelles équipes et quels joueurs surperforment ?")

intro_txt = st.markdown(
    "Merci de choisir un pays, un mode et une équipe dans la barre latérale.")
explanation_txt = st.markdown(
    "Une fois "
    "la sélection effectuée, les graphiques sur les statistiques des joueurs "
    "et des équipes apparaîtront. Ils permettent notamment de voir quels sont "
    "les joueurs les plus et les moins performants dans chaque équipe, et de "
    "voir quelles sont les situations de jeu dans lesquelles une équipe "
    "sur ou sous-performe.")
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
            st.markdown("**Les xGoals de chaque équipe sont indiqués en abscisse (axe horizontal). "
                        "Les buts effectivement marqués sont indiqués en "
                        "ordonnée (axe vertical). Chaque point représente une équipe "
                        "et la couleur représente l'écart entre les "
                        "xGoals et les buts marqués. Plus un point est vert, "
                        "plus l'équipe est efficace devant le but ; à "
                        "l'inverse, plus un point est rouge, plus une équipe a "
                        "raté des occasions de marquer. Ainsi, une équipe normale "
                        "devrait marquer autant de but réels que de xGoals "
                        "(ligne noire). **")

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
            st.markdown("**Les xPoints de chaque équipe sont indiqués en abscisse (axe horizontal). "
                        "Les points effectivement pris sont indiqués en "
                        "ordonnée (axe vertical). Chaque point représente une équipe "
                        "et la couleur représente l'écart entre les "
                        "xPoints et les vrais points marqués.**")

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
            st.markdown("**Les xGoal Against de chaque équipe sont indiqués en abscisse (axe horizontal). "
                        "Les buts effectivement concédés sont indiqués en "
                        "ordonnée (axe vertical). Chaque point représente une équipe "
                        "et la couleur représente l'écart entre les "
                        "xGA et les buts effectivement concédés.**")

        league_plot_GA = plot_xG_league(df_league,
                                        league_name=league_name,
                                        year=year_choice,
                                        mode="GA")

        st.bokeh_chart(league_plot_GA)

elif team_mode == "Par équipe":
    if (team_choice != "<Choix d'une équipe>") & (country_choice != "<Choix d'un pays>"):
        intro_txt.empty()
        explanation_txt.empty()

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

            meaning_xg_graph = st.checkbox(
                "Que représente ce graph ?", key="goals_graph")
            if meaning_xg_graph:
                st.markdown("**Les xGoals de chaque joueur sont indiqués en abscisse (axe horizontal). "
                            "Les buts effectivement marqués sont indiqués en "
                            "ordonnée (axe vertical). Chaque point représente un joueur de "
                            "l'équipe, et la couleur représente l'écart entre les "
                            "xGoals et les buts marqués. Plus un point est vert, "
                            "plus le joueur est efficace devant le but ; à "
                            "l'inverse, plus un point est rouge, plus un joueur a "
                            "raté des occasions de marquer. Ainsi, un joueur normal "
                            "devrait marquer autant de but réels que de xGoals "
                            "(ligne noire). Un attaquant de grande classe devrait "
                            "se situer au dessus (zone de surperformance), tandis "
                            "qu'un attaquant moyen se situera en dessous (zone de "
                            "sous-performance). **")

            st.bokeh_chart(goal_plot)

        if assist_options:
            st.header("Assists vs xAssists")

            meaning_xa_graph = st.checkbox(
                "Que représente ce graph ?", key="assists_graph")
            if meaning_xa_graph:
                st.markdown("**Les xAssists de chaque joueur sont indiqués en abscisse (axe horizontal). "
                            "Les passes dé (assists) effectivement données sont indiqués en "
                            "ordonnée (axe vertical). Chaque point représente un joueur de "
                            "l'équipe, et la couleur représente l'écart entre les "
                            "xAssists et les passe dés réellement données. Ainsi, "
                            "un joueur normal devrait donner autant de passes dé "
                            "qu'il n'a d'xAssists (ligne noire). Un joueur "
                            "dont les passes dé se transforment souvent en buts devrait "
                            "se situer au-dessus (zone de surperformance), tandis "
                            "qu'un passeur dont les passes ne sont que peu converties se "
                            "situera au-dessous (zone de sous-performance). **")

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
                                            "A": "Passes dé"}))

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

            meaning_diff_situations = st.checkbox(
                "Que représente ce graph ?", key="situations_graph")
            if meaning_diff_situations:
                st.markdown("**Ce graph représente la différence entre le nombre de "
                            "buts marqués et le nombre de xGoals par situation de jeu. Cela "
                            "permet d'idenfitier les situations dans lesquelles une équipe "
                            "sur ou sous-performe sur la saison, et donc ses points "
                            "forts ou faibles. **")

            st.bokeh_chart(situation_chart)

        if shots_quality_options:
            st.header("Qualité des tirs pour et contre")

            meaning_diff_shots = st.checkbox(
                "Que représente ce graph ?", key="differentiel_graph")
            if meaning_diff_shots:
                st.markdown("**Ce graph représente la différence de qualité de tirs "
                            "entre les tirs proposés et encaissés par une équipe. "
                            "Plus une équipe proposera des tirs de qualité, "
                            "plus la moyenne xG par tir sera élevée. Plus une équipe"
                            "concèdera des tirs de qualité, plus sa moyenne xGA par "
                            "tir sera élevée, signe d'une vulnérabilité. Le différentiel "
                            "est donc un outil pour évaluer la domination d'une "
                            "équipe en fonction des situations de jeu. **")

            st.bokeh_chart(quality_shot_char)

st.text("")
st.info('Source / credits: https://understat.com/')

hide_streamlit_style = """
            <style>
            # MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
