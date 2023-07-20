import pytz

import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import pandas as pd

import parse
import plot

external_stylesheets = [dbc.themes.DARKLY]
pd.options.plotting.backend = "plotly"
template = "plotly_dark"
colors = {"background": "#111111", "text": "#ffffff"}
default_fig = {}
default_df = pd.DataFrame(
    columns=["Word", "Total Reviews", "Time to Learn", "No. Relapses", "Abandoned"]
)
default_table = default_df.to_dict("records")

default_tz = "America/New_York"
timezone_list = []
for tz in pytz.common_timezones:
    timezone_list.append({"label": tz, "value": tz})

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = dbc.Container(
    [
        html.H1("JPDB Stats"),
        dbc.Modal(
            [
                dbc.ModalHeader("Welcome to the Unofficial JPDB Stats Site!"),
                dbc.ModalBody(
                    [
                        dbc.Label("Select your time zone:"),
                        dcc.Dropdown(
                            id="timezone-dropdown",
                            options=timezone_list,
                            value=default_tz,
                            style={"color": "black"},
                            persistence=True,
                        ),
                        dbc.Label("Upload your review history:"),
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(
                                [
                                    "This should be the reviews.json downloaded from the JPDB Settings page. Drag and Drop or ",
                                    html.A("Select File"),
                                ]
                            ),
                            style={
                                "width": "100%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "2px",
                            },
                            # Allow multiple files to be uploaded
                            multiple=False,
                        ),
                    ]
                ),
            ],
            id="modal-upload",
            size="xl",
            is_open=True,
        ),
        dcc.Store(id="timezone"),
        html.H3("Overall"),
        dcc.Graph(id="overall", figure=default_fig),
        dcc.Graph(id="overall_cum", figure=default_fig),
        html.H3("New Cards"),
        dcc.Graph(id="new_cum", figure=default_fig),
        dcc.Graph(id="new_daily", figure=default_fig),
        html.H3("Repetitions"),
        dcc.Graph(id="rev_cum", figure=default_fig),
        dcc.Graph(id="rev_daily", figure=default_fig),
        html.H3("Time Spent"),
        dcc.Graph(id="time_cum", figure=default_fig),
        dcc.Graph(id="time_daily", figure=default_fig),
        html.H3("Retention"),
        dcc.Graph(id="ret_known", figure=default_fig),
        dcc.Graph(id="ret_learning", figure=default_fig),
        html.H3("Problem words"),
        dash_table.DataTable(
            id="datatable-struggles",
            columns=[{"name": i, "id": i} for i in default_df.columns],
            data=default_table,
            sort_action="native",
            page_action="native",
            page_current=0,
            page_size=100,
            export_format="csv",
            style_header={"backgroundColor": "rgb(30, 30, 30)", "color": "white"},
            style_data={"backgroundColor": "rgb(50, 50, 50)", "color": "white"},
        ),
        html.Div(id="datatable-struggles-container"),
    ],
    style={"backgroundColor": colors["background"]},
    fluid=True,
)


@app.callback(
    [
        Output("new_cum", "figure"),
        Output("new_daily", "figure"),
        Output("rev_cum", "figure"),
        Output("rev_daily", "figure"),
        Output("time_cum", "figure"),
        Output("time_daily", "figure"),
        Output("overall", "figure"),
        Output("datatable-struggles", "data"),
        Output("ret_known", "figure"),
        Output("ret_learning", "figure"),
        Output("overall_cum", "figure"),
    ],
    [
        Input("upload-data", "contents"),
        Input("upload-data", "filename"),
        Input("timezone", "data"),
    ],
)
def update_graph(contents, filename, timezone):
    f_nc = default_fig
    f_nd = default_fig
    f_rc = default_fig
    f_rd = default_fig
    fm_rc = default_fig
    fm_rd = default_fig
    f_overall = default_fig
    datatable = default_table
    f_known = default_fig
    f_learn = default_fig
    f_overall_cum = default_fig
    if filename is not None:
        contents = contents.split(",")
        contents = contents[1]
        new, rev, history, struggles = parse.parse_data(contents, timezone)
        f_rc, f_rd, fm_rc, fm_rd = plot.plot_reps(rev)
        f_nc, f_nd = plot.plot_new(new)
        f_overall, f_overall_cum = plot.plot_history(history)
        f_known, f_learn = plot.plot_retention(history)
        datatable = pd.DataFrame(
            struggles,
            columns=[
                "Word",
                "Total Reviews",
                "Time to Learn",
                "No. Relapses",
                "Abandoned",
            ],
        ).to_dict("records")

    return [
        f_nc,
        f_nd,
        f_rc,
        f_rd,
        fm_rc,
        fm_rd,
        f_overall,
        datatable,
        f_known,
        f_learn,
        f_overall_cum,
    ]


@app.callback(
    [
        Output("new_cum", "style"),
        Output("new_daily", "style"),
        Output("rev_cum", "style"),
        Output("rev_daily", "style"),
        Output("time_cum", "style"),
        Output("time_daily", "style"),
        Output("overall", "style"),
        Output("ret_known", "style"),
        Output("ret_learning", "style"),
        Output("overall_cum", "style"),
    ],
    [Input("upload-data", "filename")],
)
def update_display(filename):
    if filename is not None:
        return [
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
            {"display": "block"},
        ]
    else:
        return [
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
        ]


@app.callback(Output("timezone", "data"), [Input("timezone-dropdown", "value")])
def update_timezone(value):
    return value


if __name__ == "__main__":
    app.run_server(debug=True)
