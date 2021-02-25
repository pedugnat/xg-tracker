import os

import bokeh
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.models.tools import HoverTool
from bokeh.palettes import RdYlGn
from bokeh.plotting import figure, output_file, show
from bokeh.transform import linear_cmap
from bs4 import BeautifulSoup
from selenium import webdriver

import config

#pylint: disable=too-many-function-args


@st.cache()
def get_xG_html_table(team_name: str, year: int, force_update: bool = False) -> str:
    path_name = os.path.join(config.CACHE_PATH, f"{team_name}_{year}.txt")

    # try cache
    if os.path.exists(path_name) and not force_update:
        with open(path_name) as cache_text:
            table_html = cache_text.read().replace('\n', '')
        return table_html

    print(config.CHROMEDRIVER_PATH)

    driver = webdriver.Chrome(executable_path=config.CHROMEDRIVER_PATH)
    driver.get(f"https://understat.com/team/{team_name}/{year}")

    team_soup = BeautifulSoup(driver.page_source)
    table_html = str(team_soup.find(
        "div", {"id": "team-players"}).find("table"))

    driver.quit()

    with open(path_name, "w") as cache_text:
        cache_text.write(table_html)

    return table_html


def process_html(html_table: str) -> pd.DataFrame:
    df_team = pd.read_html(html_table)[0].drop("№", axis=1).iloc[:15]

    df_team["xG"] = df_team["xG"].str.split(
        r"\+|\-").apply(lambda x: float(x[0]))
    df_team["xA"] = df_team["xA"].str.split(
        r"\+|\-").apply(lambda x: float(x[0]))

    df_team["diff_xG"] = (df_team["G"] - df_team["xG"])
    df_team["diff_xA"] = (df_team["A"] - df_team["xA"])

    # select only players that could score
    df_team = df_team[(df_team["xG"] > 0.5) | (df_team["xA"] > 0.5)]
    df_team = df_team.round(2)

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

    return fig
