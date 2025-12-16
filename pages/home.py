import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="World Bank Data Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🌍"
)

# --- 2. CUSTOM CSS (Gaya PPI Dashboard) ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .main-header { font-size: 2.5rem; font-weight: bold; color: #333; margin-bottom: 0px; }
    .sub-header { font-size: 1rem; color: #666; margin-bottom: 20px; }
    
    /* Blue Filter Bar */
    .filter-bar {
        background-color: #009FDA;
        padding: 20px;
        color: white;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    
    /* Metric Cards */
    .metric-container { display: flex; gap: 15px; margin-bottom: 20px; }
    .metric-card {
        flex: 1; padding: 20px; color: white;
        border-radius: 0px; min-height: 120px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .card-blue { background-color: #00B5E2; }
    .card-green { background-color: #00A651; }
    .card-orange { background-color: #F39200; }
    .card-red { background-color: #E74C3C; }
    
    .metric-value { font-size: 1.8rem; font-weight: bold; }
    .metric-label { font-size: 0.9rem; margin-top: 5px; opacity: 0.9; }
    
    /* Styling Streamlit Widgets inside Blue Bar */
    .stSelectbox label, .stSlider label { color: white !important; }
    
    /* Section Headers */
    .section-title {
        font-size: 1.4rem; color: #444; font-weight: 600;
        border-bottom: 3px solid #009FDA;
        padding-bottom: 5px; margin-top: 30px; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. PENGATURAN DATA ---

DATA_FOLDER = "data"  # Pastikan folder ini ada

# Mapping File berdasarkan Kategori agar dropdown rapi
FILES_STRUCTURE = {
    "1. Ekonomi Makro": {
        "GDP (Current US$)": "1.1. GDP (CURRENT US$).csv",
        "GDP Per Capita": "1.2. GDP PER CAPITA.csv",
        "GDP Growth (%)": "1.3. GDP growth (%).csv",
        "GNI": "1.4 Gross National Income (GNI).csv",
        "GDP by Sector": "1.5 GDP by sector (pertanian, industri, jasa).csv"
    },
    "2. Ketenagakerjaan": {
        "Labor Force Participation": "2.1 Labor force participation rate.csv",
        "Unemployment Rate": "2.2 Unemployment rate.csv",
        "Youth Unemployment": "2.3 Youth unemployment.csv",
        "Employment by Sector": "2.4 Employment by sector.csv"
    },
    "3. Inflasi & Konsumsi": {
        "Inflation (Consumer Prices)": "3.1 Inflation, consumer prices (%).csv",
        "Consumer Expenditure": "3.2. CONSUMER EXPENDITURE.csv"
    },
    "4. Perdagangan": {
        "Exports": "4.1 Exports of goods and services.csv",
        "Imports": "4.2 Imports of goods and services.csv",
        "Tariff Rates": "4.3 Tariff rates.csv",
        "Trade Openness": "4.4 Trade openness.csv"
    },
    "5. Investasi": {
        "FDI (Foreign Direct Investment)": "5.1 Foreign Direct Investment (FDI).csv",
        "Gross Capital Formation": "5.2 Gross capital formation.csv"
    },
    "6. Sosial (Kemiskinan & Ketimpangan)": {
        "Poverty Headcount ($4.20)": "6.1. POVERTY HEADCOUNT RATIO AT $4.20 A DAY.csv",
        "Gini Index": "6.2. GINI INDEX.csv",
        "Income Share Lowest 20%": "6.3 INCOME SHARE HELD BY LOWER 20%.csv"
    },
    "7. Demografi": {
        "Total Population": "7.1. TOTAL POPULATION.csv",
        "Urban Population": "7.2. URBAN POPULATION.csv",
        "Fertility Rate": "7.3. FERTILITY RATE.csv",
        "Life Expectancy": "7.4. LIFE EXPECTANCY AT BIRTH.csv"
    },
    "8. Pendidikan": {
        "School Enrollment": "8.1. SCHOOL ENROLLMENT.csv",
        "Govt Expenditure on Education": "8.2. GOVENRMENT EXPENDITURE ON EDUCATION.csv"
    },
    "9. Kesehatan": {
        "Health Expenditure": "9.1. HEALTH EXPENDITURE.csv",
        "Maternal Mortality": "9.2. MATERNAL MORTALITY.csv",
        "Infant Mortality": "9.3. INFANT MORTALITY.csv",
        "Drinking Water Access": "9.4. PEOPLE USING SAFELY MANAGED DRINKING WATER SERVICES.csv"
    },
    "10. Lingkungan & Energi": {
        "CO2 Emissions": "10.1. CO EMISSIONS.csv",
        "Renewable Energy Consumption": "10.2. RENEWABLE ENERGY CONSUMPTION.csv",
        "Forest Area": "10.3. FOREST AREA.csv",
        "Electricity Access": "10.4. ELECTRICITY ACCESS.csv"
    }
}

@st.cache_data
def load_and_clean_data(filename):
    """
    Membaca CSV Wide Format (Tahun sebagai kolom) dan mengubahnya menjadi Long Format.
    Mendeteksi delimiter (titik koma atau koma).
    """
    filepath = os.path.join(DATA_FOLDER, filename)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        # Coba baca dengan delimiter titik koma (sesuai screenshot Anda)
        df = pd.read_csv(filepath, sep=';')
        
        # Jika kolomnya cuma 1 (berarti salah delimiter), coba pakai koma
        if df.shape[1] < 2:
            df = pd.read_csv(filepath, sep=',')

        # Membersihkan nama kolom (hapus spasi di awal/akhir)
        df.columns = df.columns.str.strip()

        # Deteksi kolom Tahun (yang isinya angka 4 digit, misal 1990, 2000)
        year_cols = [c for c in df.columns if c.isdigit() and len(c) == 4]
        
        # Kolom Metadata (Negara, Kode, dll)
        id_vars = [c for c in df.columns if c not in year_cols]
        
        # MELT DATA: Mengubah kolom tahun menjadi baris
        df_melted = df.melt(id_vars=id_vars, value_vars=year_cols, var_name='Year', value_name='Value')
        
        # Konversi tipe data
        df_melted['Year'] = pd.to_numeric(df_melted['Year'], errors='coerce')
        df_melted['Value'] = pd.to_numeric(df_melted['Value'], errors='coerce')
        
        # Hapus baris yang nilainya kosong
        df_melted = df_melted.dropna(subset=['Value'])
        
        return df_melted

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

# --- 4. HEADER & FILTER BAR ---

st.markdown('<div class="main-header">World Bank Data Visualization</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive dashboard for global development indicators.</div>', unsafe_allow_html=True)

# Container Biru untuk Navigasi
with st.container():
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    
    with col1:
        # Pilih Kategori Utama
        selected_category = st.selectbox("1. Select Category", list(FILES_STRUCTURE.keys()))
    
    with col2:
        # Pilih Indikator (File CSV)
        available_files = FILES_STRUCTURE[selected_category]
        selected_indicator_name = st.selectbox("2. Select Indicator", list(available_files.keys()))
        selected_filename = available_files[selected_indicator_name]
    
    with col3:
        # Filter Tahun
        year_range = st.slider("3. Filter Year", 1990, 2024, (2000, 2023))

    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. DATA PROCESSING ---

df = load_and_clean_data(selected_filename)

if df is not None and not df.empty:
    # Filter Dataframe sesuai Slider Tahun
    df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    
    # Ambil Data Tahun Terakhir yang tersedia di rentang filter untuk KPI
    latest_year_in_data = df_filtered['Year'].max()
    df_latest = df_filtered[df_filtered['Year'] == latest_year_in_data]
    
    # --- 6. METRIC CARDS ---
    
    # Hitung KPI
    avg_value = df_latest['Value'].mean()
    total_countries = df_latest['Country Name'].nunique()
    
    # Negara Tertinggi
    top_country_row = df_latest.loc[df_latest['Value'].idxmax()]
    top_country_name = top_country_row['Country Name']
    top_country_val = top_country_row['Value']
    
    # Total Global (Sum) - Relevan untuk Populasi/GDP, kurang relevan untuk persentase/rate
    # Kita gunakan logika sederhana: jika rata-rata > 1000 kemungkinan ini nilai absolut (Sum relevan)
    label_sum = "Global Sum"
    val_sum = df_latest['Value'].sum()
    
    # HTML Cards
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-card card-blue">
            <div class="metric-value">{total_countries}</div>
            <div class="metric-label">Countries with Data ({latest_year_in_data})</div>
        </div>
        <div class="metric-card card-green">
            <div class="metric-value">{avg_value:,.2f}</div>
            <div class="metric-label">Global Average</div>
        </div>
        <div class="metric-card card-orange">
            <div class="metric-value">{top_country_name}</div>
            <div class="metric-label">Highest: {top_country_val:,.2f}</div>
        </div>
        <div class="metric-card card-red">
            <div class="metric-value">{val_sum:,.0f}</div>
            <div class="metric-label">{label_sum}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 7. CHARTS SECTION ---
    
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.markdown('<div class="section-title">Trends Over Time (Top 5 Countries)</div>', unsafe_allow_html=True)
        
        # Ambil 5 negara dengan nilai terbesar di tahun terakhir untuk diplot trennya
        top_5_countries = df_latest.nlargest(5, 'Value')['Country Name'].tolist()
        df_trend = df_filtered[df_filtered['Country Name'].isin(top_5_countries)]
        
        fig_trend = px.line(
            df_trend, 
            x="Year", y="Value", color="Country Name",
            markers=True,
            title=None,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        # Style Area Chart seperti PPI
        fig_trend.update_traces(fill='tozeroy')
        fig_trend.update_layout(
            height=400,
            xaxis_title="Year",
            yaxis_title=selected_indicator_name,
            legend=dict(orientation="h", y=1.1, x=0),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with c_right:
        st.markdown(f'<div class="section-title">Top 10 Ranking ({latest_year_in_data})</div>', unsafe_allow_html=True)
        
        df_rank = df_latest.nlargest(10, 'Value').sort_values('Value', ascending=True)
        
        fig_bar = px.bar(
            df_rank, 
            x="Value", y="Country Name", 
            orientation='h',
            text_auto='.2s', # Format angka singkatan (k, M, B)
            color="Value",
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(
            height=400,
            xaxis_title=None,
            yaxis_title=None,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- 8. MAP & DISTRIBUTION ---
    
    st.markdown('<div class="section-title">Global Distribution</div>', unsafe_allow_html=True)
    
    col_map, col_dist = st.columns([3, 1])
    
    with col_map:
        if 'Country Code' in df_latest.columns:
            fig_map = px.choropleth(
                df_latest,
                locations="Country Code",
                color="Value",
                hover_name="Country Name",
                color_continuous_scale="Blues",
                title=f"Geographic Spread - {selected_indicator_name}"
            )
            fig_map.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Column 'Country Code' not found. Cannot render map.")
            
    with col_dist:
        # Donut Chart sederhana untuk distribusi (High/Mid/Low)
        # Membagi data menjadi 3 tier
        try:
            df_latest['Category'] = pd.qcut(df_latest['Value'], q=3, labels=["Low Tier", "Mid Tier", "Top Tier"])
            dist_counts = df_latest['Category'].value_counts().reset_index()
            dist_counts.columns = ['Category', 'Count']
            
            fig_pie = px.pie(
                dist_counts, values='Count', names='Category', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(
                title="Value Distribution", title_x=0.5,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=True, legend=dict(orientation="h", y=-0.1)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        except:
            st.info("Not enough data points for distribution analysis.")

    # --- 9. RAW DATA TABLE ---
    st.markdown('<div class="section-title">Data Table</div>', unsafe_allow_html=True)
    
    with st.expander("Show Raw Data"):
        # Pivot kembali ke Wide Format untuk tampilan tabel agar lebih mudah dibaca
        df_wide_view = df_filtered.pivot(index=['Country Name', 'Country Code'], columns='Year', values='Value')
        st.dataframe(df_wide_view, use_container_width=True)

else:
    # Error Handling jika file kosong atau tidak ditemukan
    st.warning(f"File '{selected_filename}' tidak ditemukan di folder '{DATA_FOLDER}' atau format datanya tidak sesuai.")
    st.info("Pastikan file CSV menggunakan delimiter titik koma (;) dan memiliki kolom tahun (misal: 1990, 1991).")