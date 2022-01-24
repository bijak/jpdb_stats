import base64
from datetime import datetime
import io
import json

import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd

external_stylesheets = [dbc.themes.DARKLY]
pd.options.plotting.backend = "plotly"
template = "plotly_dark"
colors = {"background": "#111111", "text": "#ffffff"}
default_fig = {}

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(
    [
        html.H1("JPDB Stats"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["This should be the vocabulary-reviews.json downloaded from the JPDB Settings page. Drag and Drop or ", html.A("Select File")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=False,
        ),
        html.H3("New Cards"),
        dcc.Graph(id="new_cum", figure=default_fig),
        dcc.Graph(id="new_daily", figure=default_fig),
        html.H3("Reviews"),
        dcc.Graph(id="rev_cum", figure=default_fig),
        dcc.Graph(id="rev_daily", figure=default_fig)
    ],
    style={'backgroundColor':colors["background"]}
)


@app.callback(
    [Output("new_cum", "figure"),Output("new_daily", "figure"),Output("rev_cum", "figure"),Output("rev_daily", "figure")],
    [Input("upload-data", "contents"), Input("upload-data", "filename")],
)
def update_graph(contents, filename):
    f_nc = default_fig; f_nd = default_fig; f_rc = default_fig; f_rd = default_fig
    if filename == 'vocabulary-reviews.json':
        contents = contents.split(',')
        contents = contents[1]
        new, rev = parse_data(contents, filename)
        f_rc, f_rd = parse_reviews(rev)
        f_nc, f_nd = parse_new(new)

    return [f_nc, f_nd, f_rc, f_rd]

@app.callback(
    [Output("new_cum", "style"),Output("new_daily", "style"),Output("rev_cum", "style"),Output("rev_daily", "style")],
    [Input("upload-data", "filename")],
)
def update_display(filename):
    if filename == 'vocabulary-reviews.json':
        return [{"display":"block"},{"display":"block"},{"display":"block"},{"display":"block"}]
    else:
        return [{"display":"none"},{"display":"none"},{"display":"none"},{"display":"none"}]



def parse_data(contents, filename):
    decoded = base64.b64decode(contents)
    new = []
    rev = []
    try:
        reviews_json = json.load(io.StringIO(decoded.decode("utf-8")))
        for entry in reviews_json["cards_vocabulary_jp_en"]:
            new.append(datetime.utcfromtimestamp(entry['reviews'][0]['timestamp']).date())
            for review in entry['reviews']:
                rev.append(datetime.utcfromtimestamp(review['timestamp']).date())
    except Exception as e:
        print(e)
        return html.Div(["Make sure to upload the vocabulary-reviews.json downloadable in your jpdb.io Settings"])

    return new, rev

def parse_reviews(rev):
    reviews = pd.DataFrame(rev, columns=['Date'])
    reviews['Count'] = 1
    reviews = reviews.groupby('Date').sum()

    idx = pd.date_range(reviews.index.min(), reviews.index.max())
    reviews.index = pd.DatetimeIndex(reviews.index)
    reviews = reviews.reindex(idx, fill_value=0)
    reviews_cum = reviews.cumsum()
    # Cum. Plot
    f_rc = reviews_cum.plot()
    f_rc.update_layout(
        title="Reviews (Cum.)",
        yaxis_title="Total reviews",
        xaxis_title="Date",
        template=template
    )
    # Daily Plot
    f_rd = reviews.plot(kind="bar")
    f_rd.update_layout(
        title="Reviews (Daily)",
        yaxis_title="Daily reviews",
        xaxis_title="Date",
        template=template
    )

    return f_rc, f_rd

def parse_new(new_in):
    new = pd.DataFrame(new_in, columns=['Date'])
    new['Count'] = 1
    new = new.groupby('Date').sum()

    idx = pd.date_range(new.index.min(), new.index.max())
    new.index = pd.DatetimeIndex(new.index)
    new = new.reindex(idx, fill_value=0)
    new_cum = new.cumsum()
    # Cum. Plot
    f_nc = new_cum.plot()
    f_nc.update_layout(
        title="New Cards (Cum.)",
        yaxis_title="Total cards added",
        xaxis_title="Date",
        template=template
    )
    # Daily. Plot
    f_nd = new.plot(kind="bar")
    f_nd.update_layout(
        title="New Cards (Daily)",
        yaxis_title="New Cards",
        xaxis_title="Date",
        template=template
    )

    return f_nc, f_nd

if __name__ == "__main__":
    app.run_server(debug=True)