from flask import render_template, request
from flask import current_app as app
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go

from app.modeling.farsite import burn

token = open("app/static/.mapbox_token").read()
px.set_mapbox_access_token(token)


@app.route("/", methods=["POST", "GET"])
def index():

    if request.method == "GET":
        #
        # load homepage
        # render toggleable layer scatterplot from downsampled netcdf
        # https://community.plotly.com/t/adding-multiple-layers-in-mapbox/25408
        # https://plotly.com/python/custom-buttons/
        #
        # import data and scale to appropriate values
        df = pd.read_csv("app/data/farsite_lonlat_low_risk_pop_housing.csv")
        df["Risk"] /= df["Risk"].max()

        # add fake temperature, humidity, wind speed, wind direction data
        df["Temperature"] = (1 - df["US_DEM"])
        df["Humidity"] = df["Temperature"]
        df["WindSpeed"] = df["US_DEM"]
        df["WindDirection"] = df["US_ASP"]

        # generate layout for Plotly
        layout = go.Layout(mapbox=dict(accesstoken=token, center=dict(lat=df["y"].mean(), lon=df["x"].mean()), zoom=8),
                           height=1000, margin=dict(l=10, r=10, b=10, t=10))
        layout.update(mapbox_style="satellite-streets",
                      coloraxis_colorbar={"yanchor": "top", "y":1, "x":0, "ticks":"outside"})


        # load data
        data = []
        # display_columns = ["US_210CBD", "US_210CBH", "US_210CC", "US_210CH", "US_210EVC", "US_210EVH", "US_210F40",
        #                    "US_210FVC", "US_210FVH", "US_210FVT", "US_ASP", "US_DEM", "US_FDIST", "US_SLP", "RISK", "FIRE"]
        display_columns = ["Risk", "Population", "Housing", "Temperature", "Humidity", "WindSpeed", "WindDirection"]
        for column in display_columns:
            data.append(
                go.Scattermapbox(lat=df["y"], lon=df["x"], mode="markers", opacity=0.1, visible=False,
                                 marker=dict(
                                     size=8,
                                     # colorscale="viridis",
                                     color=df[column],
                                     colorbar_title=column,
                                     colorbar=dict(
                                         titleside="right",
                                     )
                                 ),
                                 hovertemplate=f"{column}: " + "%{marker.color}<br>" +
                                               "Latitude: %{lat}<br>" +
                                               "Longitude: %{lon}<br>" +
                                               "<extra></extra>",
                                 )
            )
        data[0].visible = True

        # Create button list
        buttons = []
        for i, item in enumerate(display_columns):
            visibility = [False] * len(display_columns)
            visibility[i] = True
            buttons.append(dict(
                args=["visible", visibility],
                label=item,
                method="restyle"
            ))

        # Add mapbox and dropdown
        # layout.update(
        #     updatemenus=[
        #         dict(
        #             buttons=buttons,
        #             direction="down",
        #             pad={"r": 10, "t": 10},
        #             showactive=True,
        #             x=0.1,
        #             xanchor="left",
        #             y=1.08,
        #             yanchor="top"
        #         ),
        #     ]
        # )

        # Add annotation
        # layout.update(
        #     annotations=[
        #         dict(text="Data Layer:", showarrow=False, x=0, y=1.05, yref="paper", align="left")
        #     ]
        # )

        fig = go.Figure(data=data, layout=layout)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("index.html", graph_json=graph_json, impacts=False)

    if request.method == "POST":
        #
        # run simulation and render output
        #
        form_data = request.form
        # df = burn(lat=float(form_data["lat"]), lon=float(form_data["lon"]),
        #           path_farsite="application/static/farsite.nc", path_fueldict="application/static/FUEL_DIC.csv", mins=500)
        df = burn(lat=float(form_data["lat"]), lon=float(form_data["lon"]), mins=50)

        # generate layout for Plotly
        layout = go.Layout(mapbox=dict(accesstoken=token, center=dict(lat=df["y"].mean(), lon=df["x"].mean()), zoom=12),
                           height=1000, margin=dict(l=10, r=10, b=10, t=10))
        layout.update(mapbox_style="satellite-streets")

        # load data
        data = []
        data.append(
            go.Scattermapbox(lat=df["y"], lon=df["x"], mode="markers", opacity=0.5, visible=True,
                             marker=dict(
                                 size=8,
                                 color="orange",
                             ),
                             hovertemplate=f"Fire<br>" +
                                           "Latitude: %{lat}<br>" +
                                           "Longitude: %{lon}<br>" +
                                           "<extra></extra>",
                             )
        )
        fig = go.Figure(data=data, layout=layout)
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("index.html", graph_json=graph_json, impacts=True)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/problem")
def problem():
    return render_template("problem.html")


@app.route("/resources")
def resources():
    return render_template("resources.html")


@app.route("/solution")
def solution():
    return render_template("solution.html")


@app.route("/prototyping/", methods=["POST", "GET"])
def prototyping():
    if request.method == "GET":
        return f"The URL /data is accessed directly. Try going to '/form' to submit form"
    if request.method == "POST":
        form_data = request.form
        return render_template("prototyping.html", form_data=form_data)
