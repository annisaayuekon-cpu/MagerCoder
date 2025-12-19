import os
import streamlit as st

st.set_page_config(page_title="Dashboard Ekonomi Dunia - Kelompok", page_icon="🌍", layout="wide")

def safe_page(path, title, icon):
    return st.Page(page=path, title=title, icon=icon) if os.path.exists(path) else None

pages = [
    safe_page("pages/home.py", "Dashboard Ekonomi", "🌍"),
    safe_page("pages/page1.py", "Pertumbuhan Ekonomi & GDP", "📈"),
    safe_page("pages/page2.py", "Tenaga Kerja & Pengangguran", "👷"),
    safe_page("pages/page3.py", "Inflasi & Harga Konsumen", "🔥"),
    safe_page("pages/page4.py", "Perdagangan Internasional", "🌐"),
    safe_page("pages/page5.py", "Investasi (FDI & Kapital)", "💼"),
    safe_page("pages/page6.py", "Kemiskinan & Ketimpangan (GINI)", "📉"),
    safe_page("pages/page7.py", "Populasi & Demografi", "👥"),
    safe_page("pages/page8.py", "Pendidikan", "🎓"),
    safe_page("pages/page9.py", "Kesehatan", "🏥"),
    safe_page("pages/page10.py", "Energi & Lingkungan", "🌱"),
    safe_page("pages/page11.py", "World Bank 2024", "📘"),
    safe_page("pages/outlooks.py", "Indonesia Accession to the OECD", "🏛️"),
]
pages = [p for p in pages if p is not None]

pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()
