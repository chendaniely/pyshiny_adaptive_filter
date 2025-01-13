import pandas as pd
from shiny import App, render, reactive, ui

import shiny_adaptive_filter as saf

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_action_button("reset", "Reset filters"),  # <<
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

    @reactive.effect  # <<
    @reactive.event(input.reset)  # <<
    def _():  # <<
        adaptive_reset_all()  # <<

    override = {
        "total_bill": saf.FilterNumNumericRange(),
        "tip": saf.FilterNumNumericRange(),
    }

    filter_return = saf.filter_server(
        "adaptive",
        df=tips,
        override=override,
    )
    filter_idx = filter_return["filter_idx"]
    adaptive_reset_all = filter_return["reset_all"]  # <<


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

app = App(app_ui, server)
