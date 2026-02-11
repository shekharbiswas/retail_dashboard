import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .segment-badge {
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .champions {
        background-color: #10b981;
        color: white;
    }
    .loyal {
        background-color: #3b82f6;
        color: white;
    }
    .at-risk {
        background-color: #f59e0b;
        color: white;
    }
    .lost {
        background-color: #ef4444;
        color: white;
    }
    h1 {
        color: #1f2937;
        font-weight: 700;
    }
    h2, h3 {
        color: #374151;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv", encoding='latin1')
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df = df[df["Quantity"] > 0]
    return df

def assign_rfm_segment(row):
    """Assign customer segment based on RFM scores"""
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3 and m >= 3:
        return 'Loyal Customers'
    elif r >= 4 and f <= 2:
        return 'New Customers'
    elif r <= 2 and f >= 3:
        return 'At Risk'
    elif r <= 2 and f <= 2:
        return 'Lost Customers'
    elif m >= 4:
        return 'Big Spenders'
    else:
        return 'Regular'

def calculate_rfm(df):
    """Calculate RFM metrics and segments"""
    snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    
    rfm = df.groupby("CustomerID").agg({
        "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
        "InvoiceNo": "nunique",
        "Revenue": "sum"
    })
    
    rfm.columns = ["Recency", "Frequency", "Monetary"]
    
    # Calculate RFM scores (1-5 scale)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
    
    rfm['R_Score'] = rfm['R_Score'].astype(int)
    rfm['F_Score'] = rfm['F_Score'].astype(int)
    rfm['M_Score'] = rfm['M_Score'].astype(int)
    
    # Assign segments
    rfm['Segment'] = rfm.apply(assign_rfm_segment, axis=1)
    
    return rfm

# Load data
df = load_data()

# Header
st.title("📊 E-Commerce Analytics Dashboard")
st.markdown("---")

# ============ SECTION 1: Key Metrics ============
st.header("🎯 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_revenue = df["Revenue"].sum()
    st.metric(
        label="💰 Total Revenue",
        value=f"${total_revenue:,.0f}",
        delta=f"{(df.groupby(df['InvoiceDate'].dt.to_period('M'))['Revenue'].sum().pct_change().iloc[-1]*100):.1f}% MoM"
    )

with col2:
    total_orders = df["InvoiceNo"].nunique()
    st.metric(
        label="🛍️ Total Orders",
        value=f"{total_orders:,}",
    )

with col3:
    total_customers = df["CustomerID"].nunique()
    st.metric(
        label="👥 Total Customers",
        value=f"{total_customers:,}",
    )

with col4:
    avg_order_value = total_revenue / total_orders
    st.metric(
        label="💳 Avg Order Value",
        value=f"${avg_order_value:.2f}",
    )

st.markdown("---")

# ============ SECTION 2: Revenue Analytics ============
st.header("📈 Revenue & Growth Analytics")

monthly = df.set_index("InvoiceDate").resample("M")["Revenue"].sum()
growth = monthly.pct_change() * 100

col1, col2 = st.columns([2, 1])

with col1:
    # Combined revenue and growth chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=monthly.index, 
            y=monthly, 
            name="Revenue",
            fill='tozeroy',
            line=dict(color='#667eea', width=3),
            fillcolor='rgba(102, 126, 234, 0.1)'
        ),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Bar(
            x=growth.index, 
            y=growth, 
            name="Growth %",
            marker_color=['#10b981' if x > 0 else '#ef4444' for x in growth],
            opacity=0.7
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        title="Monthly Revenue Trend & Growth Rate",
        hovermode='x unified',
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.1)')
    fig.update_yaxes(title_text="Revenue ($)", secondary_y=False, showgrid=True, gridcolor='rgba(128,128,128,0.1)')
    fig.update_yaxes(title_text="Growth (%)", secondary_y=True, showgrid=False)
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Revenue Breakdown")
    
    # Revenue by country (top 5)
    country_revenue = df.groupby("Country")["Revenue"].sum().sort_values(ascending=False).head(5)
    
    fig_pie = px.pie(
        values=country_revenue.values,
        names=country_revenue.index,
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Purples_r
    )
    
    fig_pie.update_layout(
        height=400,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ============ SECTION 3: Customer RFM Segmentation ============
st.header("👥 Customer Intelligence & RFM Segmentation")

rfm = calculate_rfm(df)

# Segment overview
segment_counts = rfm['Segment'].value_counts()
segment_revenue = rfm.groupby('Segment')['Monetary'].sum()

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.subheader("🎯 Customer Segments")
    
    # Segment distribution
    segment_colors = {
        'Champions': '#10b981',
        'Loyal Customers': '#3b82f6',
        'Big Spenders': '#8b5cf6',
        'New Customers': '#06b6d4',
        'Regular': '#6b7280',
        'At Risk': '#f59e0b',
        'Lost Customers': '#ef4444'
    }
    
    fig_segments = go.Figure(data=[go.Pie(
        labels=segment_counts.index,
        values=segment_counts.values,
        marker=dict(colors=[segment_colors.get(seg, '#6b7280') for seg in segment_counts.index]),
        hole=0.4
    )])
    
    fig_segments.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=True
    )
    
    st.plotly_chart(fig_segments, use_container_width=True)

with col2:
    st.subheader("💎 Segment Value")
    
    fig_segment_value = px.bar(
        x=segment_revenue.index,
        y=segment_revenue.values,
        color=segment_revenue.values,
        color_continuous_scale='Viridis',
        labels={'x': 'Segment', 'y': 'Total Revenue ($)'}
    )
    
    fig_segment_value.update_layout(
        height=300,
        showlegend=False,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig_segment_value, use_container_width=True)

with col3:
    st.subheader("📊 Segment Metrics")
    
    for segment in ['Champions', 'At Risk', 'Lost Customers']:
        if segment in segment_counts.index:
            count = segment_counts[segment]
            pct = (count / segment_counts.sum() * 100)
            badge_class = segment.lower().replace(' ', '-')
            
            st.markdown(f"""
                <div style='padding: 10px; margin: 5px 0; background: #f9fafb; border-radius: 8px;'>
                    <span class='segment-badge {badge_class}'>{segment}</span>
                    <div style='margin-top: 5px; font-size: 1.2rem; font-weight: bold;'>{count:,} customers</div>
                    <div style='color: #6b7280; font-size: 0.85rem;'>{pct:.1f}% of total</div>
                </div>
            """, unsafe_allow_html=True)

# RFM Analysis Details
st.subheader("🔍 Detailed Customer Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    # Top customers table with better formatting
    st.markdown("##### 🏆 Top 20 Customers by Value")
    
    top_customers = rfm.sort_values('Monetary', ascending=False).head(20).reset_index()
    top_customers['Rank'] = range(1, len(top_customers) + 1)
    
    display_df = top_customers[['Rank', 'CustomerID', 'Recency', 'Frequency', 'Monetary', 'Segment']]
    display_df['Monetary'] = display_df['Monetary'].apply(lambda x: f"${x:,.2f}")
    display_df.columns = ['Rank', 'Customer ID', 'Days Since Last Purchase', 'Total Orders', 'Total Spent', 'Segment']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        hide_index=True
    )

with col2:
    st.markdown("##### 🎯 Segment Insights")
    
    # Champions
    champions = rfm[rfm['Segment'] == 'Champions']
    if len(champions) > 0:
        st.success(f"""
        **Champions** 🏆  
        {len(champions)} customers  
        Avg Spend: ${champions['Monetary'].mean():,.2f}  
        Avg Frequency: {champions['Frequency'].mean():.1f} orders
        """)
    
    # At Risk
    at_risk = rfm[rfm['Segment'] == 'At Risk']
    if len(at_risk) > 0:
        st.warning(f"""
        **At Risk** ⚠️  
        {len(at_risk)} customers  
        Avg Days Inactive: {at_risk['Recency'].mean():.0f} days  
        Recovery potential: ${at_risk['Monetary'].sum():,.2f}
        """)
    
    # Lost Customers
    lost = rfm[rfm['Segment'] == 'Lost Customers']
    if len(lost) > 0:
        st.error(f"""
        **Lost Customers** 🚨  
        {len(lost)} customers  
        Avg Days Inactive: {lost['Recency'].mean():.0f} days  
        Lost value: ${lost['Monetary'].sum():,.2f}
        """)

st.markdown("---")

# ============ SECTION 4: Product Performance ============
st.header("🏪 Product Performance Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    # Top products chart
    product_perf = (
        df.groupby("Description")
        .agg({"Revenue": "sum", "Quantity": "sum"})
        .sort_values("Revenue", ascending=False)
        .head(20)
    )
    
    fig_products = go.Figure()
    
    fig_products.add_trace(go.Bar(
        y=product_perf.index,
        x=product_perf['Revenue'],
        orientation='h',
        marker=dict(
            color=product_perf['Revenue'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Revenue")
        ),
        text=[f"${x:,.0f}" for x in product_perf['Revenue']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<br>Qty: %{customdata:,}<extra></extra>',
        customdata=product_perf['Quantity']
    ))
    
    fig_products.update_layout(
        title="Top 20 Products by Revenue",
        height=600,
        yaxis={'categoryorder': 'total ascending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Revenue ($)",
        showlegend=False,
        margin=dict(l=200)
    )
    
    fig_products.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.1)')
    
    st.plotly_chart(fig_products, use_container_width=True)

with col2:
    st.subheader("📦 Product Stats")
    
    total_products = df["Description"].nunique()
    avg_product_revenue = df.groupby("Description")["Revenue"].sum().mean()
    top_product = product_perf.index[0]
    top_product_revenue = product_perf['Revenue'].iloc[0]
    
    st.metric("Total Products", f"{total_products:,}")
    st.metric("Avg Revenue per Product", f"${avg_product_revenue:,.2f}")
    
    st.markdown("---")
    
    st.markdown("##### 🌟 Top Product")
    st.info(f"""
    **{top_product}**  
    Revenue: ${top_product_revenue:,.2f}  
    Units Sold: {product_perf['Quantity'].iloc[0]:,}
    """)
    
    # Category performance (if you have category data)
    st.markdown("##### 📊 Quick Insights")
    
    # Items sold
    total_items = df['Quantity'].sum()
    st.metric("Total Items Sold", f"{total_items:,.0f}")
    
    # Average items per order
    avg_items = df.groupby('InvoiceNo')['Quantity'].sum().mean()
    st.metric("Avg Items/Order", f"{avg_items:.1f}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6b7280; padding: 20px;'>
        <p>📊 E-Commerce Analytics Dashboard | Data-driven insights for better business decisions</p>
    </div>
""", unsafe_allow_html=True)