import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load():
    df = pd.read_csv("data.csv", encoding = 'latin1' )
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df = df[df["Quantity"] > 0]
    return df


df = load()

country_sales = df.groupby("Country")["Revenue"].sum().reset_index()

fig = px.choropleth(
    country_sales,
    locations="Country",
    locationmode="country names",
    color="Revenue",
    color_continuous_scale="Blues",
    title="Global Revenue Heatmap"
)

fig.update_layout(
    height = 900,
    
    title=dict(
        text="🌍 Global Revenue Heatmap",
        x=0.5,
        xanchor="center",
        font=dict(size=24)
    ),
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="white",
        projection_type="natural earth",
        showland=True,
        landcolor="rgb(240,240,240)",
        showocean=True,
        oceancolor="rgb(220,235,255)",
        bgcolor="rgba(0,0,0,0)"
    ),
    margin=dict(l=0, r=0, t=60, b=0),
    coloraxis_colorbar=dict(
        title="Revenue",
        thickness=18
    ),
)

fig.update_traces(
    hovertemplate="<b>%{location}</b><br>Revenue: %{z:$,.0f}<extra></extra>"
)

st.plotly_chart(fig, use_container_width=True)

