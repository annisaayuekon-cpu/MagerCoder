





# app.py
import streamlit as st

# Optional: konfigurasi awal tampilan app (title & icon global)
st.set_page_config(page_title="Dashboard Ekonomi Dunia - Kelompok", page_icon="🌍", layout="wide")

# -----------------------------
# Daftar halaman (home + 1-10)
# -----------------------------
pages = [
    # Home (harus ada file pages/home.py)
    st.Page(page="pages/home.py", title="Dashboard Ekonomi", icon="🌍"),

    # Page 1 - 10 (pastikan file pages/page1.py ... pages/page10.py ada)
    st.Page(page="pages/page1.py",  title="Pertumbuhan Ekonomi & GDP",         icon="📈"),
    st.Page(page="pages/page2.py",  title="Tenaga Kerja & Pengangguran",        icon="👷"),
    st.Page(page="pages/page3.py",  title="Inflasi & Harga Konsumen",           icon="🔥"),
    st.Page(page="pages/page4.py",  title="Perdagangan Internasional",          icon="🌐"),
    st.Page(page="pages/page5.py",  title="Investasi (FDI & Kapital)",          icon="💼"),
    st.Page(page="pages/page6.py",  title="Kemiskinan & Ketimpangan (GINI)",    icon="📉"),
    st.Page(page="pages/page7.py",  title="Populasi & Demografi",               icon="👥"),
    st.Page(page="pages/page8.py",  title="Pendidikan",                         icon="🎓"),
    st.Page(page="pages/page9.py",  title="Kesehatan",                          icon="🏥"),
    st.Page(page="pages/page10.py", title="Energi & Lingkungan",                icon="🌱"),
    st.Page(page="pages/page11.py", title="Analisis World Bank 2025",           icon="📘"),
]

# -----------------------------
# Buat navigasi di sidebar
# -----------------------------
pg = st.navigation(
    pages,
    position="sidebar",
    expanded=True
)


# Jalankan navigation (men-load halaman yg dipilih)
pg.run()




