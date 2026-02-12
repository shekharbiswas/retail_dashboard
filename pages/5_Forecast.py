import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet

st.title("📈 Sales Forecast")

@st.cache_data
def load():
    df = pd.read_csv("data.csv", encoding = 'latin1')
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df = df[df["Quantity"] > 0]
    return df

df = load()

# Daily revenue
daily = df.groupby(df["InvoiceDate"].dt.date)["Revenue"].sum().reset_index()
daily.columns = ["ds", "y"]

st.subheader("Historical Revenue")
st.line_chart(daily.set_index("ds"))

# Forecast horizon
days = st.slider("Forecast days", 30, 180, 90)

# Prophet model
model = Prophet()
model.fit(daily)

future = model.make_future_dataframe(periods=days)
forecast = model.predict(future)

# Plot forecast
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=daily["ds"],
    y=daily["y"],
    name="Actual"
))

fig.add_trace(go.Scatter(
    x=forecast["ds"],
    y=forecast["yhat"],
    name="Forecast"
))

fig.add_trace(go.Scatter(
    x=forecast["ds"],
    y=forecast["yhat_upper"],
    fill=None,
    mode="lines",
    line=dict(width=0),
    showlegend=False
))

fig.add_trace(go.Scatter(
    x=forecast["ds"],
    y=forecast["yhat_lower"],
    fill="tonexty",
    mode="lines",
    line=dict(width=0),
    name="Confidence Band"
))

st.plotly_chart(fig, use_container_width=True)

# Forecast KPI
future_sales = forecast.tail(days)["yhat"].sum()

st.metric("Projected Revenue (Forecast Period)", f"£{future_sales:,.0f}")

