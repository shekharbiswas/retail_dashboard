import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load():
    df = pd.read_csv("data.csv", encoding = 'latin1')
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df = df[df["Quantity"] > 0]
    return df

df = load()

product_perf = (
    df.groupby("Description")
    .agg({"Revenue": "sum", "Quantity": "sum"})
    .sort_values("Revenue", ascending=False)
    .head(20)
)

fig = px.bar(product_perf, x=product_perf.index, y="Revenue",
             title="Top Products")

st.plotly_chart(fig, use_container_width=True)
