import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURASI HALAMAN & STYLE ---
st.set_page_config(
    page_title="World Bank Data Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk meniru gaya World Bank
st.markdown("""
    <style>
        .main { background-color: #F4F7F6; }
        h1, h2, h3 { color: #002244; font-family: 'Helvetica', sans-serif; }
        .stMetric {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 5px solid #0069B4;
        }
        [data-testid="stSidebar"] { background-color: #E9ECEF; }
        .css-1d391kg { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. PENGATURAN DATA ---
# Ganti path ini sesuai lokasi folder data Anda di komputer
DATA_FOLDER = "data" 

# Mapping Menu ke File CSV (Sesuai screenshot Anda)
MENU_FILES = {
    "Pertumbuhan Ekonomi & GDP": [
        "1.1. GDP (CURRENT US$).csv",
        "1.2. GDP PER CAPITA.csv",
        "1.3. GDP growth (%).csv",
        "1.4 Gross National Income (GNI).csv",
        "1.5 GDP by sector (pertanian, industri, jasa).csv"
    ],
    "Tenaga Kerja & Pengangguran": [
        "2.1 Labor force participation rate.csv",
        "2.2 Unemployment rate.csv",
        "2.3 Youth unemployment.csv",
        "2.4 Employment by sector.csv"
    ],
    "Inflasi & Harga Konsumen": [
        "3.1 Inflation, consumer prices (%).csv",
        "3.2. CONSUMER EXPENDITURE.csv"
    ],
    "Perdagangan Internasional": [
        "4.1 Exports of goods and services.csv",
        "4.2 Imports of goods and services.csv",
        "4.3 Tariff rates.csv",
        "4.4 Trade openness.csv"
    ],
    "Investasi (FDI & Kapital)": [
        "5.1 Foreign Direct Investment (FDI).csv",
        "5.2 Gross capital formation.csv"
    ],
    "Kemiskinan & Ketimpangan": [
        "6.1. POVERTY HEADCOUNT RATIO AT $4.20 A DAY.csv",
        "6.2. GINI INDEX.csv",
        "6.3 INCOME SHARE HELD BY LOWER 20%.csv"
    ],
    "Populasi & Demografi": [
        "7.1. TOTAL POPULATION.csv",
        "7.2. URBAN POPULATION.csv",
        "7.3. FERTILITY RATE.csv",
        "7.4. LIFE EXPECTANCY AT BIRTH.csv"
    ],
    "Pendidikan": [
        "8.1. SCHOOL ENROLLMENT.csv",
        "8.2. GOVENRMENT EXPENDITURE ON EDUCATION.csv"
    ],
    "Kesehatan": [
        "9.1. HEALTH EXPENDITURE.csv",
        "9.2. MATERNAL MORTALITY.csv",
        "9.3. INFANT MORTALITY.csv",
        "9.4. PEOPLE USING SAFELY MANAGED DRINKING WATER SERVICES.csv"
    ],
    "Energi & Lingkungan": [
        "10.1. CO EMISSIONS.csv",
        "10.2. RENEWABLE ENERGY CONSUMPTION.csv",
        "10.3. FOREST AREA.csv",
        "10.4. ELECTRICITY ACCESS.csv"
    ]
}

# Fungsi Load Data (dengan Error Handling jika file tidak ada)
@st.cache_data
def load_data(filename):
    path = os.path.join(DATA_FOLDER, filename)
    try:
        # Asumsi format CSV World Bank (biasanya ada header metadata, skip rows jika perlu)
        # Jika file bersih:
        df = pd.read_csv(path) 
        return df
    except FileNotFoundError:
        return None

# Fungsi Pembantu untuk membuat Dummy Data (Agar dashboard tidak error saat anda coba run pertama kali tanpa file asli)
def generate_mock_data(indicator_name):
    years = range(2010, 2025)
    countries = ["Indonesia", "Malaysia", "Vietnam", "Thailand", "Philippines"]
    data = []
    import numpy as np
    for c in countries:
        base = np.random.uniform(100, 1000)
        for y in years:
            data.append({
                "Country Name": c,
                "Country Code": c[:3].upper(),
                "Year": y,
                "Value": base * (1 + np.random.uniform(-0.05, 0.1))
            })
    return pd.DataFrame(data)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/The_World_Bank_logo.svg/2560px-The_World_Bank_logo.svg.png", width=200)
    st.title("Data Navigator")
    
    # Menu Navigasi Utama
    selected_menu = st.radio(
        "Pilih Indikator:",
        list(MENU_FILES.keys()) + ["Analisis World Bank 2025", "Dashboard Ekonomi (Home)"],
        index=len(MENU_FILES)+1 # Default ke Home
    )
    
    st.markdown("---")
    st.subheader("Filter Global")
    
    # Filter Tahun (Mockup range, nanti disesuaikan dengan data asli)
    year_range = st.slider("Rentang Tahun", 2000, 2025, (2015, 2024))
    
    # Filter Negara (Mockup list)
    selected_countries = st.multiselect("Pilih Negara", ["Indonesia", "China", "USA", "India"], default=["Indonesia"])

# --- 4. LOGIKA UTAMA (MAIN CONTENT) ---

# A. HALAMAN HOME / DASHBOARD UTAMA
if selected_menu == "Dashboard Ekonomi (Home)":
    st.title("🌍 Dashboard Ekonomi Makro")
    st.markdown("Ringkasan indikator utama pembangunan global.")
    
    # Baris Metric (KPI)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("GDP Growth (Global)", "3.2%", "+0.1%")
    c2.metric("Total Populasi", "8.1 B", "+0.9%")
    c3.metric("Inflasi Rata-rata", "4.5%", "-1.2%")
    c4.metric("FDI Inflow", "$1.3 T", "+5%")

    # Grafik Overview (Placeholder)
    st.subheader("Tren Pertumbuhan Ekonomi Regional")
    mock_df = generate_mock_data("GDP")
    fig = px.line(mock_df, x="Year", y="Value", color="Country Name", title="Simulasi Data GDP", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# B. HALAMAN INDIKATOR (Dinamis berdasarkan CSV)
elif selected_menu in MENU_FILES:
    st.title(f"📊 {selected_menu}")
    
    # Tab untuk File-file dalam kategori tersebut
    files_in_category = MENU_FILES[selected_menu]
    tabs = st.tabs([f.split('.')[1].strip().split('(')[0] for f in files_in_category]) # Mengambil nama pendek dari file
    
    for i, file_name in enumerate(files_in_category):
        with tabs[i]:
            st.subheader(f"Data: {file_name.replace('.csv', '')}")
            
            # Coba load data
            df = load_data(file_name)
            
            if df is None:
                st.warning(f"File '{file_name}' belum ditemukan di folder data. Menggunakan data simulasi.")
                df = generate_mock_data(file_name) # Fallback ke dummy
            
            # --- VISUALISASI DATA ---
            # 1. Metric Card (Data Terbaru)
            latest_year = df['Year'].max()
            latest_data = df[df['Year'] == latest_year]
            
            # Filter berdasarkan negara di sidebar (jika ada kolom Country Name)
            if 'Country Name' in df.columns and selected_countries:
                filtered_df = df[df['Country Name'].isin(selected_countries)]
                filtered_df = filtered_df[(filtered_df['Year'] >= year_range[0]) & (filtered_df['Year'] <= year_range[1])]
            else:
                filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

            # Layout Atas: Metric & Line Chart
            col_l, col_r = st.columns([1, 3])
            
            with col_l:
                if not filtered_df.empty:
                    avg_val = filtered_df['Value'].mean()
                    st.metric(label=f"Rata-rata ({year_range[0]}-{year_range[1]})", value=f"{avg_val:,.2f}")
                    st.markdown(f"**Sumber:** World Bank Data")
                else:
                    st.write("Tidak ada data untuk filter ini.")

            with col_r:
                if not filtered_df.empty:
                    fig_line = px.line(
                        filtered_df, 
                        x="Year", y="Value", 
                        color="Country Name", 
                        title=f"Tren {file_name.replace('.csv', '')}",
                        template="plotly_white",
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    st.plotly_chart(fig_line, use_container_width=True)

            # Layout Bawah: Map & Data Table
            c_map, c_data = st.columns([3, 2])
            
            with c_map:
                st.subheader("Peta Persebaran")
                # Gunakan data tahun terakhir untuk peta
                map_df = df[df['Year'] == df['Year'].max()]
                if not map_df.empty and 'Country Code' in map_df.columns:
                    fig_map = px.choropleth(
                        map_df,
                        locations="Country Code",
                        color="Value",
                        hover_name="Country Name",
                        color_continuous_scale="Blues",
                        title=f"Peta Dunia ({latest_year})"
                    )
                    fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.info("Data tidak memiliki kode negara untuk peta atau data kosong.")

            with c_data:
                st.subheader("Raw Data")
                st.dataframe(filtered_df, use_container_width=True, height=400)

# C. HALAMAN ANALISIS (Text Report)
elif selected_menu == "Analisis World Bank 2025":
    st.title("📘 Analisis Laporan World Bank 2025")
    st.markdown("### Creating Jobs, Growing Economies")
    
    with st.expander("1. Pertumbuhan Ekonomi & GDP", expanded=True):
        st.write("""
        Laporan menekankan bahwa pertumbuhan ekonomi harus diterjemahkan menjadi penciptaan lapangan kerja nyata. 
        **Türkiye** mencatat rata-rata pertumbuhan GDP riil sebesar 5,4%, sementara **Bhutan** menargetkan penggandaan GDP per kapita pada 2029. 
        Tantangan utama adalah 'Middle-Income Trap' bagi negara berkembang.
        """)
    
    with st.expander("2. Tenaga Kerja dan Pengangguran"):
        st.write("""
        **Fokus Utama:** Kesenjangan masif antara suplai tenaga kerja (1.2 miliar anak muda) dan lapangan kerja (400 juta) dalam dekade mendatang.
        Masalah akut di **Sub-Sahara Afrika**. Strategi World Bank: Infrastruktur, Regulasi, dan Modal Swasta.
        """)

    col1, col2 = st.columns(2)
    with col1:
        st.info("**3. Inflasi:** Fokus pada stabilitas makroekonomi jangka panjang (Contoh: Reformasi Sri Lanka).")
        st.info("**4. Perdagangan:** Integrasi rantai pasok dan infrastruktur (Contoh: Pelabuhan Tanger Med, Moroko).")
        st.info("**5. Investasi:** Mobilisasi modal swasta via Guarantee Platform ($20 Miliar target 2030).")
    
    with col2:
        st.success("**6. Kemiskinan:** Target mengakhiri kemiskinan ekstrem. Inklusi keuangan wanita di Nigeria & Argentina.")
        st.success("**7. Demografi:** Ledakan pemuda (Youth Bulge) bisa menjadi dividen atau bencana.")
        st.success("**8. Pendidikan:** Fokus pada STEM (African Centers of Excellence) dan skill digital.")

    st.markdown("---")
    st.caption("Sumber: Analisis Dokumen World Bank Group Annual Report 2025")