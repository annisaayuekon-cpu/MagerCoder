import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PPI Visualization Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed" # Menyembunyikan sidebar
)

# --- 2. CUSTOM CSS (PENTING UNTUK TAMPILAN MIRIP) ---
st.markdown("""
<style>
    /* Mengatur Font */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Header Styles */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    /* Blue Filter Bar */
    .filter-bar {
        background-color: #009FDA; /* Warna Biru PPI */
        padding: 15px;
        border-radius: 5px;
        color: white;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Metric Cards Styles */
    .metric-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
    }
    .metric-card {
        flex: 1;
        padding: 20px;
        color: white;
        border-radius: 0px; /* Style WB kotak tajam */
        min-height: 120px;
    }
    .card-blue { background-color: #00B5E2; }
    .card-green { background-color: #00A651; }
    .card-orange { background-color: #F39200; }
    .card-red { background-color: #E74C3C; }
    
    .metric-value { font-size: 1.8rem; font-weight: bold; }
    .metric-label { font-size: 1rem; margin-top: 5px; opacity: 0.9; }
    
    /* Section Headers */
    .section-title {
        font-size: 1.2rem;
        color: #444;
        border-bottom: 2px solid #009FDA;
        padding-bottom: 5px;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 3. DATA LOADING (MOCKUP LOGIC) ---
# Menggunakan data dummy yang disesuaikan dengan struktur file Anda
# Agar dashboard bisa langsung jalan tanpa file fisik untuk demo ini
@st.cache_data
def load_mock_data():
    years = list(range(1995, 2025))
    regions = ['East Asia', 'South Asia', 'Latin America', 'Sub-Saharan Africa', 'Europe & Central Asia']
    sectors = ['Energy', 'Transport', 'Water', 'ICT']
    
    data = []
    for _ in range(500):
        year = np.random.choice(years)
        region = np.random.choice(regions)
        sector = np.random.choice(sectors)
        investment = np.random.uniform(10, 500)
        project_count = np.random.randint(1, 5)
        
        data.append({
            "Year": year,
            "Region": region,
            "Sector": sector,
            "Investment (USD Million)": investment,
            "Project Count": project_count,
            "Project Name": f"Project {np.random.randint(1000,9999)}",
            "Status": np.random.choice(["Active", "Concluded", "Cancelled"]),
            "Income Group": np.random.choice(["Low Income", "Middle Income", "High Income"])
        })
    return pd.DataFrame(data)

df = load_mock_data()

# --- 4. LAYOUT UTAMA ---

# A. Header & Intro
st.markdown('<div class="main-header">PPI Visualization Dashboard</div>', unsafe_allow_html=True)
st.write("The PPI Visualization Dashboard is a tool which allows users to visualize the data in several ways by selecting certain filters, such as regions, countries, sectors, and project status.")

# B. Blue Action Bar (Search & Buttons)
# Kita menggunakan columns di dalam container biru tiruan
st.markdown('<div class="filter-bar">Apply Your Filters: (Demo Search Bar)</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
with c1:
    search_term = st.text_input("Search", placeholder="Search for sector, country...", label_visibility="collapsed")
with c2:
    st.button("🔄 Reset")
with c3:
    st.button("Share")
with c4:
    st.button("PDF")
with c5:
    st.button("Excel")

# C. Colored Metric Cards (HTML Injection)
# Menghitung angka untuk ditampilkan
total_projects = df.shape[0]
total_invest = df['Investment (USD Million)'].sum()
top_sector = df.groupby('Sector')['Investment (USD Million)'].sum().idxmax()
perc_low_income = (len(df[df['Income Group'] == 'Low Income']) / len(df)) * 100

st.markdown(f"""
<div class="metric-container">
    <div class="metric-card card-blue">
        <div class="metric-value">{total_projects:,}</div>
        <div class="metric-label">Total Projects</div>
    </div>
    <div class="metric-card card-green">
        <div class="metric-value">${total_invest:,.2f} M</div>
        <div class="metric-label">Total Investment</div>
    </div>
    <div class="metric-card card-orange">
        <div class="metric-value">{top_sector}</div>
        <div class="metric-label">Sector with highest investment</div>
    </div>
    <div class="metric-card card-red">
        <div class="metric-value">{perc_low_income:.2f}%</div>
        <div class="metric-label">Projects from low income countries</div>
    </div>
</div>
""", unsafe_allow_html=True)

# D. Main Charts (Timeseries & Bubble)
c_left, c_right = st.columns([3, 2])

with c_left:
    st.markdown('<div class="section-title">Project Timeseries</div>', unsafe_allow_html=True)
    
    # Aggregating data
    ts_data = df.groupby('Year').agg({'Investment (USD Million)':'sum', 'Project Count':'count'}).reset_index()
    
    # Membuat Combo Chart (Area + Line) seperti contoh
    fig_ts = go.Figure()
    
    # Area Chart untuk Investment
    fig_ts.add_trace(go.Scatter(
        x=ts_data['Year'], y=ts_data['Investment (USD Million)'],
        fill='tozeroy', mode='none', name='Total Investment',
        fillcolor='rgba(0, 114, 188, 0.6)' # Warna biru WB
    ))
    
    # Line Chart untuk Jumlah Project (Secondary Axis)
    fig_ts.add_trace(go.Scatter(
        x=ts_data['Year'], y=ts_data['Project Count'],
        mode='lines+markers', name='Number of Projects',
        line=dict(color='#F39200', width=2),
        yaxis='y2'
    ))
    
    fig_ts.update_layout(
        xaxis=dict(title='Year'),
        yaxis=dict(title='Total Investment', showgrid=True),
        yaxis2=dict(title='Number of Projects', overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", y=1.1, x=0),
        margin=dict(l=0, r=0, t=20, b=0),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_ts, use_container_width=True)

with c_right:
    st.markdown('<div class="section-title">Sectors (Investment vs Count)</div>', unsafe_allow_html=True)
    
    sec_data = df.groupby('Sector').agg({'Investment (USD Million)':'sum', 'Project Count':'count'}).reset_index()
    
    fig_bubble = px.scatter(
        sec_data, 
        x="Investment (USD Million)", 
        y="Project Count",
        size="Investment (USD Million)",
        color="Sector",
        hover_name="Sector",
        size_max=60,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_bubble.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(240,240,240,0.5)'
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

# E. Filters / Donut Charts Grid
st.markdown('<div class="section-title">Filters (Distribution)</div>', unsafe_allow_html=True)

# Kita buat 4 kolom untuk donut charts
col_d1, col_d2, col_d3, col_d4 = st.columns(4)

def create_donut(data, col, title, color_scheme=px.colors.sequential.Blues):
    grouped = data.groupby(col)['Investment (USD Million)'].sum().reset_index()
    fig = px.pie(
        grouped, 
        values='Investment (USD Million)', 
        names=col, 
        hole=0.5,
        color_discrete_sequence=color_scheme
    )
    fig.update_layout(
        title_text=title,
        title_x=0.5,
        margin=dict(l=0, r=0, t=30, b=0),
        height=200,
        showlegend=False
    )
    return fig

# Baris 1 Donut Charts
with col_d1:
    st.plotly_chart(create_donut(df, 'Status', 'Project Status', px.colors.qualitative.Pastel), use_container_width=True)
with col_d2:
    st.plotly_chart(create_donut(df, 'Sector', 'Sector Breakdown', px.colors.qualitative.Set3), use_container_width=True)
with col_d3:
    st.plotly_chart(create_donut(df, 'Income Group', 'Income Group', px.colors.qualitative.Prism), use_container_width=True)
with col_d4:
    st.plotly_chart(create_donut(df, 'Region', 'Region', px.colors.qualitative.Vivid), use_container_width=True)

# F. Data Table (Filtered Projects)
st.markdown('<div class="section-title">Filtered Projects Data</div>', unsafe_allow_html=True)

st.dataframe(
    df,
    column_config={
        "Investment (USD Million)": st.column_config.NumberColumn(format="$%.2f M"),
        "Year": st.column_config.NumberColumn(format="%d"),
    },
    use_container_width=True,
    hide_index=True
)