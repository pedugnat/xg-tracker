# pylint: disable=too-many-function-args,invalid-name,missing-function-docstring

import itertools
import os
import re
from typing import List

import pandas as pd
import streamlit as st
from bokeh.layouts import row
from bokeh.models import (
    CategoricalColorMapper,
    CategoricalTicker,
    ColorBar,
    ColumnDataSource,
    FactorRange,
    LinearColorMapper,
)
from bokeh.models.tools import HoverTool
from bokeh.palettes import RdYlGn
from bokeh.plotting import figure
from bokeh.plotting.figure import Figure
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

import config


def get_driver():
    if "DYNO" in os.environ:  # if in heroku env
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get(
            "GOOGLE_CHROME_SHIM", None)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

    else:  # if in local env
        chrome_options = Options()
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(
        options=chrome_options, executable_path=config.CHROMEDRIVER_PATH
    )

    return driver


def get_xG_html_table(
    name: str, year: int, force_update: bool = False, stats: str = "players"
):
    """stats is 'players' or 'statistics' or 'league' or 'matches'"""
    path_name = os.path.join(config.CACHE_PATH, f"{name}_{year}_{stats}.txt")

    # try cache
    if os.path.exists(path_name) and not force_update:
        print("used cache")
        with open(path_name) as cache_text:
            table_html = cache_text.read().replace("\n", "")
        return table_html

    driver = get_driver()

    mode = "team" if stats in ["players",
                               "statistics", "matches"] else "league"

    driver.get(f"https://understat.com/{mode}/{name}/{year}")
    team_soup = BeautifulSoup(driver.page_source, "lxml")

    if stats in ["players", "statistics"]:
        table_html = str(team_soup.find(
            "div", {"id": f"team-{stats}"}).find("table"))
    elif stats == "league":
        table_html = str(team_soup.find(
            "div", {"id": "league-chemp"}).find("table"))
    elif stats == "matches":
        table_html = str(team_soup.find(
            "div", {"class": "calendar-container"}))

    driver.quit()

    with open(path_name, "w+") as cache_text:
        print(f"saved file for {name}-{year}")
        cache_text.write(table_html)

    return table_html


def process_html(html_table: str, mode: str = "A"):
    df_team = pd.read_html(html_table)[0].drop("№", axis=1).iloc[:15]

    for col in ["xG", f"x{mode}"]:
        df_team[col] = df_team[col].str.split(
            r"\+|\-").apply(lambda x: float(x[0]))

    df_team["diff_xG"] = df_team["G"] - df_team["xG"]
    df_team[f"diff_x{mode}"] = df_team[f"{mode}"] - df_team[f"x{mode}"]

    # select only rows which score
    # is at least 0.5 xG or xA/xGA
    df_team = df_team[(df_team["xG"] > 0.5) | (df_team[f"x{mode}"] > 0.5)]

    return df_team


def plot_xG_df(
    df_xG_team: pd.DataFrame, team_name: str, year: int, mode: str = "G"
) -> Figure:
    if mode == "G":
        full_mode = "Goal"
    elif mode == "A":
        full_mode = "Assist"
    else:
        raise AttributeError(f"No such mode {mode}")

    plot_max = max(df_xG_team[f"x{mode}"].max(),
                   df_xG_team[f"{mode}"].max()) + 2

    amplitude = max(
        abs(df_xG_team[f"diff_x{mode}"].min()), abs(
            df_xG_team[f"diff_x{mode}"].max())
    )
    amplitude = max(amplitude, 2)  # at least 2 goals/assists of diff

    color_mapper = LinearColorMapper(
        palette=RdYlGn[9][::-1], low=-amplitude, high=amplitude
    )

    fig = figure(
        title=f"x{full_mode} vs. vrais {full_mode} pour {team_name}, saison {year}-{year + 1}",
        y_range=(-0.5, plot_max),
        plot_width=900,
        plot_height=600,
    )

    fig.xaxis.axis_label = f"x{full_mode}"
    fig.yaxis.axis_label = f"{full_mode}"
    fig.xaxis.axis_label_text_font_size = "16pt"
    fig.yaxis.axis_label_text_font_size = "16pt"
    fig.xaxis.major_label_text_font_size = "12pt"
    fig.yaxis.major_label_text_font_size = "12pt"

    fig.line(
        [0, plot_max],
        [0, plot_max],
        color="black",
        legend_label="Performance normale",
        line_width=2,
    )

    fig.line(
        [0, plot_max],
        [0, 1.2 * plot_max],
        line_dash=[8, 8],
        legend_label="Surperf de 20 %",
        line_color="green",
        line_width=2,
    )

    fig.line(
        [0, plot_max],
        [0, 0.8 * plot_max],
        line_dash=[8, 8],
        legend_label="Sousperf de 20 %",
        line_color="red",
        line_width=2,
    )

    fig.line(
        [0, plot_max],
        [0, 1.4 * plot_max],
        line_dash=[4, 4],
        line_color="green",
        line_width=1,
    )

    fig.line(
        [0, plot_max],
        [0, 0.6 * plot_max],
        line_dash=[4, 4],
        line_color="red",
        line_width=1,
    )

    r = fig.circle(
        x=f"x{mode}",
        y=f"{mode}",
        source=df_xG_team,
        size=10,
        color={"field": f"diff_x{mode}", "transform": color_mapper},
    )

    glyph = r.glyph
    glyph.size = 15
    glyph.fill_alpha = 1
    glyph.line_color = "black"
    glyph.line_width = 1

    fig.background_fill_color = "gray"
    fig.background_fill_alpha = 0.05

    hover = HoverTool()
    if mode == "G":
        hover.tooltips = [
            ("", "@Player"),
            ("xG", "@xG{0.2f}"),
            ("G", "@G{0.2f}"),
            ("Diff. xG vs G", "@diff_xG{0.2f}"),
        ]
    elif mode == "A":
        hover.tooltips = [
            ("", "@Player"),
            ("xA", "@xA{0.2f}"),
            ("A", "@A{0.2f}"),
            ("Diff. xA vs A", "@diff_xA{0.2f}"),
        ]
    else:
        raise AttributeError(f"No such mode: {mode}")

    color_bar = ColorBar(color_mapper=color_mapper, width=8)

    fig.add_layout(color_bar, "right")
    fig.add_tools(hover)
    fig.legend.location = "top_left"

    fig.toolbar.logo = None
    fig.toolbar_location = None

    return fig


def make_situation_chart(df_stats: pd.DataFrame, team_name: str, year: int) -> Figure:
    situation = df_stats["Situation"]
    diff_xg = df_stats["diff_xG"]

    amplitude = df_stats["diff_xG"].abs().max() + 1
    amplitude = max(amplitude, 4.5)  # at least 4 goals of diff so clip
    color_mapper = LinearColorMapper(
        palette=RdYlGn[11][::-1], low=-amplitude, high=amplitude
    )

    h_barchart = figure(
        title=f"Visualisation de la diff xG pour {team_name}, saison {year}-{year + 1}",
        y_range=situation.values,
        x_range=(-amplitude, amplitude),
    )

    h_barchart.yaxis.ticker = CategoricalTicker()
    hbar_chart = h_barchart.hbar(
        right=diff_xg,
        y=situation,
        height=0.2,
        color={"field": "right", "transform": color_mapper},
    )

    glyph = hbar_chart.glyph
    glyph.fill_alpha = 1
    glyph.line_color = "black"
    glyph.line_width = 0.2

    hover = HoverTool()
    hover.tooltips = [("diff xG", "@y"), ("Catégorie", "@right{0.2f}")]
    h_barchart.add_tools(hover)

    h_barchart.toolbar.logo = None
    h_barchart.toolbar_location = None

    color_bar = ColorBar(color_mapper=color_mapper, width=12)
    color_bar_plot = figure(
        height=500, width=100, toolbar_location="right", title="Diff. de xG"
    )

    color_bar_plot.add_layout(color_bar, "right")
    color_bar_plot.toolbar.logo = None
    color_bar_plot.toolbar_location = None

    layout = row(h_barchart, color_bar_plot)

    return layout


def make_quality_shot_chart(
    df_stats: pd.DataFrame, team_name: str, year: int
) -> Figure:
    df_stats = df_stats[df_stats["Situation"] != "Penalty"]
    x = list(itertools.product(df_stats["Situation"], ["xG/Sh", "xGA/Sh"]))
    counts = sum(zip(df_stats["xG/Sh"], df_stats["xGA/Sh"]), ())

    source = ColumnDataSource(data=dict(x=x, counts=counts))
    _ = "représente la qualité des tirs vs. la qualité des tirs adverses"

    fig = figure(
        x_range=FactorRange(*x),
        title=(
            f"Différence de xG pour (xG) et contre (xGA) par situation de jeu "
            f"pour {team_name}, saison {year}-{year + 1}"
        ),
        tooltips="@x : @counts{0.2f}",
    )

    amplitude = 0.2
    color_mapper = LinearColorMapper(
        palette=RdYlGn[11][::-1], low=0, high=amplitude)

    fig.vbar(
        x="x",
        top="counts",
        width=0.9,
        source=source,
        line_color="black",
        line_width=0.5,
        fill_color={"field": "counts", "transform": color_mapper},
    )

    fig.y_range.start = 0
    fig.xgrid.grid_line_color = None

    fig.toolbar.logo = None
    fig.toolbar_location = None

    return fig


def update_db(list_teams: List, list_years: List, stats: str):
    for team, year in tqdm(itertools.product(list_teams, list_years)):
        #get_xG_html_table(team, year, force_update=True, stats=stats)
        try:
            get_xG_html_table(team, year, force_update=False, stats=stats)
        except AttributeError:  # pylint:disable=bare-except
            print(f"unable to update {team}-{year}")


def make_sidebar():
    st.sidebar.header("Paramètres")

    country_choice = st.sidebar.selectbox(
        "Quelle pays veux-tu analyser ?", config.LIST_OF_COUNTRIES, index=0
    )

    team_mode = st.sidebar.selectbox(
        "Mode ? (par ligue ou par équipe)",
        ("<Choix du mode>", "Par ligue", "Par équipe"),
    )

    if team_mode == "Par équipe":
        team_choice = st.sidebar.selectbox(
            "Quelle équipe veux-tu analyser ?",
            config.COUNTRY_TEAMS[country_choice],
            index=0,
        )
    else:
        team_choice = st.text("")

    year_choice = st.sidebar.selectbox(
        "Quelle année veux-tu analyser ?", config.LIST_OF_YEARS, index=0
    )

    st.sidebar.header("Analyses")
    st.sidebar.subheader("Par joueur")

    goal_options = st.sidebar.checkbox("Montrer les buts", value=True)
    assist_options = st.sidebar.checkbox("Montrer les assists", value=True)
    top_players_options = st.sidebar.checkbox(
        "Montrer les top killers/croqueurs", value=True
    )

    st.sidebar.subheader("Par équipe")

    situations_options = st.sidebar.checkbox(
        "Montrer les situations", value=True)
    shots_quality_options = st.sidebar.checkbox(
        "Montrer la qualité des tirs", value=True
    )

    parameters = country_choice, team_choice, year_choice, team_mode
    analysis = (
        goal_options,
        assist_options,
        situations_options,
        shots_quality_options,
        top_players_options,
    )

    return parameters, analysis


def process_html_league(html_league_table: str):
    df_league = pd.read_html(str(html_league_table))[0]

    for col in ["xG", "xGA", "xPTS"]:
        df_league[col] = df_league[col].str.split(
            "[+-]", expand=True)[0].astype(float)

        df_league[f"diff_{col}"] = df_league[col[1:]] - df_league[col]

    df_league["theoretical_rank"] = df_league["xPTS"].rank(ascending=False)
    df_league["true_rank"] = df_league["PTS"].rank(ascending=False)

    return df_league


def plot_xG_league(
    df_xG_league: pd.DataFrame, league_name: str, year: int, mode="G"
) -> Figure:
    if mode == "G":
        full_mode = "Goal"
    elif mode == "GA":
        full_mode = "GoalAgainst"
    elif mode == "PTS":
        full_mode = "Points"
    else:
        raise AttributeError(f"No such mode {mode}")

    k_offset = 5
    plot_max = (
        max(df_xG_league[f"x{mode}"].max(),
            df_xG_league[f"{mode}"].max()) + k_offset
    )

    plot_min = (
        min(df_xG_league[f"x{mode}"].min(),
            df_xG_league[f"{mode}"].min()) - k_offset
    )

    amplitude = max(
        abs(df_xG_league[f"diff_x{mode}"].min()),
        abs(df_xG_league[f"diff_x{mode}"].max()),
    )

    if mode in ["G", "PTS"]:
        graph_palette = RdYlGn[9][::-1]
    elif mode == "GA":
        graph_palette = RdYlGn[9]
    else:
        raise AttributeError(f"No such mode: {mode}")

    color_mapper = LinearColorMapper(
        palette=graph_palette, low=-amplitude, high=amplitude
    )

    fig = figure(
        title=f"x{full_mode} vs. vrais {full_mode} pour {league_name}, saison {year}-{year + 1}",
        y_range=(plot_min, plot_max),
        x_range=(plot_min, plot_max),
        plot_width=900,
        plot_height=600,
    )

    fig.xaxis.axis_label = f"x{full_mode}"
    fig.yaxis.axis_label = f"{full_mode}"
    fig.xaxis.axis_label_text_font_size = "16pt"
    fig.yaxis.axis_label_text_font_size = "16pt"
    fig.xaxis.major_label_text_font_size = "12pt"
    fig.yaxis.major_label_text_font_size = "12pt"

    fig.line(
        [0, plot_max],
        [0, plot_max],
        color="black",
        legend_label="Performance normale",
        line_width=2,
    )

    r = fig.circle(
        x=f"x{mode}",
        y=f"{mode}",
        source=df_xG_league,
        size=10,
        color={"field": f"diff_x{mode}", "transform": color_mapper},
    )

    glyph = r.glyph
    glyph.size = 15
    glyph.fill_alpha = 1
    glyph.line_color = "black"
    glyph.line_width = 1

    fig.background_fill_color = "gray"
    fig.background_fill_alpha = 0.05

    hover = HoverTool()
    if mode == "G":
        hover.tooltips = [
            ("", "@Team"),
            ("xG", "@xG{0.2f}"),
            ("G", "@G{0.2f}"),
            ("Diff. xG vs G", "@diff_xG{0.2f}"),
        ]
    elif mode == "GA":
        hover.tooltips = [
            ("", "@Team"),
            ("xGA", "@xGA{0.2f}"),
            ("GA", "@GA{0.2f}"),
            ("Diff. xGA vs GA", "@diff_xGA{0.2f}"),
        ]
    elif mode == "PTS":
        hover.tooltips = [
            ("", "@Team"),
            ("xPTS", "@xPTS{0.2f}"),
            ("PTS", "@PTS{0.2f}"),
            ("Diff. xPTS vs PTS", "@diff_xPTS{0.2f}"),
        ]
    else:
        raise AttributeError(f"No such mode {mode}")

    color_bar = ColorBar(color_mapper=color_mapper, width=8)

    fig.add_layout(color_bar, "right")
    fig.add_tools(hover)
    fig.legend.location = "top_left"

    fig.toolbar.logo = None
    fig.toolbar_location = None

    return fig


def make_croqueurs_killers(df_team):
    formating_dict = {
        "xG": "{:.2f}",
        "xA": "{:.2f}",
        "diff_xG": "{:.2f}",
        "Apparitions": "{:,.0f}",
        "Minutes": "{:,.0f}",
    }

    cols_to_drop = ["Pos", "Sh90", "KP90", "xG90", "xA90", "diff_xA"]
    df_team_top = (
        df_team.drop(cols_to_drop, axis=1)
        .set_index("Player")
        .round(2)
        .rename(
            columns={
                "Apps": "Apparitions",
                "Min": "Minutes",
                "G": "Buts",
                "A": "Passes dé",
            }
        )
    )

    df_killers = (
        df_team_top.sort_values(by="diff_xG", ascending=False)
        .head(3)
        .style.format(formating_dict)
    )

    df_croqueurs = (
        df_team_top.sort_values(by="diff_xG").head(
            3).style.format(formating_dict)
    )

    return df_killers, df_croqueurs


def make_match_dict(match: str) -> dict:
    """Converts raw html of match boxes to dict"""
    date = match.find("div", {"class": "calendar-date"}).text
    opponent = match.find("div", {"class": "team-title"}).text
    goals = match.find("div", {"class": "teams-xG"}).text
    home_goals = goals[:4]
    away_goals = goals[4:]

    tag_results = str(match.find("div", {"class": "calendar-date"}))
    match_result = re.findall(r"data-result=(.{3})", tag_results)[0][1]
    team_side = re.findall(r"data-side=(.{3})", tag_results)[0][1]

    match_dict = {
        "date": date,
        "opponent": opponent,
        "team_side": team_side,
        "match_result": match_result,
        "home_xGoals": float(home_goals),
        "away_xGoals": float(away_goals),
    }

    return match_dict


def process_df_teams(df_team: pd.DataFrame, days_rolling: int):
    """Create team xG columns from home/away xG
    and adds rolling xG"""
    goals_if_home = (df_team["team_side"] == "h") * df_team["home_xGoals"]
    goals_if_away = (df_team["team_side"] == "a") * df_team["away_xGoals"]

    df_team["team_xGoals"] = goals_if_home + goals_if_away
    df_team["opponents_xGoals"] = (
        df_team["home_xGoals"] +
        df_team["away_xGoals"] - df_team["team_xGoals"]
    )

    df_team = df_team.reset_index()
    df_team["journée"] = df_team["index"] + 1
    df_team["rolling_team_xG"] = (
        df_team["team_xGoals"].rolling(days_rolling, min_periods=2).mean()
    )

    df_team["rolling_opponent_xG"] = (
        df_team["opponents_xGoals"].rolling(days_rolling, min_periods=2).mean()
    )

    side_mapper = {"h": "Domicile", "a": "Extérieur"}
    result_mapper = {"w": "Victoire", "d": "Match Nul", "l": "Défaite"}

    df_team["team_side"] = df_team["team_side"].map(side_mapper)
    df_team["match_result"] = df_team["match_result"].map(result_mapper)

    return df_team


def make_matches_df_from_html(table_html: str):
    list_matches = BeautifulSoup(table_html).find_all(
        "div", {"class": "calendar-date-container mini"}
    )

    match_info = dict()
    for j, match in enumerate(list_matches):
        try:
            match_info[j] = make_match_dict(match)
        except AttributeError:  # match not played yet
            pass

    df_team = pd.DataFrame.from_dict(match_info).T
    df_team = process_df_teams(df_team, days_rolling=6)

    return df_team


def plot_xG_team_df(
    df_team: pd.DataFrame,
    team_name: str,
    year: int,
    rolling_xG: bool,
    rolling_xGA: bool,
) -> Figure:
    team_max_xG = df_team["team_xGoals"].max() + 0.5

    fig = figure(
        title=f"xG pour {team_name}, saison {year}-{year + 1}",
        plot_width=900,
        plot_height=600,
        x_axis_label="x",
        y_axis_label="y",
        y_range=(0, team_max_xG),
    )

    match_outcomes = ["Victoire", "Match Nul", "Défaite"]
    color_mapper = CategoricalColorMapper(
        factors=match_outcomes, palette=RdYlGn[len(match_outcomes)]
    )

    r = fig.circle(
        x="journée",
        y="team_xGoals",
        source=df_team,
        size=10,
        color={"field": "match_result", "transform": color_mapper},
    )

    if rolling_xG:
        fig.line(
            x="journée",
            y="rolling_team_xG",
            source=df_team,
            color="green",
            legend_label="Moyenne glissante de xG produits (6 matchs)",
            line_width=1.5,
        )

    if rolling_xGA:
        fig.line(
            x="journée",
            y="rolling_opponent_xG",
            source=df_team,
            color="red",
            legend_label="Moyenne glissante de xG concédés (6 matchs)",
            line_width=1.5,
        )

    glyph = r.glyph
    glyph.size = 15
    glyph.fill_alpha = 1
    glyph.line_color = "black"
    glyph.line_width = 1

    hover = HoverTool()
    hover.tooltips = [
        ("Date", "@date"),
        ("xG", "@team_xGoals{0.2f}"),
        ("xG contre", "@opponents_xGoals{0.2f}"),
        ("Opponent", "@opponent"),
        ("Lieu", "@team_side"),
        ("Résultat", "@match_result"),
    ]
    fig.add_tools(hover)

    fig.toolbar.logo = None
    fig.toolbar_location = None

    fig.xaxis.major_label_text_font_size = "12pt"
    fig.yaxis.major_label_text_font_size = "12pt"
    fig.xaxis.axis_label = "Journée"
    fig.yaxis.axis_label = "xGoals par match"
    fig.xaxis.axis_label_text_font_size = "16pt"
    fig.yaxis.axis_label_text_font_size = "16pt"

    fig.background_fill_color = "gray"
    fig.background_fill_alpha = 0.05

    return fig
