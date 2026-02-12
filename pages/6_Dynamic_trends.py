import streamlit as st
import pandas as pd
import plotly.express as px

st.title(" Animated Sales Evolution ")

@st.cache_data
def load():
    df = pd.read_csv("data.csv", encoding = 'latin1')
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df = df[df["Quantity"] > 0]
    return df

df = load()

# Monthly aggregation by country
df["Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)

animated = (
    df.groupby(["Month", "Country"])["Revenue"]
    .sum()
    .reset_index()
)

fig = px.bar(
    animated,
    x="Country",
    y="Revenue",
    color="Country",
    animation_frame="Month",
    animation_group="Country",
    range_y=[0, animated["Revenue"].max()],
    title="Monthly Sales Animation by Country"
)

st.plotly_chart(fig, use_container_width=True)
