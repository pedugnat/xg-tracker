import itertools
import os

import bokeh
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from bokeh.layouts import row
from bokeh.models import (CategoricalTicker, ColorBar, ColumnDataSource,
                          LinearColorMapper, NumeralTickFormatter)
from bokeh.models.tools import HoverTool
from bokeh.palettes import RdYlGn
from bokeh.plotting import figure, output_file, show
from bokeh.transform import linear_cmap
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import config

# pylint: disable=too-many-function-args


@st.cache()
def get_xG_html_table(team_name: str, year: int, force_update: bool = False, stats: str = "players") -> str:
    path_name = os.path.join(
        config.CACHE_PATH, f"{team_name}_{year}_{stats}.txt")

    # try cache
    if os.path.exists(path_name) and not force_update:
        with open(path_name) as cache_text:
            table_html = cache_text.read().replace('\n', '')
        return table_html

    print(stats)

    if 'DYNO' in os.environ:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.binary_location = config.GOOGLE_CHROME_PATH

    else:
        chrome_options = Options()
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options,
                              executable_path=config.CHROMEDRIVER_PATH)

    driver.get(f"https://understat.com/team/{team_name}/{year}")

    team_soup = BeautifulSoup(driver.page_source)
    table_html = str(team_soup.find(
        "div", {"id": f"team-{stats}"}).find("table"))

    driver.quit()

    with open(path_name, "w") as cache_text:
        cache_text.write(table_html)

    return table_html


def process_html(html_table: str, mode: str = "A") -> pd.DataFrame:
    df_team = pd.read_html(html_table)[0].drop("№", axis=1).iloc[:15]

    df_team["xG"] = df_team["xG"].str.split(
        r"\+|\-").apply(lambda x: float(x[0]))
    df_team[f"x{mode}"] = df_team[f"x{mode}"].str.split(
        r"\+|\-").apply(lambda x: float(x[0]))

    df_team["diff_xG"] = (df_team["G"] - df_team["xG"])
    df_team[f"diff_x{mode}"] = (df_team[f"{mode}"] - df_team[f"x{mode}"])

    # select only players that could score
    # ie at least 0.5 xG or xA/xGA
    df_team = df_team[(df_team["xG"] > 0.5) | (df_team[f"x{mode}"] > 0.5)]

    return df_team


def plot_xG_df(df_xG_team: pd.DataFrame, team_name: str, year: int, mode: str = "G") -> None:
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


def make_situation_chart(df, team_name: str, year: int):
    x = df['Situation']
    y = df['diff_xG']

    amplitude = df['diff_xG'].abs().max() + 1
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
                            toolbar_location="right")

    color_bar_plot.add_layout(color_bar, 'right')
    color_bar_plot.toolbar.logo = None
    color_bar_plot.toolbar_location = None

    layout = row(h_barchart, color_bar_plot)

    return layout


def update_db(list_teams, list_years):
    for team, year in itertools.product(list_teams, list_years):
        try:
            get_xG_html_table(team, year, force_update=True)
        except:
            print(f'unable to update {team}-{year}')
