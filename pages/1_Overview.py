import plotly.graph_objects as go
import pandas as pd
import streamlit as st

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

monthly = df.set_index("InvoiceDate").resample("M")["Revenue"].sum()
growth = monthly.pct_change() * 100


fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly.index, y=monthly, name="Revenue"))
fig.add_trace(go.Bar(x=growth.index, y=growth, name="Growth %"))

st.subheader("Monthly Growth Analytics")
st.plotly_chart(fig, use_container_width=True)
