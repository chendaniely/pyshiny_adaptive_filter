import pandas as pd
from shiny import App, render, reactive, ui

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
        ui.input_checkbox_group(
            "filter_day",
            "Day:",
            {x: x for x in sorted(tips["day"].unique())},
        ),
        ui.input_checkbox_group(
            "filter_time",
            "Time:",
            {x: x for x in sorted(tips["time"].unique())},
        ),
    ),
    ui.output_data_frame("render_df"),
)


def server(input, output, session):
    @reactive.calc
    def data_filtered():
        df = tips
        if input.filter_day():
            df = df.loc[df["day"].isin(input.filter_day())]
        if input.filter_time():
            df = df.loc[df["time"].isin(input.filter_time())]
        return df

    @render.data_frame
    def render_df():
        return render.DataGrid(data_filtered())


app = App(app_ui, server)
