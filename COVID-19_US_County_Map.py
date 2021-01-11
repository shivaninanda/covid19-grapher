import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

#df1 = pd.read_csv('/Users/shivaninanda/Desktop/COVID_Grapher/setup.csv')
#df2 = pd.read_csv("/Users/shivaninanda/Desktop/COVID_Grapher/us-counties.csv")
#df3 = pd.read_csv('/Users/shivaninanda/Desktop/COVID_Grapher/clusterNums.csv')

available_indicators1 = ["Maryland", "Virginia", "Pennsylvania",
                         "Delaware", "New Jersey", "New York"]
#available_indicators1 = df1['SDS'].unique()
available_indicators2 = range(2, 16)
#available_indicators2 = df3['ClusterNum'].unique()

df2 = pd.read_csv('./daily_cases_data.csv')

app.title = 'COVID-19 Clustering App'

app.layout = html.Div([
    html.Div([
        html.Center(html.H1("COVID-19 US County Map"))
    ]),
    html.Div([
        html.Div(
            [
                dcc.Dropdown(
                    id='sds',
                    options=[{'label': i, 'value': i} for i in available_indicators1],
                    value='Maryland'
                )
            ], 
            style={'width': '25%', 'display': 'inline-block'}
        ),
        dcc.Graph(id='covid_graph'),        
    ]),
    html.Div([

        html.Div(
            [
                dcc.Dropdown(
                    id='clusterNum',
                    options=[{'label': i, 'value': i} for i in available_indicators2],
                    value='2'
                )
            ],
            style={'width': '25%', 'display': 'inline-block'}
        ),
        dcc.Graph(id='cluster_graph'),
        dcc.Graph(id='cluster_trend')
    ])
])

@app.callback(
    Output('cluster_graph', 'figure'),
    Output('cluster_trend', 'figure'),
    [Input('sds', 'value'), Input('clusterNum', 'value')])

def clusters(sds, clusterNum):

    filtered_df = df2.query("state == @sds")
    cluster_df = filtered_df.pivot(
        index = 'county', 
        columns = 'date', 
        values = 'daily_cases_rate').sort_index()
    cluster_df = cluster_df.fillna(0)
    
    cluster_data = cluster_df.to_numpy()
    clusterer = KMeans(n_clusters=int(clusterNum), random_state=10)
    cluster_labels = clusterer.fit_predict(cluster_data)
    #silhouette_avg = silhouette_score(cluster_data, cluster_labels)

    latest_date = filtered_df.date.max()
    latest_cases_and_deaths = filtered_df.loc[filtered_df.date == latest_date]
    latest_cases_and_deaths = latest_cases_and_deaths.sort_values('county')
    #print(latest_cases_and_deaths)
    latest_cases_and_deaths['Cluster'] = cluster_labels.astype('string')
    fig = px.scatter(
        latest_cases_and_deaths, 
        x = 'cases', y = 'deaths', color = 'Cluster', 
        hover_data = ['county']
    )
    fig.update_xaxes(title_text = 'Cumulative Cases')
    fig.update_yaxes(title_text = 'Cumulative Deaths')

    cluster_label_df = pd.DataFrame({'cluster' : cluster_labels}, index = cluster_df.index)
    data_with_cluster = filtered_df.merge(cluster_label_df, 'left', left_on = 'county', right_index = True)
    daily_data_with_cluster = data_with_cluster.groupby(["date", "cluster"], as_index = False).agg({"daily_cases": "sum"})
    print(daily_data_with_cluster)
    trend_fig = px.line(
        daily_data_with_cluster, x = 'date', y = 'daily_cases',
        color = 'cluster', line_group = 'cluster'
    )
    trend_fig.update_xaxes(title_text = 'Date')
    trend_fig.update_yaxes(title_text = 'COVID-19 Cases')
    return (fig, trend_fig)


    # print(cluster_labels)
    # labels = cluster_labels.tolist()
    # labels = pd.Series(labels,name='labels')
    # #print(labels)
    # values = pd.value_counts(labels)
    # cluster_df["Cluster"] = cluster_labels
    # #print(cluster_data)
    # return(repr(values)).replace(' ', '\t').replace('\n', '  \n')

@app.callback(
    Output('covid_graph', 'figure'),
    [Input('sds', 'value')])

def update_figure(sds):
    filtered_df = df2.query("state == @sds")
    filtered_df = filtered_df.groupby("date", as_index = False).agg(
      # Sum of new cases/deaths in all counties within state
      {"daily_deaths": "sum", "daily_cases": "sum"}
    )
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(x=filtered_df['date'], y=filtered_df['daily_cases'], mode = "lines", name = "New Cases"),
    )
    fig.add_trace(
        go.Scatter(x=filtered_df['date'], y=filtered_df['daily_deaths'], mode = "lines", name = "New Deaths"),
    )

    fig.update_xaxes(title_text = 'Date')
    fig.update_yaxes(title_text = 'COVID-19 Cases & Deaths')
    return fig

if __name__ == '__main__':
    app.run_server()