import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# Konfigurasi Halaman
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="World Bank Group Annual Report 2025",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk styling sederhana
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #0071bc;
        text-align: center;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #444;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0071bc;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar: Tentang Kami & Institusi
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/The_World_Bank_logo.svg/2560px-The_World_Bank_logo.svg.png", use_container_width=True)
    st.header("Tentang Kami")
    st.info("**Misi:** Mengakhiri kemiskinan ekstrem dan meningkatkan kemakmuran bersama di planet yang layak huni.")
    
    st.subheader("Institusi World Bank Group")
    with st.expander("IBRD & IDA (World Bank)", expanded=True):
        st.write("Memberikan pinjaman, hibah, dan saran kebijakan untuk pemerintah.")
    with st.expander("IFC"):
        st.write("Fokus pada sektor swasta di negara berkembang.")
    with st.expander("MIGA"):
        st.write("Menyediakan garansi risiko politik dan peningkatan kredit.")
    with st.expander("ICSID"):
        st.write("Menyelesaikan sengketa investasi internasional.")

    st.divider()
    st.caption("Sumber: World Bank Group Annual Report 2025")
    st.caption("Presiden: Ajay Banga")

# -----------------------------------------------------------------------------
# Header Utama
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">CREATING JOBS, GROWING ECONOMIES</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">World Bank Group Annual Report 2025 - Dashboard Ringkasan</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Bagian 1: Key Metrics (Fiscal 2025)
# -----------------------------------------------------------------------------
st.subheader("📊 Sorotan Utama Tahun Fiskal 2025")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Komitmen Global", value="$118.5 Miliar", delta="Tahun Fiskal 2025")
with col2:
    st.metric(label="Private Capital Mobilized", value="$68.9 Miliar", delta="Oleh IFC & MIGA")
with col3:
    st.metric(label="Climate Finance", value="48%", delta="Melampaui target 45%")
with col4:
    st.metric(label="Penerbitan Garansi (Platform Baru)", value="$12.3 Miliar", delta="Meningkat 19%")

st.divider()

# -----------------------------------------------------------------------------
# Bagian 2: Komitmen Finansial Berdasarkan Wilayah
# -----------------------------------------------------------------------------
col_chart, col_text = st.columns([2, 1])

with col_chart:
    st.subheader("🌍 Komitmen Berdasarkan Wilayah (Miliar USD)")
    
    # Data dari Laporan (Halaman 9)
    data_region = {
        'Region': [
            'Sub-Saharan Africa', 
            'Europe & Central Asia', 
            'Latin America & Caribbean', 
            'South Asia', 
            'East Asia & Pacific', 
            'Middle East & North Africa',
            'Global'
        ],
        'Commitments ($B)': [34.0, 25.1, 24.9, 13.2, 12.2, 8.5, 0.6]
    }
    df_region = pd.DataFrame(data_region)
    
    fig = px.bar(
        df_region, 
        x='Region', 
        y='Commitments ($B)', 
        color='Region',
        text_auto=True,
        title="Distribusi Pendanaan Regional FY2025"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_text:
    st.subheader("Fokus Regional")
    st.markdown("""
    - **Sub-Saharan Africa** menerima porsi terbesar ($34.0B) dengan inisiatif besar seperti **Mission 300** untuk akses listrik.
    - **Eropa & Asia Tengah** ($25.1B) berfokus pada pemulihan pasca-krisis dan keamanan energi.
    - **Amerika Latin** ($24.9B) fokus pada perlindungan Amazon dan infrastruktur.
    """)
    st.info("Total Komitmen IBRD: $40.9B | IDA: $39.9B | IFC: $23.0B (Own Account) | MIGA: $9.5B (Gross Issuance)")

st.divider()

# -----------------------------------------------------------------------------
# Bagian 3: Prioritas Strategis & Scorecard
# -----------------------------------------------------------------------------
st.subheader("🎯 Prioritas Strategis & Scorecard Dampak")

tab1, tab2 = st.tabs(["5 Prioritas Utama", "Scorecard Dampak Terpilih"])

with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.success("**Produktivitas Pertanian**")
        st.caption("Target $9M per tahun pada 2030 untuk agribisnis.")
    with c2:
        st.warning("**Akses Listrik**")
        st.caption("Menghubungkan 300 juta orang di Afrika (Mission 300).")
    with c3:
        st.error("**Layanan Kesehatan**")
        st.caption("Menjangkau 1.5 miliar orang dengan layanan berkualitas.")
    with c4:
        st.info("**Perlindungan Sosial**")
        st.caption("Mencapai 500 juta orang miskin & rentan.")
    with c5:
        st.primary("**Pemberdayaan Wanita**")
        st.caption("Akses broadband untuk 300 juta wanita.")

with tab2:
    # Data dari Halaman 8
    scorecard_data = {
        'Indikator': [
            'Penerima manfaat jaring pengaman sosial',
            'Siswa yang didukung pendidikan lebih baik',
            'Orang yang menerima layanan kesehatan berkualitas',
            'Orang yang mendapat akses listrik baru',
            'Orang yang menggunakan internet broadband',
            'Penerima manfaat kesetaraan gender',
            'Total Modal Swasta yang Dimobilisasi'
        ],
        'Pencapaian FY25': ['244 Juta', '325 Juta', '379 Juta', '215 Juta', '217 Juta', '257 Juta', '$242 Miliar'],
        'Target/Ekspektasi FY25': ['251 Juta', '406 Juta', '467 Juta', '576 Juta', '431 Juta', '439 Juta', '-']
    }
    df_score = pd.DataFrame(scorecard_data)
    st.dataframe(df_score, use_container_width=True, hide_index=True)

st.divider()

# -----------------------------------------------------------------------------
# Bagian 4: Hasil Berdasarkan Tema (Case Studies)
# -----------------------------------------------------------------------------
st.subheader("💡 Hasil Berdasarkan Tema & Studi Kasus")

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("### 👷 Jobs & Economic Growth")
    with st.expander("Lihat Detail"):
        st.write("""
        **Strategi 3 Pilar Penciptaan Lapangan Kerja:**
        1. Membangun infrastruktur dasar (Fisik & Manusia).
        2. Memperkuat tata kelola & regulasi.
        3. Memobilisasi modal swasta.
        
        **Studi Kasus:**
        - **Tanzania:** IFC memberikan pinjaman $45M ke KIOO (pembuat kaca) untuk meningkatkan produksi dan lapangan kerja.
        - **Benin:** MIGA & IDA memberikan garansi $221.5M untuk meningkatkan pertumbuhan sektor swasta dan ketahanan iklim.
        """)

with row1_col2:
    st.markdown("### 🌿 Planet & Climate")
    with st.expander("Lihat Detail"):
        st.write("""
        **Fokus:** Udara bersih, air, sistem pangan berkelanjutan.
        
        **Studi Kasus:**
        - **Papua New Guinea:** Proyek agrikultur senilai $40M membantu 20.000 petani kopi dan kakao.
        - **Kenya:** MIGA menjamin $49.5M untuk proyek panas bumi Menengai guna mencapai 100% energi bersih pada 2030.
        - **Romania:** IFC memberikan 'blue loan' pertama di Eropa Timur untuk manajemen air.
        """)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("### 💻 Digital Transformation")
    with st.expander("Lihat Detail"):
        st.write("""
        **Tantangan:** Afrika Timur & Selatan memiliki laju digitalisasi terlambat.
        
        **Program IDEA:** 
        Investasi $2.5 Miliar untuk memberdayakan 180 juta orang dengan akses internet di Afrika Timur & Selatan.
        
        **Malaysia:**
        IFC mendanai kampus pusat data di Johor Bahru untuk mendukung ekonomi digital Asia Pasifik.
        """)

with row2_col2:
    st.markdown("### 👩 Gender & Youth")
    with st.expander("Lihat Detail"):
        st.write("""
        **Target 2030:** 80 juta wanita mendapat akses modal, 300 juta akses broadband.
        
        **Studi Kasus:**
        - **Nigeria:** Program Nigeria2Equal bersama MTN Nigeria untuk meningkatkan kesetaraan gender di tempat kerja.
        - **Argentina:** Garansi MIGA $500M untuk Santander Argentina guna meningkatkan pinjaman bagi UMKM wanita.
        - **Bangladesh:** Program RAISE membantu 137.000 pemuda (termasuk migran yang kembali) mendapatkan pekerjaan.
        """)

st.divider()

# -----------------------------------------------------------------------------
# Bagian 5: Reformasi & Masa Depan
# -----------------------------------------------------------------------------
st.markdown("""
<div style="background-color:#e3f2fd;padding:20px;border-radius:10px;">
    <h3 style="text-align:center;color:#0071bc;">Membangun "Better Bank"</h3>
    <p style="text-align:center;">
        WBG telah memotong waktu persetujuan proyek dari <b>19 bulan menjadi 13 bulan</b>. 
        Meluncurkan <b>World Bank Group Guarantee Platform</b> yang terpadu, 
        serta inisiatif <b>Global Collaborative Co-Financing Platform</b> untuk merampingkan operasi dengan bank pembangunan multilateral lainnya.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Dashboard dibuat dengan Streamlit berdasarkan data dari World Bank Group Annual Report 2025 (Juli 2024 - Juni 2025).")