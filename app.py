import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Bangladesh Social Data Atlas",
    page_icon="🇧🇩",
    layout="wide",
)

DATA_PATH = Path("data/bangladesh_social_indicators_2019.csv")
GEOJSON_PATH = Path("data/bangladesh_districts.geojson")

st.title("🇧🇩 Bangladesh Social Data Atlas")
st.caption(
    "Exploring district-level patterns in child marriage and participation in organized learning"
)

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

@st.cache_data
def load_geojson():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    def signed_area(ring):
        return 0.5 * sum(
            ring[i][0] * ring[(i + 1) % len(ring)][1]
            - ring[(i + 1) % len(ring)][0] * ring[i][1]
            for i in range(len(ring))
        )

    def orient_ring(ring, clockwise):
        area = signed_area(ring)

        if clockwise and area > 0:
            return list(reversed(ring))

        if not clockwise and area < 0:
            return list(reversed(ring))

        return ring

    for feature in geojson["features"]:
        geometry = feature["geometry"]

        if geometry["type"] == "Polygon":
            rings = geometry["coordinates"]

            # Exterior clockwise, holes counter-clockwise
            rings[0] = orient_ring(rings[0], clockwise=True)

            for i in range(1, len(rings)):
                rings[i] = orient_ring(rings[i], clockwise=False)

        elif geometry["type"] == "MultiPolygon":
            for polygon in geometry["coordinates"]:
                # Exterior clockwise, holes counter-clockwise
                polygon[0] = orient_ring(polygon[0], clockwise=True)

                for i in range(1, len(polygon)):
                    polygon[i] = orient_ring(polygon[i], clockwise=False)

    return geojson

def norm_name(x):
    if x is None:
        return ""
    s = str(x).strip().lower()
    aliases = {
        "barisal": "barishal",
        "chittagong": "chattogram",
        "comilla": "cumilla",
        "jessore": "jashore",
        "bogra": "bogura",
        "khagrachari": "khagrachhari",
        "chandpur": "chandpur",
        "cox's bazar": "cox's bazar",
        "cox’s bazar": "cox's bazar",
        "coxs bazar": "cox's bazar",
        "netrokona": "netrakona",
        "jhalokathi": "jhalokati",
        "chapainawabganj": "chapainababganj",
    }
    return aliases.get(s, s)

def find_name_property(geojson, candidates=None):
    candidates = candidates or [
    "adm2_name",
    "NAME_2",
    "name",
    "NAME_2_EN",
    "ADM2_EN",
    "district",
    "District",
    "shapeName",
    "NAME"
]
    features = geojson.get("features", [])
    if not features:
        raise ValueError("GeoJSON has no features.")
    props = features[0].get("properties", {})
    for c in candidates:
        if c in props:
            return c
    # Fall back to a string-valued property containing a district-like name.
    for k, v in props.items():
        if isinstance(v, str) and v:
            return k
    raise ValueError("Could not identify a district-name property in the GeoJSON.")

def attach_values(geojson, df, value_col):
    name_prop = find_name_property(geojson)
    lookup = dict(zip(df["district_norm"], df[value_col]))
    gj = json.loads(json.dumps(geojson))
    for feature in gj["features"]:
        props = feature.setdefault("properties", {})
        district = norm_name(props.get(name_prop))
        props["district"] = district
        props["value"] = lookup.get(district, None)
    return gj

df = load_data()
df["district_norm"] = df["district"].map(norm_name)

missing = []
if not DATA_PATH.exists():
    st.error("Data CSV is missing.")
    st.stop()
if not GEOJSON_PATH.exists():
    st.error(
        "GeoJSON is missing. Download a Bangladesh ADM2/district GeoJSON and save it as "
        "`data/bangladesh_districts.geojson`."
    )
    st.stop()

geojson = load_geojson()

indicator_labels = {
    "organized_learning_2019_direct_pct": "Participation in organized learning (%)",
    "child_marriage_before_18_2019_direct_pct": "Women 20–24 married before 18 (%)",
}

choice = st.sidebar.radio(
    "Map",
    list(indicator_labels.keys()),
    format_func=lambda x: indicator_labels[x],
)

min_v = float(df[choice].min())
max_v = float(df[choice].max())

map_geojson = attach_values(geojson, df, choice)

fig = go.Figure(
    go.Choropleth(
        geojson=map_geojson,
        locations=df["district_norm"],
        z=df[choice],
        featureidkey="properties.district",
        colorscale="YlOrRd",
        zmin=min_v,
        zmax=max_v,
        marker_line_width=0.5,
        colorbar_title=indicator_labels[choice],
        customdata=df[
            [
                "district",
                "organized_learning_2019_direct_pct",
                "child_marriage_before_18_2019_direct_pct",
            ]
        ],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Organized learning: %{customdata[1]:.1f}%<br>"
            "Child marriage before 18: %{customdata[2]:.1f}%"
            "<extra></extra>"
        ),
    )
)

fig.update_geos(
    fitbounds="locations",
    visible=False,
    bgcolor="rgba(0,0,0,0)",
)
fig.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    height=650,
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("### What the map shows")
if choice == "child_marriage_before_18_2019_direct_pct":
    st.write(
        "The indicator is the percentage of women aged 20–24 who were first married "
        "before age 18, using the direct district estimates from MICS 2019."
    )
else:
    st.write(
        "The education indicator is participation in organized learning, using the "
        "direct district estimates from MICS 2019. This is an early-childhood/entry-age "
        "education indicator, not a general literacy rate."
    )

st.divider()
st.subheader("The relationship between the two indicators")

corr = df[
    ["organized_learning_2019_direct_pct",
     "child_marriage_before_18_2019_direct_pct"]
].corr().iloc[0, 1]

x = df["organized_learning_2019_direct_pct"].to_numpy()
y = df["child_marriage_before_18_2019_direct_pct"].to_numpy()
slope, intercept = np.polyfit(x, y, 1)

scatter = px.scatter(
    df,
    x="organized_learning_2019_direct_pct",
    y="child_marriage_before_18_2019_direct_pct",
    hover_name="district",
    labels={
        "organized_learning_2019_direct_pct": "Organized learning (%)",
        "child_marriage_before_18_2019_direct_pct": "Child marriage before 18 (%)",
    },
)
scatter.add_scatter(
    x=np.linspace(x.min(), x.max(), 100),
    y=slope * np.linspace(x.min(), x.max(), 100) + intercept,
    mode="lines",
    name="Linear trend",
)
scatter.update_layout(height=500)
st.plotly_chart(scatter, use_container_width=True)

st.metric("Pearson correlation", f"{corr:.2f}")

st.warning(
    "This is an exploratory district-level association, not a causal relationship. "
    "The two indicators are measured at the area level and do not establish that "
    "education participation causes child marriage to rise or fall."
)

st.divider()
st.subheader("District ranking")

rank_metric = st.selectbox(
    "Rank districts by",
    list(indicator_labels.keys()),
    format_func=lambda x: indicator_labels[x],
)

ascending = rank_metric == "organized_learning_2019_direct_pct"
ranked = df[["district", rank_metric]].sort_values(
    rank_metric, ascending=ascending
).copy()
ranked[rank_metric] = ranked[rank_metric].round(1)

st.dataframe(
    ranked,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Source: Bangladesh Bureau of Statistics (BBS) and UNICEF Bangladesh, "
    "Small Area Estimation: Upazila Level Prevalence of Participation in Organized "
    "Learning and Child Marriage in Bangladesh, April 2024, based on MICS 2019."
)
