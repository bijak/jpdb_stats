import pandas as pd
import plotly.graph_objects as go

def gen_cum_daily_plot(dataframe, type, unit, rolling=False, template='plotly_dark'):
    idx = pd.date_range(dataframe.index.min(), dataframe.index.max())
    dataframe.index = pd.DatetimeIndex(dataframe.index)
    dataframe = dataframe.reindex(idx, fill_value=0)
    dataframe_cum = dataframe.cumsum()
    # Cum. Plot
    f_cum = dataframe_cum.plot()
    f_cum.update_layout(
        title=f"{type} (Cum.)",
        yaxis_title=f"Total {unit}",
        xaxis_title="Date",
        template=template
    )
    # Daily Plot
    f_daily = dataframe.plot(kind="bar")
    if rolling:
        rolling_df = dataframe.rolling(7).mean()
        f_daily.add_trace(
        go.Scatter(
            name="Rolling Average",
            x=rolling_df.index,
            y=rolling_df["Count"]
        ))
    f_daily.update_layout(
        title=f"{type} (Daily)",
        yaxis_title=f"Daily {unit}",
        xaxis_title="Date",
        template=template
    )
    return f_cum, f_daily

def gen_retention_plot(dataframe, type, template='plotly_dark'):
    idx = pd.date_range(dataframe.index.min(), dataframe.index.max())
    dataframe.index = pd.DatetimeIndex(dataframe.index)
    dataframe = dataframe.reindex(idx, fill_value=0)
    dataframe['Retention'] = 100 * dataframe['Passed'] / (dataframe['Passed'] + dataframe['Failed'])
    window_df = dataframe.rolling(7).sum()
    dataframe['Rolling Average'] = 100 * window_df['Passed'] / (window_df['Passed'] + window_df['Failed'])
    f_retention = dataframe.plot(y='Retention', kind='bar')
    f_retention.add_trace(
        go.Scatter(
            name="Rolling Average",
            x=dataframe.index,
            y=dataframe["Rolling Average"]
        ))
    f_retention.update_layout(
        title=f"Retention ({type})",
        yaxis_title="Retention (%)",
        xaxis_title="Date",
        template=template
    )
    return f_retention

def plot_reps(rep, template='plotly_dark'):
    reviews = pd.DataFrame(rep, columns=['Date'])
    reviews['Count'] = 1
    reviews_minute = pd.DataFrame(rep, columns=['Date'])
    reviews_minute["Count"] = 1
    reviews = reviews.groupby(pd.Grouper(key="Date", freq='1D')).sum()
    reviews_minute = reviews_minute.groupby(pd.Grouper(key="Date", freq='1Min')).sum()

    f_rc, f_rd = gen_cum_daily_plot(reviews, "Repetitions", "repetitions", rolling=True)
    # Time spent
    reviews_minute.index = pd.DatetimeIndex(reviews_minute.index)
    reviews_minute["Count"] = reviews_minute['Count'].where(reviews_minute['Count'] == 0, 1)
    reviews_minute = reviews_minute.groupby(pd.Grouper(freq='D')).sum()
    
    fm_rc, fm_rd = gen_cum_daily_plot(reviews_minute, "Time Spent", "time (minutes)", rolling=True)
    

    return f_rc, f_rd, fm_rc, fm_rd

def plot_history(history, template='plotly_dark'):
    history_df = (pd.DataFrame(history, columns=['Date', 'Failed', 'Passed', 'New', 'Abandoned', 'Known'])).drop(['Known'], axis=1)
    history_df = history_df.groupby('Date').sum()
    idx = pd.date_range(history_df.index.min(), history_df.index.max())
    history_df.index = pd.DatetimeIndex(history_df.index)
    history_df = history_df.reindex(idx, fill_value=0)
    colors = ['#EF553B','#00CC96','#636EFA', '#D3D3D3']
    f_history = history_df.plot(kind='bar', color_discrete_sequence=colors)
    f_history.update_layout(
        title="Cards (Daily)",
        yaxis_title="Card Count",
        xaxis_title="Date",
        template=template
    )
    return f_history

def plot_retention(history, template='plotly_dark'):
    retention_df = pd.DataFrame(history, columns=['Date', 'Failed', 'Passed', 'New', 'Abandoned', 'Known'])
    retention_known_df = retention_df[retention_df['Known']==True].groupby('Date').sum()
    retention_learning_df = retention_df[retention_df['Known']==False].groupby('Date').sum()
    
    known_plot = gen_retention_plot(retention_known_df, 'Known', template)
    learning_plot = gen_retention_plot(retention_learning_df, 'Learning', template)

    return known_plot, learning_plot

def plot_new(new_in, template='plotly_dark'):
    new = pd.DataFrame(new_in, columns=['Date'])
    new['Count'] = 1
    new = new.groupby('Date').sum()

    f_nc, f_nd = gen_cum_daily_plot(new, "New Cards", "new cards added", rolling=True)

    return f_nc, f_nd