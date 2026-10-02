import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="E-Commerce Analytics Dashboard", layout="wide")

st.markdown("""
    <style>
    .block-container {padding-top: 2rem;}
    .segment-badge {padding: 5px 12px; border-radius: 15px; font-size: 0.85rem;
                    font-weight: 600; display: inline-block; color: white;}
    </style>
    """, unsafe_allow_html=True)

SEGMENT_COLORS = {
    "Champions": "#10b981",
    "Loyal Customers": "#3b82f6",
    "Big Spenders": "#8b5cf6",
    "New Customers": "#06b6d4",
    "Regular": "#6b7280",
    "At Risk": "#f59e0b",
    "Lost Customers": "#ef4444",
}


@st.cache_data
def load_data():
    df = pd.read_csv("data.csv", encoding="latin1")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df[df["Quantity"] > 0]


def assign_rfm_segment(row):
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "New Customers"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f <= 2:
        return "Lost Customers"
    elif m >= 4:
        return "Big Spenders"
    return "Regular"


@st.cache_data
def calculate_rfm(df):
    snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("CustomerID").agg({
        "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
        "InvoiceNo": "nunique",
        "Revenue": "sum",
    })
    rfm.columns = ["Recency", "Frequency", "Monetary"]

    # rank(method="first") avoids duplicate bin edges in qcut
    rfm["R_Score"] = pd.qcut(rfm["Recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["Segment"] = rfm.apply(assign_rfm_segment, axis=1)
    return rfm


def chart(fig):
    st.plotly_chart(fig, width="stretch")


df = load_data()
monthly = df.set_index("InvoiceDate").resample("ME")["Revenue"].sum()
growth = monthly.pct_change() * 100

st.title("E-Commerce Analytics Dashboard")
st.markdown("---")

# ---------- Key metrics ----------
st.header("Key Performance Indicators")
total_revenue = df["Revenue"].sum()
total_orders = df["InvoiceNo"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"${total_revenue:,.0f}", f"{growth.iloc[-1]:.1f}% MoM")
c2.metric("Total Orders", f"{total_orders:,}")
c3.metric("Total Customers", f"{df['CustomerID'].nunique():,}")
c4.metric("Avg Order Value", f"${total_revenue / total_orders:.2f}")

st.markdown("---")

# ---------- Revenue ----------
st.header("Revenue & Growth Analytics")
col1, col2 = st.columns([2, 1])

with col1:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=monthly.index, y=monthly, name="Revenue", fill="tozeroy",
                             line=dict(color="#667eea", width=3),
                             fillcolor="rgba(102, 126, 234, 0.1)"), secondary_y=False)
    fig.add_trace(go.Bar(x=growth.index, y=growth, name="Growth %", opacity=0.7,
                         marker_color=["#10b981" if x > 0 else "#ef4444" for x in growth]),
                  secondary_y=True)
    fig.update_layout(title="Monthly Revenue Trend & Growth Rate", hovermode="x unified",
                      height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                              xanchor="right", x=1),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(title_text="Revenue ($)", secondary_y=False)
    fig.update_yaxes(title_text="Growth (%)", secondary_y=True, showgrid=False)
    chart(fig)

with col2:
    st.subheader("Revenue by Country")
    country = df.groupby("Country")["Revenue"].sum().nlargest(5)
    fig_pie = px.pie(values=country.values, names=country.index, hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
    fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20))
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    chart(fig_pie)

st.markdown("---")

# ---------- RFM ----------
st.header("Customer Intelligence & RFM Segmentation")
rfm = calculate_rfm(df)
counts = rfm["Segment"].value_counts()
seg_revenue = rfm.groupby("Segment")["Monetary"].sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Customer Segments")
    fig_seg = go.Figure(go.Pie(labels=counts.index, values=counts.values, hole=0.4,
                               marker=dict(colors=[SEGMENT_COLORS[s] for s in counts.index])))
    fig_seg.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    chart(fig_seg)

with col2:
    st.subheader("Segment Value")
    fig_val = px.bar(x=seg_revenue.index, y=seg_revenue.values, color=seg_revenue.index,
                     color_discrete_map=SEGMENT_COLORS,
                     labels={"x": "Segment", "y": "Total Revenue ($)"})
    fig_val.update_layout(height=300, showlegend=False, margin=dict(l=0, r=0, t=30, b=0),
                          xaxis_tickangle=-45)
    chart(fig_val)

with col3:
    st.subheader("Segment Metrics")
    for seg in ["Champions", "At Risk", "Lost Customers"]:
        if seg in counts.index:
            st.markdown(f"""
                <div style='padding:10px; margin:5px 0; background:#f9fafb; border-radius:8px;'>
                    <span class='segment-badge' style='background:{SEGMENT_COLORS[seg]}'>{seg}</span>
                    <div style='margin-top:5px; font-size:1.2rem; font-weight:bold; color:#1f2937;'>{counts[seg]:,} customers</div>
                    <div style='color:#6b7280; font-size:0.85rem;'>{counts[seg] / counts.sum() * 100:.1f}% of total</div>
                </div>""", unsafe_allow_html=True)

st.subheader("Detailed Customer Analysis")
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("##### Top 20 Customers by Value")
    top = rfm.sort_values("Monetary", ascending=False).head(20).reset_index()
    top.insert(0, "Rank", range(1, len(top) + 1))
    display_df = top[["Rank", "CustomerID", "Recency", "Frequency", "Monetary", "Segment"]].copy()
    display_df["CustomerID"] = display_df["CustomerID"].astype(int)
    display_df["Monetary"] = display_df["Monetary"].map("${:,.2f}".format)
    display_df.columns = ["Rank", "Customer ID", "Days Since Last Purchase",
                          "Total Orders", "Total Spent", "Segment"]
    st.dataframe(display_df, width="stretch", height=400, hide_index=True)

with col2:
    st.markdown("##### Segment Insights")
    champ = rfm[rfm["Segment"] == "Champions"]
    risk = rfm[rfm["Segment"] == "At Risk"]
    lost = rfm[rfm["Segment"] == "Lost Customers"]
    if len(champ):
        st.success(f"**Champions**  \n{len(champ):,} customers  \n"
                   f"Avg spend: ${champ['Monetary'].mean():,.2f}  \n"
                   f"Avg frequency: {champ['Frequency'].mean():.1f} orders")
    if len(risk):
        st.warning(f"**At Risk**  \n{len(risk):,} customers  \n"
                   f"Avg days inactive: {risk['Recency'].mean():.0f}  \n"
                   f"Recovery potential: ${risk['Monetary'].sum():,.2f}")
    if len(lost):
        st.error(f"**Lost Customers**  \n{len(lost):,} customers  \n"
                 f"Avg days inactive: {lost['Recency'].mean():.0f}  \n"
                 f"Lost value: ${lost['Monetary'].sum():,.2f}")

st.markdown("---")

# ---------- Products ----------
st.header("Product Performance Analysis")
col1, col2 = st.columns([2, 1])

product_perf = (df.groupby("Description").agg({"Revenue": "sum", "Quantity": "sum"})
                  .sort_values("Revenue", ascending=False).head(20))

with col1:
    fig_prod = go.Figure(go.Bar(
        y=product_perf.index, x=product_perf["Revenue"], orientation="h",
        marker=dict(color=product_perf["Revenue"], colorscale="Viridis", showscale=True,
                    colorbar=dict(title="Revenue")),
        text=[f"${x:,.0f}" for x in product_perf["Revenue"]], textposition="outside",
        customdata=product_perf["Quantity"],
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<br>Qty: %{customdata:,}<extra></extra>",
    ))
    fig_prod.update_layout(title="Top 20 Products by Revenue", height=600,
                           yaxis={"categoryorder": "total ascending"},
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           xaxis_title="Revenue ($)", showlegend=False, margin=dict(l=200))
    chart(fig_prod)

with col2:
    st.subheader("Product Stats")
    st.metric("Total Products", f"{df['Description'].nunique():,}")
    st.metric("Avg Revenue per Product", f"${df.groupby('Description')['Revenue'].sum().mean():,.2f}")
    st.markdown("---")
    st.markdown("##### Top Product")
    st.info(f"**{product_perf.index[0]}**  \n"
            f"Revenue: ${product_perf['Revenue'].iloc[0]:,.2f}  \n"
            f"Units sold: {product_perf['Quantity'].iloc[0]:,}")
    st.metric("Total Items Sold", f"{df['Quantity'].sum():,.0f}")
    st.metric("Avg Items/Order", f"{df.groupby('InvoiceNo')['Quantity'].sum().mean():.1f}")
