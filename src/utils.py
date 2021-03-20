from tqdm import tqdm
import itertools
import os

import bokeh
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from bokeh.layouts import row
from bokeh.models import (CategoricalTicker, ColorBar, ColumnDataSource,
                          LinearColorMapper, NumeralTickFormatter, FactorRange)
from bokeh.models.tools import HoverTool
from bokeh.palettes import RdYlGn
from bokeh.plotting import figure, output_file, show
from bokeh.plotting.figure import Figure
from bokeh.transform import linear_cmap

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import List

import config

# pylint: disable=too-many-function-args


def get_driver():
    if 'DYNO' in os.environ:    # if in heroku env
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_SHIM',
                                                        None)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')

    else:      # if in local env
        chrome_options = Options()
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options,
                              executable_path=config.CHROMEDRIVER_PATH)

    return driver


def get_xG_html_table(name: str, year: int, force_update: bool = False, stats: str = "players") -> str:
    """stats = 'players' or 'statistics' or 'league'
    """
    path_name = os.path.join(
        config.CACHE_PATH, f"{name}_{year}_{stats}.txt")

    # try cache
    if os.path.exists(path_name) and not force_update:
        with open(path_name) as cache_text:
            table_html = cache_text.read().replace('\n', '')
        return table_html

    driver = get_driver()

    mode = 'team' if stats in ["players", "statistics"] else "league"

    driver.get(f"https://understat.com/{mode}/{name}/{year}")
    team_soup = BeautifulSoup(driver.page_source)

    if mode == "team":
        table_html = str(team_soup.find(
            "div", {"id": f"team-{stats}"}).find("table"))
    elif mode == "league":
        table_html = team_soup.find(
            "div", {"id": "league-chemp"}).find("table")

    driver.quit()

    with open(path_name, "w") as cache_text:
        cache_text.write(table_html)

    return table_html


def process_html(html_table: str, mode: str = "A") -> pd.DataFrame:
    df_team = pd.read_html(html_table)[0].drop("№", axis=1).iloc[:15]

    df_team["xG"] = (df_team["xG"]
                     .str
                     .split(r"\+|\-")
                     .apply(lambda x: float(x[0])))

    df_team[f"x{mode}"] = (df_team[f"x{mode}"]
                           .str
                           .split(r"\+|\-")
                           .apply(lambda x: float(x[0])))

    df_team["diff_xG"] = (df_team["G"] - df_team["xG"])
    df_team[f"diff_x{mode}"] = (df_team[f"{mode}"] - df_team[f"x{mode}"])

    # select only rows which score
    # is at least 0.5 xG or xA/xGA
    df_team = df_team[(df_team["xG"] > 0.5) | (df_team[f"x{mode}"] > 0.5)]

    return df_team


def plot_xG_df(df_xG_team: pd.DataFrame, team_name: str, year: int, mode: str = "G") -> Figure:
    if mode == "G":
        full_mode = "Goal"
    elif mode == "A":
        full_mode = "Assist"
    else:
        raise AttributeError(f"No such mode {mode}")

    plot_max = max(df_xG_team[f"x{mode}"].max() + 2,
                   df_xG_team[f"{mode}"].max() + 2)

    amplitude = max(abs(df_xG_team[f"diff_x{mode}"].min()),
                    abs(df_xG_team[f"diff_x{mode}"].max()))
    amplitude = max(amplitude, 2)   # at least 2 goals/assists of diff

    color_mapper = LinearColorMapper(
        palette=RdYlGn[9][::-1], low=-amplitude, high=amplitude)

    fig = figure(
        title=f"x{full_mode} vs. vrais {full_mode} pour {team_name}, saison {year}-{year + 1}",
        y_range=(-0.5, plot_max),
        plot_width=900,
        plot_height=600,
    )

    fig.xaxis.axis_label = f'x{full_mode}'
    fig.yaxis.axis_label = f'{full_mode}'
    fig.xaxis.axis_label_text_font_size = "18pt"
    fig.yaxis.axis_label_text_font_size = "18pt"

    fig.line([0, plot_max], [0, plot_max], color="black",
             legend_label="Performance normale", line_width=2)

    fig.line([0, plot_max], [0, 1.2 * plot_max],
             line_dash=[8, 8], legend_label="Surperf de 20 %", line_color='green', line_width=2)

    fig.line([0, plot_max], [0, 0.8 * plot_max],
             line_dash=[8, 8], legend_label="Sousperf de 20 %", line_color='red', line_width=2)

    fig.line([0, plot_max], [0, 1.4 * plot_max],
             line_dash=[4, 4], line_color='green', line_width=1)

    fig.line([0, plot_max], [0, 0.6 * plot_max],
             line_dash=[4, 4], line_color='red', line_width=1)

    r = fig.circle(x=f'x{mode}',
                   y=f'{mode}',
                   source=df_xG_team,
                   size=10,
                   color={'field': f'diff_x{mode}', 'transform': color_mapper})

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
            ('', '@Player'),
            ('xG', '@xG{0.2f}'),
            ('G', '@G{0.2f}'),
            ('Diff. xG vs G', '@diff_xG{0.2f}')
        ]
    elif mode == "A":
        hover.tooltips = [
            ('', '@Player'),
            ('xA', '@xA{0.2f}'),
            ('A', '@A{0.2f}'),
            ('Diff. xA vs A', '@diff_xA{0.2f}')
        ]
    else:
        raise AttributeError(f"No such mode {mode}")

    color_bar = ColorBar(color_mapper=color_mapper, width=8)

    fig.add_layout(color_bar, 'right')
    fig.add_tools(hover)
    fig.legend.location = "top_left"

    fig.toolbar.logo = None
    fig.toolbar_location = None

    return fig


def make_situation_chart(df_stats: pd.DataFrame, team_name: str, year: int) -> Figure:
    x = df_stats['Situation']
    y = df_stats['diff_xG']

    amplitude = df_stats['diff_xG'].abs().max() + 1
    amplitude = max(amplitude, 4.5)   # at least 4 goals of diff so clip
    color_mapper = LinearColorMapper(
        palette=RdYlGn[11][::-1], low=-amplitude, high=amplitude)

    h_barchart = figure(
        title=f'Visualisation de la diff xG pour {team_name}, saison {year}-{year + 1}',
        y_range=x.values,
        x_range=(- amplitude, amplitude))

    h_barchart.yaxis.ticker = CategoricalTicker()
    r = h_barchart.hbar(right=y, y=x, height=0.2,
                        color={'field': "right", 'transform': color_mapper},
                        )

    glyph = r.glyph
    glyph.fill_alpha = 1
    glyph.line_color = "black"
    glyph.line_width = 0.2

    hover = HoverTool()
    hover.tooltips = [('diff xG', '@y'), ('Catégorie', '@right{0.2f}')]
    h_barchart.add_tools(hover)

    h_barchart.toolbar.logo = None
    h_barchart.toolbar_location = None

    color_bar = ColorBar(color_mapper=color_mapper, width=12)
    color_bar_plot = figure(height=500, width=100,
                            toolbar_location="right", title="Diff. de xG")

    color_bar_plot.add_layout(color_bar, 'right')
    color_bar_plot.toolbar.logo = None
    color_bar_plot.toolbar_location = None

    layout = row(h_barchart, color_bar_plot)

    return layout


def make_quality_shot_chart(df_stats: pd.DataFrame, team_name: str, year: int) -> Figure:
    df_stats = df_stats[df_stats["Situation"] != "Penalty"]
    x = list(itertools.product(df_stats["Situation"], ["xG/Sh", "xGA/Sh"]))
    counts = sum(zip(df_stats['xG/Sh'], df_stats['xGA/Sh']), ())

    source = ColumnDataSource(data=dict(x=x, counts=counts))
    _ = "représente la qualité des tirs vs. la qualité des tirs adverses"

    fig = figure(x_range=FactorRange(*x),
                 title=f"Différence de xG pour (xG) et contre (xGA) par situation de jeu pour {team_name}, saison {year}-{year + 1}",
                 tooltips="@x : @counts{0.2f}")

    amplitude = max(counts)
    amplitude = 0.2
    color_mapper = LinearColorMapper(
        palette=RdYlGn[11][::-1], low=0, high=amplitude)

    fig.vbar(x='x', top='counts', width=0.9,
             source=source, line_color="black", line_width=0.5,
             fill_color={'field': "counts", 'transform': color_mapper},
             )

    fig.y_range.start = 0
    fig.xgrid.grid_line_color = None

    fig.toolbar.logo = None
    fig.toolbar_location = None

    return fig


def update_db(list_teams: List, list_years: List, stats: str):
    for team, year in tqdm(itertools.product(list_teams, list_years)):
        try:
            get_xG_html_table(team, year, force_update=True, stats=stats)
        except:
            print(f'unable to update {team}-{year}')


def make_sidebar():
    st.sidebar.header("Paramètres")

    country_choice = st.sidebar.selectbox(
        'Quelle pays veux-tu analyser ?',
        config.LIST_OF_COUNTRIES,
        index=0)

    team_mode = st.sidebar.selectbox('Mode ? (par ligue ou par équipe)',
                                     ('Par ligue', 'Par équipe'))

    if team_mode == "Par équipe":
        team_choice = st.sidebar.selectbox(
            'Quelle équipe veux-tu analyser ?',
            config.COUNTRY_TEAMS[country_choice],
            index=0)
    else:
        team_choice = st.text("")

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

    parameters = country_choice, team_choice, year_choice, team_mode
    analysis = goal_options, assist_options, situations_options, shots_quality_options, top_players_options

    return parameters, analysis


def process_html_ligue(html_league_table: str):

    df_league = pd.read_html(str(table_html))[0]

    for col in ["xG", "xGA", "xPTS"]:
        df_league[col] = (df_league[col]
                          .str
                          .split('[+-]', expand=True)[0]
                          .astype(float))

        df_league[f"diff_{col}"] = df_league[col[1:]] - df_league[col]

    df_league["theoretical_rank"] = df_league["xPTS"].rank(ascending=False)
    df_league["true_rank"] = df_league["PTS"].rank(ascending=False)

    return df_league
