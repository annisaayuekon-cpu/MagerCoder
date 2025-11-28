






# app.py
import streamlit as st

# ========== DEFINISI HALAMAN ==========
pages = [
    st.Page(
        page="pages/1_PertumbuhanEkonomi.py",
        title="Pertumbuhan Ekonomi & GDP",
        icon="📈"   # ikon pertumbuhan ekonomi
    ),
    st.Page(
        page="pages/2_PDBPerKapita.py",
        title="GDP Per Kapita & Struktur Ekonomi",
        icon="💰"   # ikon PDB per kapita
    ),
    st.Page(
        page="pages/3_Inflasi.py",
        title="Inflasi & Harga Konsumen",
        icon="🔥"   # ikon inflasi
    ),
    st.Page(
        page="pages/4_Pengangguran.py",
        title="Pengangguran",
        icon="👷"   # ikon tenaga kerja
    ),
    st.Page(
        page="pages/5_Perdagangan.py",
        title="Perdagangan Internasional",
        icon="🌐"   # ikon perdagangan
    ),
    st.Page(
        page="pages/6_Investasi.py",
        title="Investasi (FDI & Kapital)",
        icon="💼"   # ikon investasi
    ),
    st.Page(
        page="pages/7_KemiskinanGINI.py",
        title="Kemiskinan & GINI",
        icon="📉"   # ikon kemiskinan
    ),
    st.Page(
        page="pages/8_Populasi.py",
        title="Populasi & Demografi",
        icon="👥"   # ikon populasi
    ),
    st.Page(
        page="pages/9_KesehatanPendidikan.py",
        title="Kesehatan & Pendidikan",
        icon="🏥"   # ikon kesehatan
    ),
    st.Page(
        page="pages/10_EnergiLingkungan.py",
        title="Energi & Lingkungan",
        icon="🌱"   # ikon energi
    )
]

# ========== NAVIGASI (SIDEBAR) ==========
pg = st.navigation(
    pages,
    position="sidebar",
    expanded=True
)

# ========== JALANKAN HALAMAN ==========
pg.run()
