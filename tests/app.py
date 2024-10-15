import pandas as pd
from shiny import App, render, reactive, ui

import shiny_adaptive_filter as saf

data = {
    "total_bill": [16.99, 10.34, 21.01, 23.68, 24.59],
    "tip": [1.01, 1.66, 3.50, 3.31, 3.61],
    "sex": ["Female", "Male", "Male", "Male", "Female"],
    "smoker": ["No", "No", "No", "No", "Yes"],
    "day": ["Sun", "Sun", "Sun", "Fri", "Sun"],
    "time": ["Lunch", "Dinner", "Dinner", "Dinner", "Dinner"],
    "size": [2, 3, 3, 2, 4],
}

tips = pd.DataFrame(data)

app_ui = ui.page_sidebar(
    ui.sidebar(
        saf.filter_ui("adaptive"),
    ),
    ui.output_data_frame("render_df"),
)


def server(input, output, session):
    @reactive.calc
    def data_filtered():
        df = tips.loc[filter_idx()]
        return df

    @render.data_frame
    def render_df():
        return render.DataGrid(data_filtered())

    override = {
        "total_bill": None,
        "tip": None,
        "time": saf.FilterCatStringSelect,
        "size": "Party Size",
    }

    filter_return = saf.filter_server(
        "adaptive",
        df=tips,
        override=override,
    )
    filter_idx = filter_return["filter_idx"]


app = App(app_ui, server)
