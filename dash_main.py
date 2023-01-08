import datetime
import json
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, no_update

from log_usecase import LogUsecase

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="IIDX Home Analyzer"
)
log_usecase = LogUsecase()


player_layout = html.Div([
    dbc.Navbar([
            dbc.NavItem([
                dbc.Input(id="player-id", placeholder="Player ID", type="text")
            ])
        ],
        style={"padding": "0.5rem 1rem"}
    ),
    html.Div(id="player-play-time"),
    dbc.Table([html.Tbody(id="player-play-date")])
])

@app.callback(
    Output("player-play-time", "children"),
    Input("player-id", "value")
)
def play_time(value):
    if value == None:
        return
    data = log_usecase.get_playtime(value)
    fig = go.Figure(go.Scatter(
        x=[datetime.datetime(2022,1,1) + t for t in data.keys()],
        y=list(data.values()),
        hovertemplate="<b>%{x|%H:%M}</b><br>%{y} times<extra></extra>"
    ))
    fig.update_xaxes(tickformat="%H:%M")
    fig.update_layout(hovermode="x")
    return dcc.Graph(figure=fig)

@app.callback(
    Output("player-play-date", "children"),
    Input("player-id", "value")
)
def play_date(value):
    if value == None:
        return
    data = log_usecase.get_all_playdate(value)
    header = [
        html.Thead(html.Tr([html.Th("date")]))
    ]
    body = list(map(lambda d: html.Tr([html.Td(d)]), data))
    return header + body


date_layout = html.Div([
    dbc.Navbar(
        [
            dbc.NavItem(
                dcc.DatePickerSingle(
                    id='date-input',
                    initial_visible_month=datetime.datetime.now().date()
                )
            )
        ],
        style={"padding": "0.5rem 1rem"}
    ),
    html.Div(id="date-headcounts"),
    dcc.Tooltip(id="date-headcounts-tooltip"),
    dcc.Store(id="date-headcounts-players-store")
])

@app.callback(
    Output("date-headcounts", "children"),
    Output("date-headcounts-players-store", "data"),
    Input("date-input", "date")
)
def date_headcounts(date_iso):
    if date_iso == None:
        return None, None
    date = datetime.date.fromisoformat(date_iso)
    data = log_usecase.get_players_over_time(date)
    # plotlyが勝手にdatetimeのxaxisのフォーマットを変えるので合わせる必要がある
    data = dict(zip(
        map(lambda dt: dt.isoformat(sep=" ", timespec="minutes"), data.keys()),
        map(list, data.values())
    ))
    xs = list(data.keys())
    ys = list(map(len, data.values()))
    fig = go.Figure(go.Scatter(
        x=xs,
        y=ys
    ))
    fig.update_layout(hovermode="x")
    #fig.update_xaxes(range=[xs[0], xs[-1]])
    return dcc.Graph(figure=fig, id="date-headcounts-graph"), json.dumps(data)

@app.callback(
    Output("date-headcounts-tooltip", "show"),
    Output("date-headcounts-tooltip", "bbox"),
    Output("date-headcounts-tooltip", "children"),
    Input("date-headcounts-graph", "hoverData"),
    Input("date-headcounts-players-store", "data")
)
def date_headcounts_tooltip(hoverData, data):
    if hoverData is None:
        return False, no_update, no_update
    pt = hoverData["points"][0]
    data = json.loads(data)
    bbox = pt["bbox"]
    players = list(map(lambda p: p[0], data[pt["x"]]))
    children = [
        html.Div([
            html.P(p) for p in players
        ], style={'width': '200px', 'white-space': 'normal'})
    ]

    return True, bbox, children


stats_layout = html.Div([
    dbc.Container(
        [
            html.H1("Weekday Average"),
            dbc.RadioItems(
                id="stats-weekday-radio",
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
                options=[
                    {"label": "Mon", "value": 0},
                    {"label": "Tue", "value": 1},
                    {"label": "Wed", "value": 2},
                    {"label": "Thu", "value": 3},
                    {"label": "Fri", "value": 4},
                    {"label": "Sat", "value": 5},
                    {"label": "Sun", "value": 6},
                ],
                value=0
            ),
            dcc.Graph(id="stats-weekday-headcounts")
        ],
        fluid=True
    )
])

@app.callback(
    Output("stats-weekday-headcounts", "figure"),
    [Input("stats-weekday-radio", "value")]
)
def stats_weekday_average(value):
    data = log_usecase.get_headcounts_average_weekday(value)
    fig = go.Figure(go.Scatter(
        x=[datetime.datetime(2022,1,1) + t for t in data.keys()],
        y=list(data.values()),
        hovertemplate="<b>%{x|%H:%M}</b><br>%{y} times<extra></extra>"
    ))
    fig.update_xaxes(tickformat="%H:%M")
    fig.update_layout(hovermode="x")
    return fig


navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Player", href="/player")),
        dbc.NavItem(dbc.NavLink("Date", href="/date")),
        dbc.NavItem(dbc.NavLink("Stats", href="/stats")),
    ],
    id="navbar",
    brand="IIDX Home Analyzer",
    links_left=True,
    color="dark",
    dark=True
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(
        id="page-content",
        style={"width":"100%","height":"100%"}
    )
])

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def router(pathname):
    match pathname:
        case "/" | "/player": return player_layout
        case "/date": return date_layout
        case "/stats": return stats_layout
        case _ : return 'Not found'

if __name__ == "__main__":
    app.run_server(debug=True)