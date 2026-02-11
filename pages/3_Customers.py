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


snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = df.groupby("CustomerID").agg({
    "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
    "InvoiceNo": "count",
    "Revenue": "sum"
})

rfm.columns = ["Recency", "Frequency", "Monetary"]

st.title("Customer RFM Segmentation")
st.dataframe(rfm.head())

st.write("High value customers:")
st.dataframe(rfm.sort_values("Monetary", ascending=False).head(10))

