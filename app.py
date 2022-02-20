import base64
from datetime import datetime
import io
import json
import pytz

import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from matplotlib.pyplot import hist

import pandas as pd

external_stylesheets = [dbc.themes.DARKLY]
pd.options.plotting.backend = "plotly"
template = "plotly_dark"
colors = {"background": "#111111", "text": "#ffffff"}
default_fig = {}
default_df = pd.DataFrame(columns=["Word", "Total Reviews", "Time to Learn", "No. Relapses"])
default_table = default_df.to_dict('records')

timezone_list = []
for tz in pytz.common_timezones:
    timezone_list.append({'label':tz, 'value':tz})

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(
    [
        html.H1("JPDB Stats"),
        dcc.Dropdown(
            id='timezone-dropdown',
            options=timezone_list,
            value='America/New_York',
            style={'color': 'black'}
        ),
        dcc.Store(id='timezone'),
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
        html.H3("Overall"),
        dcc.Graph(id="overall", figure=default_fig),
        html.H3("New Cards"),
        dcc.Graph(id="new_cum", figure=default_fig),
        dcc.Graph(id="new_daily", figure=default_fig),
        html.H3("Reviews"),
        dcc.Graph(id="rev_cum", figure=default_fig),
        dcc.Graph(id="rev_daily", figure=default_fig),
        html.H3("Problem words"),
        dash_table.DataTable(
            id='datatable-struggles',
            columns=[
                {"name": i, "id": i} for i in default_df.columns
            ],
            data=default_table,
            sort_action="native",
            page_action="native",
            page_current= 0,
            page_size= 25,
            style_header={
                'backgroundColor': 'rgb(30, 30, 30)',
                'color': 'white'
            },
            style_data={
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white'
            }
        ),
        html.Div(id='datatable-struggles-container')
    ],
    style={'backgroundColor':colors["background"]}
)


@app.callback(
    [Output("new_cum", "figure"),Output("new_daily", "figure"),Output("rev_cum", "figure"),Output("rev_daily", "figure"),Output("overall", "figure"),Output("datatable-struggles","data")],
    [Input("upload-data", "contents"), Input("upload-data", "filename"), Input("timezone", "data")],
)
def update_graph(contents, filename, timezone):
    f_nc = default_fig; f_nd = default_fig; f_rc = default_fig; f_rd = default_fig; f_overall = default_fig; datatable = default_table
    if (filename is not None) and filename.startswith('vocabulary'):
        contents = contents.split(',')
        contents = contents[1]
        new, rev, history, struggles = parse_data(contents, filename, timezone)
        f_rc, f_rd = parse_reviews(rev)
        f_nc, f_nd = parse_new(new)
        f_overall = parse_history(history)
        datatable = pd.DataFrame(struggles, columns=["Word", "Total Reviews", "Time to Learn", "No. Relapses"]).to_dict('records')

    return [f_nc, f_nd, f_rc, f_rd, f_overall, datatable]

@app.callback(
    [Output("new_cum", "style"),Output("new_daily", "style"),Output("rev_cum", "style"),Output("rev_daily", "style"), Output("overall", "style")],
    [Input("upload-data", "filename")],
)
def update_display(filename):
    if (filename is not None) and filename.startswith('vocabulary'):
        return [{"display":"block"},{"display":"block"},{"display":"block"},{"display":"block"},{"display":"block"}]
    else:
        return [{"display":"none"},{"display":"none"},{"display":"none"},{"display":"none"},{"display":"none"}]

@app.callback(Output("timezone","data"), [Input("timezone-dropdown","value")])
def update_timezone(value):
    return value

def parse_data(contents, filename, timezone):
    decoded = base64.b64decode(contents)
    new = []
    rev = []
    history = []
    struggles = []
    try:
        reviews_json = json.load(io.StringIO(decoded.decode("utf-8")))
        for entry in reviews_json["cards_vocabulary_jp_en"]:
            if (len(entry['reviews']) == 0):
                continue
            new.append(datetime.utcfromtimestamp(entry['reviews'][0]['timestamp']).astimezone(pytz.timezone(timezone)).date())
            for review in entry['reviews']:
                rev.append(datetime.utcfromtimestamp(review['timestamp']).astimezone(pytz.timezone(timezone)).date())
            history += parse_entry(entry, timezone)
            struggles += parse_struggles(entry)
    except Exception as e:
        print(e)
        return html.Div(["Make sure to upload the vocabulary-reviews.json downloadable in your jpdb.io Settings"])

    return new, rev, history, struggles

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

def is_successful(string):
    if string in ['known', 'pass', 'hard', 'easy', 'okay']:
        return 1
    return 0

def is_fail(string):
    if string in ['known', 'pass', 'hard', 'easy', 'okay']:
        return 0
    return 1

# The idea here is not to count reviews that are either the first review for a word or reviews that aren't the first review of the day
def parse_entry(entry, timezone):
    history = []
    previous = None
    for review in entry['reviews']:
        if previous is None:
            history.append([datetime.utcfromtimestamp(review['timestamp']).date(), 0, 0, 1])
        elif (previous is not None) and (datetime.utcfromtimestamp(previous['timestamp']).astimezone(pytz.timezone(timezone)).date() != datetime.utcfromtimestamp(review['timestamp']).date()):
            history.append([datetime.utcfromtimestamp(review['timestamp']).astimezone(pytz.timezone(timezone)).date(), is_fail(review['grade']), is_successful(review['grade']), 0 ])
        previous = review
    return history

def parse_history(history):
    history_df = pd.DataFrame(history, columns=['Date', 'Failed', 'Passed', 'New'])
    history_df = history_df.groupby('Date').sum()
    idx = pd.date_range(history_df.index.min(), history_df.index.max())
    history_df.index = pd.DatetimeIndex(history_df.index)
    history_df = history_df.reindex(idx, fill_value=0)
    colors = ['#EF553B','#00CC96','#636EFA']
    f_history = history_df.plot(kind='bar', color_discrete_sequence=colors)
    f_history.update_layout(
        title="Cards (Daily)",
        yaxis_title="Card Count",
        xaxis_title="Date",
        template=template
    )
    return f_history\

def parse_struggles(entry):
    time_to_learn = 0
    relapses = 0
    everKnown = False
    isKnown = False
    consecutive_success = 0
    for review in entry['reviews']:
        if is_successful(review['grade']):
            if (not everKnown) and (time_to_learn < 1):
                everKnown = True
                isKnown = True
            elif (not everKnown) and (consecutive_success == 2):
                everKnown = True
                isKnown = True
                time_to_learn += 1
            elif (not everKnown):
                consecutive_success += 1
                time_to_learn += 1
            elif (not isKnown) and (consecutive_success == 2):
                isKnown = True
            elif not isKnown:
                consecutive_success += 1
        else:
            consecutive_success = 0
            if isKnown:
                isKnown = False
                relapses += 1
            if not everKnown:
                time_to_learn += 1
    return [[entry['spelling'], len(entry['reviews']), time_to_learn, relapses]]    
    





if __name__ == "__main__":
    app.run_server(debug=True)