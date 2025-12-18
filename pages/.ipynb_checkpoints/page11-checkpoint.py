import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="World Bank Group 2024 Insights",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk mempercantik tampilan
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #0071bc;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    h1, h2, h3 {
        color: #002244;
    }
    .highlight {
        color: #0071bc;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SIDEBAR & HEADER
# -----------------------------------------------------------------------------

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/The_World_Bank_logo.svg/2560px-The_World_Bank_logo.svg.png", width=200)
    st.title("Navigasi Laporan")
    st.info("Dashboard ini merangkum wawasan utama dari tiga laporan unggulan World Bank Group tahun 2024.")
    
    st.markdown("### Sumber Data:")
    st.markdown("1. **Annual Report 2024**: A Better Bank for a Better World")
    st.markdown("2. **WDR 2024**: The Middle-Income Trap")
    st.markdown("3. **Poverty, Prosperity, and Planet**: Pathways Out of the Polycrisis")
    
    st.markdown("---")
    st.markdown("**Visi Baru:**")
    st.caption("Creating a world free of poverty on a livable planet.")

st.title("🌍 World Bank Group: Laporan Terintegrasi 2024")
st.markdown("#### Ringkasan Eksekutif, Strategi Ekonomi, dan Tantangan Global")

# -----------------------------------------------------------------------------
# 3. TAB STRUKTUR
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "🏦 Annual Report: Kinerja & Komitmen", 
    "📈 WDR 2024: Middle-Income Trap", 
    "📉 Poverty & Planet: Polycrisis"
])

# =============================================================================
# TAB 1: ANNUAL REPORT 2024 (A Better Bank)
# =============================================================================
with tab1:
    st.header("A Better Bank for a Better World")
    st.markdown("Tahun fiskal 2024 menandai transformasi World Bank dengan visi baru, instrumen keuangan baru, dan fokus pada kecepatan serta dampak.")

    # Baris 1: Key Financials
    st.subheader("Ringkasan Finansial Fiskal 2024")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total Komitmen Global", value="$117.5 Miliar", delta="IBRD, IDA, IFC, MIGA")
    with col2:
        st.metric(label="Pendanaan Iklim", value="45%", delta="Target 2025")
    with col3:
        st.metric(label="Komitmen Afrika", value="$38.0 Miliar", help="Wilayah dengan komitmen terbesar")
    with col4:
        st.metric(label="Sektor Kesehatan", value="1.5 Miliar Orang", help="Target layanan kesehatan berkualitas pada 2030")

    st.markdown("---")

    # Baris 2: Grafik & Breakdown
    col_chart, col_text = st.columns([1.5, 1])
    
    with col_chart:
        # Data Komitmen per Region (Dari PDF Summary)
        data_region = {
            'Region': ['Africa', 'Europe & Central Asia', 'Latin America & Caribbean', 'South Asia', 'East Asia & Pacific', 'Middle East & North Africa'],
            'Amount (Billion $)': [38.0, 24.7, 19.4, 15.9, 12.5, 6.5]
        }
        df_region = pd.DataFrame(data_region)
        
        fig_region = px.bar(
            df_region, 
            x='Amount (Billion $)', 
            y='Region', 
            orientation='h',
            title='Komitmen Berdasarkan Wilayah (Fiscal 2024)',
            color='Amount (Billion $)',
            color_continuous_scale='Blues',
            text='Amount (Billion $)'
        )
        fig_region.update_layout(xaxis_title="Miliar USD", yaxis_title="")
        st.plotly_chart(fig_region, use_container_width=True)

    with col_text:
        st.subheader("Inisiatif Utama")
        with st.expander("5 Unit Pengetahuan Tematik (New Structure)", expanded=True):
            st.markdown("""
            Bank Dunia melakukan reorganisasi menjadi 5 unit *Vice Presidency* untuk berbagi pengetahuan lebih efektif:
            1. **People** (Kesehatan, Pendidikan, Perlindungan Sosial)
            2. **Prosperity** (Ekonomi, Keuangan, Kemiskinan)
            3. **Planet** (Iklim, Pertanian, Air)
            4. **Infrastructure** (Energi, Transportasi)
            5. **Digital** (Transformasi Digital)
            """)
        
        with st.expander("Instrumen Keuangan Baru"):
            st.markdown("""
            - **Hybrid Capital & Portfolio Guarantee Platform**: Memungkinkan pengambilan risiko lebih besar.
            - **Crisis Preparedness and Response Toolkit**: Termasuk opsi penundaan pembayaran utang bagi negara kecil saat bencana.
            - **Livable Planet Fund**: Diluncurkan April 2024 untuk kontribusi pemerintah dan filantropi.
            """)

# =============================================================================
# TAB 2: WDR 2024 (The Middle-Income Trap)
# =============================================================================
with tab2:
    st.header("World Development Report 2024: The Middle-Income Trap")
    
    st.markdown("""
    > *"Negara-negara berpenghasilan menengah sedang berpacu dengan waktu. Banyak yang masih menggunakan pedoman lama dari abad lalu, hanya mengandalkan investasi modal. Ini seperti mengendarai mobil dengan gigi satu dan mencoba melaju lebih cepat."* - **Indermit Gill**, Chief Economist.
    """)
    
    # Konsep Inti
    st.info("**Masalah Utama:** Sejak 1990-an, hanya 34 negara berpenghasilan menengah yang berhasil transisi ke status berpenghasilan tinggi. Sisanya terjebak karena pertumbuhan melambat saat pendapatan per kapita mencapai sekitar 10% dari level AS (sekitar $8.000 hari ini).")

    st.subheader("Solusi: Strategi 3i")
    st.markdown("Negara harus melakukan **dua transisi** berturut-turut melalui tiga tahap kebijakan:")

    # Layout 3 Kolom untuk Strategi 3i
    col_i1, col_i2, col_i3 = st.columns(3)
    
    with col_i1:
        st.container(border=True)
        st.markdown("### 1. Investment")
        st.markdown("**Fase: Low-Income**")
        st.write("Fokus pada akumulasi modal fisik (infrastruktur) dan sumber daya manusia.")
        st.progress(33)
    
    with col_i2:
        st.container(border=True)
        st.markdown("### 2. Infusion")
        st.markdown("**Fase: Lower-Middle Income**")
        st.write("Meniru dan mengadopsi teknologi global. Membawa ide dari luar dan menyebarkannya secara domestik.")
        st.progress(66)
    
    with col_i3:
        st.container(border=True)
        st.markdown("### 3. Innovation")
        st.markdown("**Fase: Upper-Middle Income**")
        st.write("Mendorong batas teknologi global. Menciptakan ide baru, bukan hanya mengadopsi.")
        st.progress(100)

    st.markdown("---")
    
    # Kekuatan Schumpeterian
    st.subheader("Dinamika 'Creative Destruction'")
    col_dest1, col_dest2 = st.columns([1, 2])
    
    with col_dest1:
        st.markdown("""
        Untuk sukses, masyarakat harus menyeimbangkan tiga kekuatan ekonomi:
        1. **Creation (Kreasi):** Inkumben dan pendatang baru menciptakan nilai.
        2. **Preservation (Pelestarian):** Kekuatan yang melindungi status quo (elit, monopoli).
        3. **Destruction (Destruksi):** Menghilangkan praktik/perusahaan usang agar yang baru bisa tumbuh.
        """)
        
    with col_dest2:
        # Simulasi Data Produktivitas (Illustrative)
        data_prod = pd.DataFrame({
            'Stage': ['Investment Only', 'Investment + Infusion', '3i Strategy (Korea/Poland)'],
            'Growth Potential': [2.5, 4.5, 6.0],
            'Complexity': ['Low', 'Medium', 'High']
        })
        
        fig_prod = px.bar(data_prod, x='Stage', y='Growth Potential', 
                          color='Complexity', 
                          title="Potensi Pertumbuhan Berdasarkan Strategi Kebijakan",
                          text_auto=True)
        st.plotly_chart(fig_prod, use_container_width=True)

# =============================================================================
# TAB 3: POVERTY & PLANET REPORT 2024
# =============================================================================
with tab3:
    st.header("Poverty, Prosperity, and Planet: Pathways Out of the Polycrisis")
    
    st.error("**Peringatan:** Pengurangan kemiskinan global melambat hingga hampir berhenti. Periode 2020-2030 berisiko menjadi 'dekade yang hilang'.")
    
    # Key Stats Row
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Kemiskinan Ekstrem (2024)", "8.5%", "-0.3% sejak 2019 (Stagnan)")
    kpi2.metric("Penduduk di Bawah $6.85/hari", "44%", "Hampir separuh populasi dunia")
    kpi3.metric("Risiko Iklim", "1 dari 5 Orang", "Beresiko menghadapi cuaca ekstrem seumur hidup")

    st.markdown("---")

    col_poly1, col_poly2 = st.columns(2)
    
    with col_poly1:
        st.subheader("Indikator Baru: Global Prosperity Gap")
        st.markdown("""
        World Bank memperkenalkan ukuran baru kemakmuran bersama.
        - **Definisi:** Faktor rata-rata dimana pendapatan harus dilipatgandakan untuk mencapai standar $25 per orang per hari.
        - **Status Saat Ini:** Rata-rata global adalah **5x**. Pendapatan rata-rata dunia harus naik 5 kali lipat untuk mencapai standar kemakmuran $25.
        - **Ketimpangan:** Jumlah negara dengan ketimpangan tinggi (Gini > 40) menurun, tetapi populasi di negara tersebut tetap tinggi (1.7 Miliar orang).
        """)
        
    with col_poly2:
        st.subheader("Polycrisis & Iklim")
        st.markdown("""
        Tantangan kemiskinan kini saling terkait dengan krisis iklim (**Polycrisis**).
        - **Trade-offs:** Mengentaskan kemiskinan ekstrem tidak membebani emisi global secara signifikan, namun mencapai standar kemakmuran yang lebih tinggi membutuhkan efisiensi energi yang masif.
        - **Sub-Saharan Africa:** Menampung 2/3 dari orang miskin ekstrem dunia dan memiliki risiko iklim tertinggi karena kerentanan infrastruktur.
        """)

    # Chart Proyeksi Kemiskinan
    st.subheader("Proyeksi Kemiskinan Ekstrem (Target 3% pada 2030)")
    
    # Data dummy representatif berdasarkan narasi laporan
    years = [2015, 2019, 2020, 2024, 2030]
    poverty_rates = [10.0, 8.8, 9.7, 8.5, 7.3] # 2030 projected at 7.3% based on current trends
    
    df_pov = pd.DataFrame({'Tahun': years, 'Tingkat Kemiskinan (%)': poverty_rates})
    
    fig_pov = px.line(df_pov, x='Tahun', y='Tingkat Kemiskinan (%)', markers=True, 
                      title="Tren Kemiskinan Global & Proyeksi (Garis Putus = Target 3% Meleset Jauh)")
    fig_pov.add_hline(y=3.0, line_dash="dash", line_color="green", annotation_text="Target SDG (3%)")
    fig_pov.add_vrect(x0=2019, x1=2021, fillcolor="red", opacity=0.1, annotation_text="COVID-19 Impact")
    
    st.plotly_chart(fig_pov, use_container_width=True)
    
    st.markdown("""
    **Kesimpulan Kebijakan:**
    Negara berpenghasilan rendah harus memprioritaskan pertumbuhan jangka panjang dan modal manusia. Negara berpenghasilan menengah dan tinggi harus mempercepat transisi rendah karbon untuk melindungi kelompok rentan dari risiko iklim.
    """)

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("Dashboard dikembangkan berdasarkan World Bank Annual Report 2024, WDR 2024, dan Poverty Prosperity and Planet Report 2024. Semua nilai mata uang dalam Dolar AS.")