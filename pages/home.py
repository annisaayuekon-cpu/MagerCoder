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

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .main-header { font-size: 2.5rem; font-weight: bold; color: #333; margin-bottom: 0px; }
    .sub-header { font-size: 1rem; color: #666; margin-bottom: 20px; }
    .filter-bar { background-color: #009FDA; padding: 20px; color: white; margin-bottom: 20px; border-radius: 4px; }
    .metric-container { display: flex; gap: 15px; margin-bottom: 20px; }
    .metric-card { flex: 1; padding: 20px; color: white; border-radius: 0px; min-height: 120px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .card-blue { background-color: #00B5E2; }
    .card-green { background-color: #00A651; }
    .card-orange { background-color: #F39200; }
    .card-red { background-color: #E74C3C; }
    .metric-value { font-size: 1.8rem; font-weight: bold; }
    .metric-label { font-size: 0.9rem; margin-top: 5px; opacity: 0.9; }
    .stSelectbox label, .stSlider label { color: white !important; }
    .section-title { font-size: 1.4rem; color: #444; font-weight: 600; border-bottom: 3px solid #009FDA; padding-bottom: 5px; margin-top: 30px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 3. PENGATURAN DATA ---
DATA_FOLDER = "data"

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
    Fungsi Pintar:
    1. Deteksi Delimiter (; atau ,)
    2. Deteksi Format Data (Long/Sudah Rapi vs Wide/Perlu Melt)
    """
    filepath = os.path.join(DATA_FOLDER, filename)
    if not os.path.exists(filepath): return None
    
    try:
        # A. DETEKSI DELIMITER
        df = pd.read_csv(filepath, sep=';')
        if df.shape[1] < 2: 
            df = pd.read_csv(filepath, sep=',')

        # Bersihkan nama kolom
        df.columns = df.columns.str.strip()

        # B. DETEKSI FORMAT DATA
        
        # KASUS 1: DATA SUDAH RAPI (FORMAT LONG) - Contoh: CO2 EMISSIONS.csv
        # Ciri: Ada kolom bernama 'Year'
        if 'Year' in df.columns:
            # Kita perlu standarisasi kolom nilai menjadi 'Value'
            # Cari kolom yang BUKAN metadata (Country Name, Code, Year)
            metadata_cols = ['Country Name', 'Country Code', 'Year', 'Unnamed: 0']
            value_cols = [c for c in df.columns if c not in metadata_cols]
            
            if value_cols:
                # Ambil kolom nilai pertama yg ditemukan (misal: 'CO2 emissions (per capita)')
                # dan rename jadi 'Value' agar kode visualisasi di bawah tidak error
                df = df.rename(columns={value_cols[0]: 'Value'})
            
            # Pastikan tipe data benar
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
            return df.dropna(subset=['Value'])

        # KASUS 2: DATA MELEBAR (FORMAT WIDE) - Contoh: GDP.csv
        # Ciri: Tahun menjadi nama kolom (1990, 1991, ...)
        else:
            year_cols = [c for c in df.columns if c.isdigit() and len(c) == 4]
            if not year_cols:
                # Jika tidak ketemu format apapun
                st.error(f"Format kolom pada file {filename} tidak dikenali.")
                return None
            
            id_vars = [c for c in df.columns if c not in year_cols]
            df_melted = df.melt(id_vars=id_vars, value_vars=year_cols, var_name='Year', value_name='Value')
            
            df_melted['Year'] = pd.to_numeric(df_melted['Year'], errors='coerce')
            df_melted['Value'] = pd.to_numeric(df_melted['Value'], errors='coerce')
            return df_melted.dropna(subset=['Value'])

    except Exception as e:
        st.error(f"Error reading file {filename}: {e}")
        return None

# --- 4. HEADER & NAVIGASI ---

st.markdown('<div class="main-header">World Bank Data Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive visualization for global development indicators.</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    
    with col1:
        selected_category = st.selectbox("1. Select Category", list(FILES_STRUCTURE.keys()))
    with col2:
        available_files = FILES_STRUCTURE[selected_category]
        selected_indicator_name = st.selectbox("2. Select Indicator", list(available_files.keys()))
        selected_filename = available_files[selected_indicator_name]
    with col3:
        year_range = st.slider("3. Filter Year", 1990, 2024, (2000, 2023))
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. VISUALISASI ---

df = load_and_clean_data(selected_filename)

if df is not None and not df.empty:
    if 'Year' in df.columns and 'Value' in df.columns:
        
        # Filter Tahun
        df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
        
        if df_filtered.empty:
            st.warning("Data kosong untuk rentang tahun yang dipilih.")
        else:
            latest_year_in_data = df_filtered['Year'].max()
            df_latest = df_filtered[df_filtered['Year'] == latest_year_in_data]
            
            # Tentukan kolom Nama Negara (Bisa 'Country Name' atau kolom pertama)
            country_col = 'Country Name' if 'Country Name' in df_latest.columns else df_latest.columns[0]

            # --- KPI CARDS ---
            avg_val = df_latest['Value'].mean()
            total_countries = df_latest[country_col].nunique()
            
            if not df_latest.empty:
                top_row = df_latest.loc[df_latest['Value'].idxmax()]
                top_name, top_val = top_row[country_col], top_row['Value']
            else:
                top_name, top_val = "-", 0
            
            val_sum = df_latest['Value'].sum() # Relevan untuk CO2 total, Populasi, GDP
            
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card card-blue">
                    <div class="metric-value">{total_countries}</div>
                    <div class="metric-label">Countries ({latest_year_in_data})</div>
                </div>
                <div class="metric-card card-green">
                    <div class="metric-value">{avg_val:,.2f}</div>
                    <div class="metric-label">Global Average</div>
                </div>
                <div class="metric-card card-orange">
                    <div class="metric-value">{str(top_name)[:15]}..</div>
                    <div class="metric-label">Highest: {top_val:,.2f}</div>
                </div>
                <div class="metric-card card-red">
                    <div class="metric-value">{val_sum:,.0f}</div>
                    <div class="metric-label">Global Sum</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- CHARTS ---
            c_left, c_right = st.columns([2, 1])
            
            with c_left:
                st.markdown('<div class="section-title">Trends Over Time (Top 5)</div>', unsafe_allow_html=True)
                top_5 = df_latest.nlargest(5, 'Value')[country_col].tolist()
                df_trend = df_filtered[df_filtered[country_col].isin(top_5)]
                
                fig = px.line(df_trend, x="Year", y="Value", color=country_col, markers=True, color_discrete_sequence=px.colors.qualitative.Safe)
                fig.update_traces(fill='tozeroy')
                fig.update_layout(height=400, xaxis_title="Year", yaxis_title=selected_indicator_name, legend=dict(orientation="h", y=1.1, x=0))
                st.plotly_chart(fig, use_container_width=True)
                
            with c_right:
                st.markdown(f'<div class="section-title">Top 10 ({latest_year_in_data})</div>', unsafe_allow_html=True)
                df_rank = df_latest.nlargest(10, 'Value').sort_values('Value', ascending=True)
                fig_bar = px.bar(df_rank, x="Value", y=country_col, orientation='h', text_auto='.2s', color="Value", color_continuous_scale="Blues")
                fig_bar.update_layout(height=400, xaxis_title=None, yaxis_title=None, coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            # --- MAP & TABLE ---
            st.markdown('<div class="section-title">Global Distribution</div>', unsafe_allow_html=True)
            col_map, col_dist = st.columns([3, 1])
            
            with col_map:
                # Cek kode negara untuk peta
                code_col = 'Country Code' if 'Country Code' in df_latest.columns else None
                if code_col:
                    fig_map = px.choropleth(df_latest, locations=code_col, color="Value", hover_name=country_col, color_continuous_scale="Blues")
                    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.info("Peta tidak tersedia (Kolom 'Country Code' tidak ditemukan).")
            
            with col_dist:
                try:
                    df_latest['Tier'] = pd.qcut(df_latest['Value'], 3, labels=["Low", "Mid", "High"])
                    fig_pie = px.pie(df_latest['Tier'].value_counts().reset_index(), values='count', names='Tier', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                    st.plotly_chart(fig_pie, use_container_width=True)
                except:
                    st.write("Data distribution not available.")

            st.markdown('<div class="section-title">Raw Data</div>', unsafe_allow_html=True)
            with st.expander("Show Data Table"):
                st.dataframe(df_filtered, use_container_width=True)
    else:
        st.error("Struktur data tidak valid. Kolom 'Year' atau 'Value' hilang setelah pemrosesan.")
else:
    st.warning(f"File '{selected_filename}' tidak ditemukan di folder '{DATA_FOLDER}'.")