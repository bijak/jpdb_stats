import base64
import datetime
import io
import plotly.graph_objs as go
import json

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import pandas as pd

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

colors = {"graphBackground": "#F5F5F5", "background": "#ffffff", "text": "#000000"}

app.layout = html.Div(
    [
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
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
        dcc.Graph(id="new_cum"),
        dcc.Graph(id="new_daily"),
        dcc.Graph(id="rev_cum"),
        dcc.Graph(id="rev_daily"),
    ]
)


@app.callback(
    [Output("new_cum", "f_nc"),Output("new_daily", "f_nd"),Output("rev_cum", "f_rc"),Output("rev_daily", "f_rd")],
    [Input("upload-data", "contents"), Input("upload-data", "filename")],
)
def update_graph(contents, filename):
    fig = {
        "layout": go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"],
        )
    }

    if contents:
        contents = contents[0]
        filename = filename[0]
        new, rev = parse_data(contents, filename)
        f_rc, f_rd = parse_reviews(rev)
        f_nc, f_nd = parse_new(new)

    return f_nc, f_nd, f_rc, f_rd


def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if filename == 'vocabulary-reviews.json':
            reviews_json = json.load(io.StringIO(decoded.decode("utf-8")))
            new = []
            rev = []
            for entry in reviews_json["cards_vocabulary_jp_en"]:
                new.append(datetime.utcfromtimestamp(entry['reviews'][0]['timestamp']).date())
                for review in entry['reviews']:
                    rev.append(datetime.utcfromtimestamp(review['timestamp']).date())
    except Exception as e:
        print(e)
        return html.Div(["Make sure to upload the vocabulary-reviews.json downloadable in your jpdb.io Settings"])

    return new, rev

def parse_reviews(rev):
    f_rc = {
        "layout": go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"],
        )
    }

    f_rd = {
        "layout": go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"],
        )
    }

    reviews = pd.DataFrame(rev, columns=['Date'])
    reviews['Count'] = 1
    reviews = reviews.groupby('Date').sum()

    idx = pd.date_range(reviews.index.min(), reviews.index.max())
    reviews.index = pd.DatetimeIndex(reviews.index)
    reviews = reviews.reindex(idx, fill_value=0)
    reviews_cum = reviews.cumsum()
    # Cum. Plot
    p_rc = reviews_cum.iplot(asFigure=True)
    p_rc.set_ylabel("Total reviews")
    p_rc.set_title("Reviews (Cum.)")
    p_rc.set_ylim(bottom=0)
    f_rc["data"] = p_rc
    # Cum. Plot
    p_rd = reviews.iplot(asFigure=True)
    p_rd.set_ylabel("Daily reviews")
    p_rd.set_title("Reviews (Daily)")
    p_rd.set_ylim(bottom=0)
    f_rd["data"] = p_rd

    return f_rc, f_rd

def parse_new(new_in):
    f_nc = {
        "layout": go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"],
        )
    }

    f_nd = {
        "layout": go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"],
        )
    }

    new = pd.DataFrame(new_in, columns=['Date'])
    new['Count'] = 1
    new = new.groupby('Date').sum()

    idx = pd.date_range(new.index.min(), new.index.max())
    new.index = pd.DatetimeIndex(new.index)
    new = new.reindex(idx, fill_value=0)
    new_cum = new.cumsum()
    # Cum. Plot
    p_nc = new_cum.iplot(asFigure=True)
    p_nc.set_ylabel("Total cards added")
    p_nc.set_title("New Cards (Cum.)")
    p_nc.set_ylim(bottom=0)
    f_nc["data"] = p_nc
    # Cum. Plot
    p_nd = new.iplot(asFigure=True)
    p_nd.set_ylabel("Daily cards added")
    p_nd.set_title("New Cards (Daily)")
    p_nd.set_ylim(bottom=0)
    f_nd["data"] = p_nd

    return f_nc, f_nd

if __name__ == "__main__":
    app.run_server(debug=True)