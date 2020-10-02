import pandas as pd
import numpy as np
import json
import os

#interpolation
import scipy.interpolate
import pykrige.kriging_tools as kt
from pykrige.ok import OrdinaryKriging

#dash
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

#mapbox token
token = 'pk.eyJ1Ijoicml0bWFuZG90cHkiLCJhIjoiY2s3ZHJidGt0MDFjNzNmbGh5aDh4dTZ0OSJ9.-SROtN91ZvqtFpO1nGPFeg'
mapbox_style="mapbox://styles/ritmandotpy/cke3b197900zr19oy9oh1curh"
mapbox_style_sat = "mapbox://styles/ritmandotpy/ckf2s0kv56oxm19os5sfh8lfy"

#reading the data
df = pd.read_csv("data/PERFILES CTDO PILPILEHUE.csv")

#stations mapbox
fig = go.Figure(data=go.Scattermapbox(
        lon=df["Longitud"].unique().round(2),
        lat=df["Latitud"].unique().round(2),
        text=df["Estación"].unique(), textposition="bottom right",
        mode="markers+text",
        customdata=df["Estación"].unique(),
        marker={"size":10, "symbol":["circle-stroked" for x in range(8)]}
        ))
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},clickmode='event+select',
                  mapbox= dict(style="light", center={"lat":-42.7,"lon":-73.5}, zoom=10, accesstoken=token))

#top-left point
NO = np.array([-73.6339, -42.6772])
#buttom-right point
SE = np.array([-73.4832, -42.7561])

diff = np.abs(NO-SE)
#the spacing between stations is nearby 0.15° in the x axis and 0.8° in the y axis.
#So I'm gonna interpolate in a 0.15x0.8  grid
xline = np.linspace(NO[0], SE[0], int(diff[0]/0.01))
yline = np.linspace(SE[1], NO[1], int(diff[1]/0.01))

#making the grid
grid_x,grid_y = np.meshgrid(xline, yline)
#krigging as a function
def kriging(depth, variable):
    dff2 = df[df["Profundidad"]== depth][[variable, "Latitud", "Longitud"]]
    #ordinary kriging
    ok= OrdinaryKriging(dff2["Longitud"], dff2["Latitud"], dff2[variable], variogram_model='linear',
                       verbose=False)
    z,ss = ok.execute('grid',xline,yline)
    return np.array(z)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
server = app.server
app.title = "OD analysis"

lore_ipsum = """Dashboard de variables oceanográficas: Oxígeno (mg/L, %sat y teórico), temperatura, salinidad,
                sigma-t (densidad del agua), AOU y fluorescencia cómo clorofila a. Mapa de estaciones, perfiles y
                cubo 3d para visualizar interactivamente los datos del área de estudio."""

lore_ipsum2 = """Haga clic en las estaciones para ver perfiles individuales o selecciones varios (herramienta seleccionar del mapa).
En el gráfico 3d seleccione la profundidad en la barra ubicada a la izquierda. """

def card_maker(card_text):
    """returns a dbc.Card its inpus are an id (string) and a
     list of text, the first item correspond to the header and every other
      item in the list will be an html.P paragraph"""
    return dbc.Card(
        dbc.CardBody(
            [
                html.P(card_text, className="card-text"),
                html.P(lore_ipsum2)
            ]
        ),
        className="mt-3",
    )

#first row card
oxigeno_mgl_tab = card_maker(lore_ipsum)
oxigeno_sat_tab = card_maker(lore_ipsum)
oxigeno_teo_tab = card_maker(lore_ipsum)
temperatura_tab = card_maker(lore_ipsum)
sigmat_tab = card_maker(lore_ipsum)
aou_tab = card_maker(lore_ipsum)
salinidad_tab = card_maker(lore_ipsum)
fluorescenia_tab = card_maker(lore_ipsum)

app.layout = dbc.Container(
                    [
                            html.H2("Análisis de oxígeno"),
                            html.H4("Centro Pilpilehue, Camanchaca S.A."),
                            dbc.Row(
                                dbc.Col([
                                    dbc.Card(
                                        dbc.CardHeader(
                                            [
                                                dbc.Tabs(
                                                    [
                                                        dbc.Tab(oxigeno_mgl_tab, label="Oxígeno mg/L", tab_id="oximgl-tab"),
                                                        dbc.Tab(oxigeno_sat_tab, label="Oxígeno %SAT", tab_id="oxisat-tab"),
                                                        dbc.Tab(oxigeno_teo_tab, label="Oxígeno teórico", tab_id="oxiteo-tab"),
                                                        dbc.Tab(temperatura_tab, label="Temperatura °C", tab_id="temp-tab"),
                                                        dbc.Tab(salinidad_tab, label="Salinidad PSU", tab_id="salin-tab"),
                                                        dbc.Tab(sigmat_tab, label="sigma-t", tab_id="sigmat-tab"),
                                                        dbc.Tab(aou_tab, label="AOU", tab_id="aou-tab"),
                                                        dbc.Tab(fluorescenia_tab, label="Fluorescencia", tab_id="fluo-tab")

                                                    ],
                                                    id="header-tab",
                                                    card=True,
                                                    active_tab="oximgl-tab"
                                                )
                                            ]
                                        )
                                    )
                                ], xl=12)
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Estaciones de perfiles CTD-O"),
                                                    dbc.CardBody(dcc.Graph(id="map", figure=fig,
                                                                            clickData={'points':[{"customdata": "E1"}]}
                                                                          )
                                                                )
                                                ]
                                            )
                                        ], xl=6, md=12
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader("Estaciones de perfiles CTD-O"),
                                                    dbc.CardBody(dcc.Graph(id="perfil-scatter"))
                                                ]
                                            )
                                        ], xl=6, md=12
                                    )
                                ], style={"margin-top":20}
                            ),
                            html.Hr(),
                            dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    [
                                                        html.Label("Profundidad", style={"margin-top":20, "margin-left":20}),
                                                        dcc.Slider(
                                                            id="depth-slider",
                                                            marks={i:{"label":str(i)+"m"} for i in range (-1, -80, -10)},
                                                            min=-80,
                                                            max=-1,
                                                            value=-1,
                                                            tooltip={"always_visible":False},
                                                            updatemode="drag",
                                                            vertical=True,
                                                            verticalHeight=600
                                                        ),
                                                    ]
                                                )
                                            ],
                                            xl=2, md=4, style={"height":"90vh", "margin-left":50, "margin-top":50}
                                        ),
                                        dbc.Col(
                                            [
                                                dcc.Graph(id="kriging-fig"),
                                            ],
                                            xl=4, md=12, style={"height":"100vh", "margin-left":50,"margin-top":50}
                                        )
                                    ]
                            )
                    ], fluid=True
)
#callbacks
#perfil scatter when selected
@app.callback(Output("perfil-scatter", "figure"),
             [Input("map", "selectedData"),
              Input("map", "clickData"),
              Input("header-tab", "active_tab")])
def perfiles_scatter_maker(selectedData, clickData, variable):
    if clickData['points'][0]["customdata"] in df["Estación"].unique() and selectedData == None:
        print(clickData)
        try:
            clickdata = clickData['points'][0]["customdata"]
        except:
            clickdata = clickData['points'][0]["text"]
        variable_dict = {"oximgl-tab":"Oxígeno (mg/L)",
                        "oxisat-tab":"Oxígeno (%Sat)",
                        "oxiteo-tab":"Oxígeno",
                        "temp-tab":"Temperatura",
                        "salin-tab":"Salinidad",
                        "sigmat-tab":"Densidad (sigma-t)",
                        "aou-tab":"AOU",
                        "fluo-tab":"Fluorescencia",
                        "sigma-t-tab":"Densidad (sigma-t)",
                        "aou-tab":"AOU"
                        }
        variable = variable_dict[variable]
        dff = df.loc[df["Estación"]==clickdata][[variable, "Profundidad"]]

        fig2d = go.Figure(data=go.Scatter(x=dff[variable],
                                          y=dff["Profundidad"],
                                          mode="markers+lines"))
        fig2d.update_layout(title=f"Perfil de {variable}: {clickdata}", margin={"r":0,"t":30,"l":0,"b":0},
                            xaxis_title=variable, yaxis_title="Profundidad")
        fig2d.update_xaxes(range=[df[variable].min(), df[variable].max()])
        return fig2d

    if selectedData != None:
        try:
            selected = selectedData['points'][0]["customdata"]
        except:
            selected = selected['points'][0]["text"]
        variable_dict = {"oximgl-tab":"Oxígeno (mg/L)",
                        "oxisat-tab":"Oxígeno (%Sat)",
                        "oxiteo-tab":"Oxígeno",
                        "temp-tab":"Temperatura",
                        "salin-tab":"Salinidad",
                        "sigmat-tab":"Densidad (sigma-t)",
                        "aou-tab":"AOU",
                        "fluo-tab":"Fluorescencia",
                        "sigma-t-tab":"Densidad (sigma-t)",
                        "aou-tab":"AOU"
                        }
        variable = variable_dict[variable]
        dff = df.loc[df["Estación"].isin([selected])][[variable, "Profundidad"]]

        fig2d = go.Figure(data=go.Scatter())
        title = []
        for point in selectedData['points']:
            point = point["customdata"]
            title.append(point)#the title of the graph
            tdf = df.loc[df["Estación"]==point][[variable, "Profundidad"]]
            fig2d.add_trace(go.Scatter(x=tdf[variable], y=tdf["Profundidad"], mode="markers+lines", name=point))
        fig2d.update_layout(title=f"Perfil(es) de {variable}: {' ,'.join(title)}", margin={"r":0,"t":30,"l":0,"b":0},
                            xaxis_title=variable, yaxis_title="Profundidad"
                            )
        fig2d.update_xaxes(range=[df[variable].min(), df[variable].max()])
        return fig2d

#kriging callback
@app.callback(Output("kriging-fig","figure"),
              [Input("depth-slider","value"),
               Input("header-tab","active_tab")])
def kriging_fig_maker(value, variable):
    variable_dict = {"oximgl-tab":"Oxígeno (mg/L)",
                    "oxisat-tab":"Oxígeno (%Sat)",
                    "oxiteo-tab":"Oxígeno",
                    "temp-tab":"Temperatura",
                    "salin-tab":"Salinidad",
                    "sigmat-tab":"Densidad (sigma-t)",
                    "aou-tab":"AOU",
                    "fluo-tab":"Fluorescencia",
                    "sigma-t-tab":"Densidad (sigma-t)",
                    "aou-tab":"AOU"
                    }
    variable = variable_dict[variable]
    #add profiles as traces
    def add_traces(estacion, fig, variable):
        dff = df.loc[(df["Estación"]==estacion)&(df["Profundidad"]>=-80)]
        return fig.add_trace(go.Scatter3d(x=dff["Longitud"], y=dff["Latitud"], z=dff[variable], mode="lines", name=estacion,
                                         hovertemplate= 'Latitud: %{y:.2f} <br> Longitud: %{x:.2f} <br> z: %{z:.2f}'))

    krig_fig = go.Figure([
                              go.Surface(x=grid_x, y=grid_y, z=kriging(value, variable),
                              cmax=df[variable].mean()+(df[variable].std()*2),
                              cmin=df[variable].mean()-(df[variable].std()*2),
                              colorscale="RdBu" if variable !="Temperatura" else "RdBu_r",
                              uirevision=True,
                              hovertemplate= 'Latitud: %{y:.2f} <br> Longitud: %{x:.2f} <br> z: %{z:.2f}',
                              )
                          ], layout=go.Layout(uirevision=True))

    #adding the traces
    krig_fig.add_trace(go.Scatter3d(x=[-73.608872], y=[-42.724906], z=[df.loc[df["Estación"]=="E5"][variable].mean()],
                                    name="CENTRO", mode="markers",
                                    hovertemplate= 'Latitud: %{y:.2f} <br> Longitud: %{x:.2f} <br> z: %{z:.2f}'))
    add_traces("E1", krig_fig, variable)
    add_traces("E2", krig_fig, variable)
    add_traces("E3", krig_fig, variable)
    add_traces("E4", krig_fig, variable)
    add_traces("E5", krig_fig, variable)
    add_traces("E6", krig_fig, variable)
    add_traces("E7", krig_fig, variable)
    add_traces("E8", krig_fig, variable)
    krig_fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0},
                           legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01
                            ),
                            title=f"{variable} a los {value} metros",
                            width=900,
                            height=600,
                            scene=dict(
                                zaxis=dict(title=variable),
                                xaxis=dict(title="Longitud"),
                                yaxis=dict(title="Latitud"),
                                aspectratio=dict(x=1, y=1, z=1),
                                ),
                    )
    return krig_fig
if __name__ == '__main__':
    app.run_server(debug=True)
